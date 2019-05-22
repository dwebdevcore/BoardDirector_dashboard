from django.db.transaction import atomic
from django.utils import timezone
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from common.mixins import FilterSerializerByAccountMixin
from documents.models import Document, Folder
from meetings.models import Meeting, MeetingRepetition, MeetingAttendance, MeetingNextRepetition
from profiles.models import Membership
from committees.models import Committee
from committees.serializers import CommitteeSerializer
from profiles.serializers import MembershipShortSerializer
from accounts.serializers import AccountSerializer


class MeetingSerializer(FilterSerializerByAccountMixin, serializers.ModelSerializer):

    extra_members = PrimaryKeyRelatedField(many=True, queryset=Membership.objects.all(), required=False)
    documents = PrimaryKeyRelatedField(many=True, queryset=Document.objects.all(), required=False, write_only=True)
    creator = MembershipShortSerializer(many=False)
    committee_name = serializers.SerializerMethodField()
    date_formatted = serializers.SerializerMethodField()
    time_formatted = serializers.SerializerMethodField()

    def get_committee_name(self, obj):
        return obj.committee.name if obj.committee else None

    def get_time_formatted(self, obj):
        a = timezone.datetime.strftime(timezone.localtime(obj.start), '%I:%M %p')
        b = timezone.datetime.strftime(timezone.localtime(obj.end), '%I:%M %p')
        t = timezone.datetime.strftime(timezone.localtime(obj.start), '%Z')
        return "%s &ndash; %s %s" % (a, b, t)

    def get_date_formatted(self, obj):
        # return timezone.datetime.strftime(timezone.localtime(obj.start), '%l, %B %d %Y')
        month = timezone.datetime.strftime(timezone.localtime(obj.start), '%b')
        strf1 = timezone.datetime.strftime(timezone.localtime(obj.start), '%A, %B')
        strf2 = '%i, %i' % (obj.start.day, obj.start.year)  # avoid zero-padding for date 8/
        return ["%s %s" % (strf1, strf2), obj.start.day, month, obj.start.year]

    def __init__(self, instance=None, **kwargs):
        super(MeetingSerializer, self).__init__(instance, **kwargs)
        self.filter_account('committee')
        self.filter_account_in_many('extra_members')
        self.filter_account_in_many('documents')

    @atomic
    def create(self, validated_data):
        documents = validated_data.pop('documents', [])
        meeting = super(MeetingSerializer, self).create(validated_data)
        self.bind_documents(documents, meeting)
        return meeting

    def update(self, instance, validated_data):
        documents = validated_data.pop('documents', [])
        meeting = super(MeetingSerializer, self).update(instance, validated_data)
        self.bind_documents(documents, meeting)
        return meeting

    def bind_documents(self, documents, meeting):
        if documents:
            Folder.objects.update_or_create_meeting_folder(meeting)
        for document in documents:
            document.folder = meeting.folder
            document.save()

    class Meta:
        model = Meeting
        exclude = []
        read_only_fields = ['account', 'status']


class MeetingListSerializer(MeetingSerializer):
    next_repetition_date = serializers.SerializerMethodField()

    def get_next_repetition_date(self, meeting):

        # simple -- meeting is not recurring, use start date
        if meeting.repeat_type == Meeting.REPEAT_TYPES.once:
            return meeting.start

        # check future dates
        today = timezone.localdate(timezone.now())
        next_time = MeetingRepetition.objects.filter(meeting=meeting,
                                                     date__gte=today,
                                                     meeting__status=Meeting.STATUSES.published)
        next_time = next_time.values('date').order_by('date').first()

        if next_time:
            return next_time['date']

        # no meetings in the future -- check last one in the past
        last_time = MeetingRepetition.objects.filter(meeting=meeting,
                                                     meeting__status=Meeting.STATUSES.published)
        last_time = last_time.values('date').order_by('date').first()

        if last_time:
            return next_time['date']

        return None


def doc_to_dict(doc):
    return {
        'id': doc.id,
        'name': doc.name,
        'download_url': doc.get_api_download_url(),
        'preview_url': doc.get_api_preview_url(),
        'content_type': doc.file_type(),
        'view_url': doc.get_viewer_url()
    }


def make_doc_field(name, many=False):
    def getter(self, meeting):
        doc = getattr(meeting, 'get_' + name)()
        if not doc:
            return None
        elif not many:
            return doc_to_dict(doc)
        else:
            return [doc_to_dict(d) for d in doc]

    return serializers.SerializerMethodField(), getter


class MeetingDetailsSerializer(MeetingSerializer):
    agenda, get_agenda = make_doc_field('agenda')
    minutes, get_minutes = make_doc_field('minutes')
    board_book, get_board_book = make_doc_field('board_book')
    other_docs, get_other_docs = make_doc_field('other_docs', many=True)

    class Meta(MeetingSerializer.Meta):
        pass


class OptionalField(serializers.Field):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(OptionalField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        return getattr(value, self.name, None)


class MeetingRepetitionSerializer(serializers.ModelSerializer):
    rsvp_response = serializers.SerializerMethodField()
    rsvp_accept_type = OptionalField('rsvp_accept_type')
    rsvp_note = OptionalField('rsvp_note')

    def get_rsvp_response(self, meeting_repetition):
        return getattr(meeting_repetition, 'rsvp_response_num', None)  # this attr is dynamic so it can be or can absent

    class Meta:
        model = MeetingRepetition
        fields = ['id', 'date', 'rsvp_response', 'rsvp_accept_type', 'rsvp_note']


class DashboardMeetingSerializer(MeetingSerializer):
    current_repetition = MeetingRepetitionSerializer()


class CalendarMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = ['id', 'name', 'description', 'location', 'start', 'end', 'is_event', 'committee']


class MeetingAttendanceSerializer(FilterSerializerByAccountMixin, ModelSerializer):
    class Meta:
        model = MeetingAttendance
        fields = ['user', 'present']

    def __init__(self, instance=None, **kwargs):
        super(MeetingAttendanceSerializer, self).__init__(instance, **kwargs)
        self.filter_account('user', account_field='membership__account')


class AddToCalendarSerializer(serializers.Serializer):
    connect_type = serializers.RegexField("office|google")
