from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.db.transaction import atomic
from django.http.response import Http404
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.mixins import GetMembershipWithURLFallbackMixin, AccountSerializerContextMixin, \
    RecentActivityMixin, PerActionSerializerModelViewSetMixin
from dashboard.models import RecentActivity
from documents.models import Document, Folder, AuditTrail, Annotation
from documents.serializers import DocumentCreateSerializer, FolderSerializer, DocumentUpdateSerializer, \
    FolderShareSerializer, FolderDetailSerializer, \
    DocumentDeleteSerializer, AnnotationSerializer, AnnotationUpdateSerializer
from documents.views import PermissionAddView
from documents.views.document import DocumentCreateMixin, DocumentDownloadView, \
    DocumentAjaxDeleteView, DocumentRevisionDownloadView, DocumentPdfPreviewView
from documents.views.folder_lookup import FolderLookupMixin
from permissions import PERMISSIONS
from permissions.mixins import RestPermissionByMethodMixin, RestPermissionMixin
from permissions.rest_permissions import CheckAccountUrl
from permissions.shortcuts import get_object_permissions, filter_by_permission, has_object_permission


# noinspection PyUnresolvedReferences
class FolderPropertyMixin(object):
    @cached_property
    def folder(self):
        if 'folder' not in self.request.query_params:
            return Folder.objects.get_account_root(self.get_current_account())
        else:
            return get_object_or_404(Folder, pk=self.request.query_params['folder'], account=self.get_current_account())

    def require_folder_permission(self, permission, folder=None):
        if permission not in get_object_permissions(self.get_current_membership(), folder or self.folder):
            raise PermissionDenied("You don't have %s permission for this folder" % (permission,))


class DocumentViewset(RestPermissionMixin, RestPermissionByMethodMixin, GetMembershipWithURLFallbackMixin,
                      AccountSerializerContextMixin, DocumentCreateMixin, RecentActivityMixin, FolderPropertyMixin,
                      PerActionSerializerModelViewSetMixin,
                      viewsets.ModelViewSet):
    """
    Operations on document:

    * `?folder=id` to list contents of desired folder, root folder is used by default
    * `POST` to create new document, body is base64 encoded, practical limit is 50Mb files
        * Note: document is created inside folder, given in POSTed `folder` field, querystring folder is ignored
    * `GET /{pk}/` - get document details
    * `GET /{pk}/download/` - download document contents
    * `GET /{pk}/download-preview/` - download document PDF preview
    * `GET /{pk}/download-revision/{revision-num}/` - download document revision (note: new id is used).

    Working with document revisions:

    1. `POST` to create new document, providing `old_doc`: id of old document
    2. `DELETE` old document providing body `{"change_type": 0}` to indicate update.
    3. use `revisions` on new document
    """
    serializer_class = DocumentCreateSerializer
    serializer_class_update = DocumentUpdateSerializer
    serializer_class_destroy = DocumentDeleteSerializer
    permission_model = Document
    permission_classes = [IsAuthenticated, CheckAccountUrl]

    def get_queryset(self):
        return Document.objects.filter(account=self.get_current_account()).order_by('name')

    def list(self, request, *args, **kwargs):
        self.require_folder_permission('view')

        queryset = self.get_queryset().filter(folder=self.folder)
        documents = filter_by_permission(queryset, self.get_current_membership(), PERMISSIONS.view)
        Document.prefetch_revisions(documents)

        serializer = self.get_serializer(documents, many=True)

        return Response(serializer.data)

    @atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        folder = serializer.validated_data['folder']
        if folder:
            # In some use-cases folder can be omitted: creating documents later bound to meeting/committee
            self.require_folder_permission('add', folder=folder)
            if not folder.can_add_files:
                raise PermissionDenied(_("parent folder '%s' doesn't allow to add files") % (folder.name,))

        self.object = document = serializer.save()

        check = self._check_and_update_storage(self.get_current_account(), len(document.file))
        if check is not True:
            transaction.set_rollback(True)
            return Response(check, status=status.HTTP_400_BAD_REQUEST)

        self.post_save_actions(document,
                               old_doc=serializer.validated_data.get('old_doc'),
                               meeting=serializer.validated_data.get('meeting'))

        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @atomic
    def perform_update(self, serializer):
        folder = serializer.validated_data['folder']
        self.require_folder_permission('edit', folder=folder)

        if folder != self.get_object().folder and not folder.can_add_files:
            raise PermissionDenied(_("parent folder '%s' doesn't allow to add files") % (folder.name,))

        serializer.save()

        self.save_recent_activity(RecentActivity.CHANGE, self.get_object())

    @atomic
    def perform_destroy(self, document):
        try:
            serializer = DocumentDeleteSerializer(data=self.request.data)
            serializer.is_valid(raise_exception=True)
            change_type = serializer.validated_data['change_type']
        except ParseError:
            change_type = AuditTrail.DELETED
        DocumentAjaxDeleteView.process_delete(change_type, document, self.request.user.id)

    @detail_route(methods=['GET'])
    def download(self, request, url, pk):
        document = self._find_document_and_check_can_view(pk)

        return DocumentDownloadView.do_download(document)

    @detail_route(methods=['GET'], url_path=r'download-revision/(?P<revision>\d+)/', url_name='download-revision')
    def download_revision(self, request, url, pk, revision):
        # Validate access
        self._find_document_and_check_can_view(pk)

        return DocumentRevisionDownloadView.get(request, pk, revision)

    @detail_route(methods=['GET'], url_path=r'download-preview/?', url_name='download-preview')
    def download_preview(self, request, url, pk):
        document = self._find_document_and_check_can_view(pk)
        preview = document.generate_preview()
        if document.pdf_preview:
            return DocumentDownloadView.do_download_file(document.pdf_preview, document.name + '.pdf')
        elif preview:
            return DocumentDownloadView.do_download_file(preview, document.name)
        else:
            raise Http404

    def _find_document_and_check_can_view(self, pk):
        # No filtering by folder here as any document id, for current account is alright
        document = self.get_queryset().get(pk=int(pk))
        if not has_object_permission(self.get_current_membership(), document, PERMISSIONS.view):
            raise PermissionDenied()
        return document


class FolderViewset(RestPermissionMixin, RestPermissionByMethodMixin, FolderLookupMixin, GetMembershipWithURLFallbackMixin,
                    AccountSerializerContextMixin, DocumentCreateMixin, RecentActivityMixin, FolderPropertyMixin,
                    viewsets.ModelViewSet):
    """
    Operations on folders:

    * `?folder=id` to list contents of desired folder, root folder is used by default
    * `POST` to create new folder
        * Note: folder is created based on `parent` field, and doesn't honor `?folder=id` query param.
    * `/lookup` special route, which exposes data, required to move folders/documents:
        * `?init_for_document_id=document.id` - will return folder structure for target document, i.e. it's parents
        * `?init_for_folder_id=folder.id` - same for folder
        * `?folder_id=folder.id` - will return data for specific folder (i.e. user clicks to expand it)
    * `POST /{pk}/share` to share folder (check options for it)
    * `DELETE/{pk}/share` to remove shared permission:
        * use `GET /{pk}` to get details and ['permissions'][i]['id'] to get permission id.
        * Pass `{ permission_id: id }` as body to `DELETE/{pk}/share` (this way mimics the way Web UI works).
        * Note: edit will give several permissions, you can pass only one, it'll delete all others as well
    """
    serializer_class = FolderDetailSerializer
    serializer_class_list = FolderSerializer
    permission_model = Folder
    permission_classes = [IsAuthenticated, CheckAccountUrl]

    def get_queryset(self):
        return Folder.objects.filter(account=self.get_current_account()).order_by('name')

    def or_permission(self, account, membership):
        return self.action == 'create'  # Manual checks in this case

    def and_permission(self, account, membership):
        # View only explicitly allowed folders (usually RolePermission view means can view all)
        try:
            return self.action in ['list', 'create', 'lookup'] or has_object_permission(membership, self.get_object(), PERMISSIONS.view)
        except Http404:
            return True  # Ok.. you've got access to nothing.
        except:
            return False

    def list(self, request, *args, **kwargs):
        # Parent filtering is only done for list, so that updates/delete can use just id.
        queryset = self.get_queryset().filter(parent=self.folder)

        folders = filter_by_permission(queryset, self.get_current_membership(), 'view')
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        parent = serializer.validated_data['parent']
        self.require_folder_permission('add', folder=parent)
        if not parent.can_add_folders:
            raise PermissionDenied(_("parent folder '%s' doesn't allow to add folders") % (parent.name,))
        serializer.save(account=self.get_current_account(), user=self.request.user)

    def perform_update(self, serializer):
        parent = serializer.validated_data['parent']

        # Detect malicious move:
        if parent != self.get_object().parent:
            self.require_folder_permission('add', folder=parent)

            if not parent.can_add_folders:
                raise PermissionDenied(_("parent folder '%s' doesn't allow to add folders") % (parent.name,))

        super(FolderViewset, self).perform_update(serializer)

    @list_route(methods=['GET'])
    def lookup(self, request, url):
        data = self.collect_data(self.request)
        return Response(data, status=400 if 'error' in data else 200)

    @detail_route(methods=['POST', 'DELETE'], serializer_class=FolderShareSerializer)
    def share(self, request, url, pk):
        folder = self.get_object()
        self.require_folder_permission('share', folder=folder)

        if request.method == 'DELETE':
            permission_id = int(request.data['permission_id'])
            permission = get_object_or_404(folder.permissions.all(), pk=permission_id)
            folder.permissions.filter(
                role=permission.role,
                membership=permission.membership
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            serializer = FolderShareSerializer(data=request.data, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            PermissionAddView.do_add_permissions(memberships=data.get('memberships', []),
                                                 permission=data['permission'],
                                                 role=data.get('role'),
                                                 perm_obj=folder)

            return Response({'result': 'ok'}, status=status.HTTP_201_CREATED)


class AnnotationsViewSet(RestPermissionMixin, RestPermissionByMethodMixin, PerActionSerializerModelViewSetMixin,
                         GetMembershipWithURLFallbackMixin, AccountSerializerContextMixin, viewsets.ModelViewSet):
    """
    Annotations API which mostly resembles [Annotation API Document](https://docs.google.com/document/d/1olOH9_XLpCZeDSvZMSFDVcIGFVg4M2Mp889vl8Rgew0/edit#).

    `id`s for annotations and comments are currently generated server-side. If some `id` is provided for entity it's considered as an update of related entity.

    Partial updates are fine: i.e. post only new/changed annotation and don't touch others. Same for comments.
    """
    serializer_class = AnnotationUpdateSerializer
    permission_classes = [IsAuthenticated, CheckAccountUrl]

    def get_queryset(self):
        return Annotation.objects.none()

    def list(self, request, *args, **kwargs):
        query = request.query_params
        if 'document_id' not in query:
            return Response({'detail': 'document_id is required'}, status=400)

        document_id = int(query['document_id'])
        document = get_object_or_404(Document, account=self.get_current_account(), pk=document_id)
        if PERMISSIONS.view not in get_object_permissions(self.get_current_membership(), document):
            raise PermissionDenied("No view permission for document %d" % document_id)

        queryset = Annotation.objects.filter(document_id=document_id)\
            .filter(Q(author_user=request.user) | Q(shared=True))

        if 'from_page' in query:
            queryset = queryset.filter(document_page__gte=query['from_page'])
        if 'to_page' in query:
            queryset = queryset.filter(document_page__lte=query['to_page'])

        annotations = list(queryset)

        serializer = AnnotationUpdateSerializer({
            'document_id': document_id,
            'annotations': annotations,
        }, context=self.get_serializer_context())

        return Response(serializer.data)

    @list_route(methods=['POST'])
    def drop_annotations(self, request, *args, **kwargs):
        if settings.DEBUG:
            return Response(Annotation.objects.all().delete())
        else:
            return Response({}, status=403)

    def update(self, request, *args, **kwargs):
        raise NotImplemented

    def destroy(self, request, *args, **kwargs):
        raise NotImplemented
