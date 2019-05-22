from encodings.base64_codec import base64_decode

from copy import copy
from django.core.files.base import ContentFile
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.fields import JSONField
from rest_framework.generics import get_object_or_404

from common.mixins import FilterSerializerByAccountMixin, ReBindListSerializer
from documents.models import Document, Folder, AuditTrail, AnnotationComment, Annotation
from documents.views.document import DocumentCreateMixin
from meetings.models import Meeting
from permissions import PERMISSIONS
from permissions.serializers import ObjectPermissionsBriefSerializer
from permissions.shortcuts import get_object_permissions
from profiles.models import Membership


class AuditTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditTrail
        fields = ['id', 'name', 'created_at', 'user', 'change_type', 'revision']


class DocumentSerializer(FilterSerializerByAccountMixin, serializers.ModelSerializer):
    revisions = AuditTrailSerializer(many=True, read_only=True)

    def __init__(self, instance=None, **kwargs):
        super(DocumentSerializer, self).__init__(instance, **kwargs)
        self.filter_account('folder')
        self.fields['folder'].required = True
        self.fields['name'].required = True

    class Meta:
        model = Document
        fields = ['id', 'name', 'type', 'created_at', 'folder', 'revisions']
        read_only_fields = ['created_at']


class DocumentCreateSerializer(DocumentCreateMixin, DocumentSerializer):
    meeting = serializers.PrimaryKeyRelatedField(queryset=Meeting.objects.all(), required=False, allow_null=True, write_only=True)
    old_doc = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all(), required=False, allow_null=True, write_only=True)
    body = serializers.CharField(write_only=True)

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ['body', 'old_doc', 'meeting']

    def __init__(self, instance=None, **kwargs):
        super(DocumentCreateSerializer, self).__init__(instance, **kwargs)
        self.filter_account('meeting')
        self.filter_account('old_doc')

    def create(self, validated_data):
        body = validated_data.get('body')
        body = base64_decode(body)[0]

        document = Document()
        document.account = self.context['account']
        document.folder = validated_data.get('folder')
        document.type = validated_data.get('type') or Document.OTHER
        document.file = ContentFile(body, validated_data.get('name'))
        document.user = self.context['user']

        old_doc = validated_data.get('old_doc')
        if old_doc:
            document.previous_version = old_doc.id

        document.save()

        return document

    def update(self, instance, validated_data):
        instance.name = validated_data['name']
        instance.folder = validated_data['folder']
        instance.save()
        return instance


class DocumentUpdateSerializer(DocumentCreateSerializer):
    def __init__(self, instance=None, **kwargs):
        super(DocumentUpdateSerializer, self).__init__(instance, **kwargs)
        del self.fields['body']


class DocumentDeleteSerializer(serializers.Serializer):
    change_type = serializers.ChoiceField(choices=AuditTrail.CHANGES_TYPES, required=False, default=AuditTrail.DELETED)


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent', 'user', 'slug', 'created', 'modified', 'protected', 'meeting', 'committee', 'membership']
        read_only_fields = ['slug', 'meeting', 'committee', 'membership', 'protected', 'user']

    def __init__(self, instance=None, **kwargs):
        super(FolderSerializer, self).__init__(instance, **kwargs)

        self.fields['slug'].required = False


class FolderDetailSerializer(FolderSerializer):
    permissions = ObjectPermissionsBriefSerializer(many=True, read_only=True)

    class Meta(FolderSerializer.Meta):
        fields = FolderSerializer.Meta.fields + ['permissions']


class FolderShareSerializer(FilterSerializerByAccountMixin, serializers.Serializer):
    memberships = serializers.PrimaryKeyRelatedField(queryset=Membership.objects.all(), many=True, required=False)
    role = serializers.ChoiceField(required=False, choices=[
        (Membership.ROLES.member, _('All Board Members')),
        (Membership.ROLES.guest, _('All Board Guests'))])
    permission = serializers.ChoiceField(choices=[('view', _('View')), ('edit', _('Edit'))])

    def __init__(self, instance=None, **kwargs):
        super(FolderShareSerializer, self).__init__(instance, **kwargs)
        self.filter_account_in_many('memberships')

    def validate(self, attrs):
        attrs = super(FolderShareSerializer, self).validate(attrs)

        if not attrs.get('memberships') and not attrs.get('role'):
            raise ValidationError('Either membreships or role must be set')

        return attrs


def filter_users(qs, account):
    return qs.filter(id__in=Membership.objects.filter(account=account, is_active=True).values_list('user_id'))


class AnnotationCommentSerializer(FilterSerializerByAccountMixin, serializers.ModelSerializer):
    class Meta:
        model = AnnotationComment
        fields = ['id', 'author_user_id', 'author_user_name', 'created', 'text']
        list_serializer_class = ReBindListSerializer

    id = serializers.IntegerField(required=False)
    author_user_name = serializers.SerializerMethodField()

    def get_author_user_name(self, annotation):
        return annotation.author_user.get_membership(self.context['account']).get_full_name()

    def __init__(self, instance=None, **kwargs):
        super(AnnotationCommentSerializer, self).__init__(instance, **kwargs)


class AnnotationSerializer(FilterSerializerByAccountMixin, serializers.ModelSerializer):
    cargo_json = JSONField()
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Annotation
        fields = ['id', 'author_user_id', 'document_id', 'audit_trail_id', 'document_page', 'type', 'created', 'geometry_tools_version', 'cargo_json',
                  'comments', 'local_id', 'shared']
        list_serializer_class = ReBindListSerializer

    comments = AnnotationCommentSerializer(many=True)

    def __init__(self, instance=None, **kwargs):
        super(AnnotationSerializer, self).__init__(instance, **kwargs)

    def create(self, validated_data):
        comments = validated_data.pop('comments', [])
        annotation = super(AnnotationSerializer, self).create(validated_data)
        self.sync_comments(annotation, comments)
        return annotation

    def update(self, instance, validated_data):
        comments = validated_data.pop('comments', [])
        if not self.context.get('readonly'):
            annotation = super(AnnotationSerializer, self).update(instance, validated_data)
        else:
            annotation = self.instance
        self.sync_comments(annotation, comments)
        return annotation

    def sync_comments(self, annotation, comments):
        existing_comments = {c.id: c for c in annotation.comments.filter(author_user=self.context['user'])}
        for comment in comments:
            if 'id' in comment:
                if comment['id'] in existing_comments:
                    s = AnnotationCommentSerializer(instance=existing_comments[comment['id']], data=comment, context=self.context)
                else:
                    raise ValidationError({'detail': "Can't update comment id=%d: it either not exists or belongs to other user" % comment['id']})
            else:
                s = AnnotationCommentSerializer(data=comment, context=self.context)

            s.is_valid(raise_exception=True)
            s.save(author_user=self.context['user'], annotation=annotation)


class AnnotationUpdateSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    annotations = AnnotationSerializer(many=True, required=False, default=[])
    annotation_id_to_delete = serializers.ListField(child=serializers.IntegerField(), required=False)
    notes = serializers.ListField(child=serializers.CharField(), read_only=True, required=False)

    @atomic
    def create(self, validated_data):
        context = self.context
        document = get_object_or_404(Document, account=context['account'], pk=validated_data['document_id'])
        permissions = get_object_permissions(context['membership'], document)
        if PERMISSIONS.view not in permissions:
            raise PermissionDenied("No view permission for document %d" % document.id)

        notes = []
        deleted_annotations = []
        annotations_query = document.annotations.prefetch_related('comments')
        user_annotations = {a.id: a for a in annotations_query.filter(author_user=context['user'])}
        shared_annotations = {a.id: a for a in annotations_query.filter(shared=True) if a.id not in user_annotations}
        if 'annotation_id_to_delete' in validated_data:
            for annotation_id in validated_data['annotation_id_to_delete']:
                if annotation_id not in user_annotations:
                    notes.append("Can't delete annotation with id=%d as it doesn't belong to current user or document" % annotation_id)
                else:
                    user_annotations[annotation_id].delete()
                    del user_annotations[annotation_id]
                    deleted_annotations.append(annotation_id)

        result_annotations = []
        for annotation in validated_data['annotations']:
            try:
                if 'id' in annotation:
                    if annotation['id'] in user_annotations:
                        s = AnnotationSerializer(user_annotations[annotation['id']], data=annotation, context=context)
                    elif annotation['id'] in shared_annotations:
                        # Only comments can be updated, so: get data as it is in DB + change comments
                        readonly_context = copy(context)
                        readonly_context['readonly'] = True
                        aa = AnnotationSerializer(shared_annotations[annotation['id']], context=readonly_context).data
                        aa['comments'] = annotation.get('comments', [])
                        s = AnnotationSerializer(shared_annotations[annotation['id']], data=aa, context=readonly_context)
                    else:
                        raise ValidationError({
                            'detail': "Can't update annotation with id=%d which doesn't belong to current user or document." % annotation['id']})
                else:
                    s = AnnotationSerializer(data=annotation, context=context)

                s.is_valid(raise_exception=True)
                s.save(author_user=context['user'], account=context['account'], document=document)
                result_annotations.append(s.instance)
            except ValidationError as e:
                notes.append(e.detail['detail'])

        return {
            'document_id': validated_data['document_id'],
            'annotations': result_annotations,
            'annotation_id_to_delete': deleted_annotations,
            'notes': notes,
        }
