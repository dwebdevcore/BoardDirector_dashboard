from datetime import date, timedelta
from logging import getLogger

from dateutil.relativedelta import relativedelta
from django.db.transaction import atomic
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.mixins import GetMembershipWithURLFallbackMixin, RecentActivityMixin, AccountSerializerContextMixin, PerActionSerializerModelViewSetMixin
from common.models import TemplateModel
from common.views import do_add_event_to_calendar
from dashboard.models import RecentActivity
from meetings.models import MeetingManager, Meeting, MeetingAttendance, MeetingRepetition
from meetings.serializers import MeetingDetailsSerializer, MeetingRepetitionSerializer, MeetingAttendanceSerializer, \
    CalendarMeetingSerializer, AddToCalendarSerializer, MeetingListSerializer, MeetingSerializer
from meetings.views import MeetingsFilteredQuerysetMixin, MeetingDetailView
from permissions.mixins import RestPermissionByMethodMixin, RestPermissionMixin
from permissions.rest_permissions import RequireObjectEdit, CheckAccountUrl, IsAccountAdmin
from rsvp.serializers import RsvpResponseSerializer

logger = getLogger(__name__)


class MeetingViewSet(RestPermissionMixin, RestPermissionByMethodMixin, MeetingsFilteredQuerysetMixin, GetMembershipWithURLFallbackMixin,
                     RecentActivityMixin, AccountSerializerContextMixin, PerActionSerializerModelViewSetMixin, viewsets.ModelViewSet):
    """
    Meeting views:

    * `?past=1` to get past meetings
    * `?event=1` to get events (by default meetings are returned)
    * `?committee=id` to filter by committee (use `?committee=__full__` to get only full board meetings)
    * `?order_by=asc|desc` to sort by date (`asc` is default)
    * `GET /calendar_data[?month=YYYY-MM][&from=YYYY-MM-DD][&to=YYYY-MM-DD]` is used to get meetings data to build calendar:
        it is subset of data, with meetings repeated for each repetition
        (3 months back in time + all future meetings, currently).
        Optional `month` param can be specified to limit results to one month only.
        If `month` isn't set, optional `from` and `to` serve similar purpose.
    * `POST /{pk}/publish` is used to publish Meeting. There is no other way for API to create publish meeting then to create it and then publish.
    * `POST /{pk}/reminder` sends reminder to all meeting members except current user.
    * `POST /{pk}/rsvp` to set rsvp for current user (check via viewer to get fields via OPTIONS request).
    * `POST /{pk}/attendance` to set attendance information after meeting started (is_admin only), check via viewer to get fields via OPTIONS request.
    * `POST /{pk}/add_to_online_calendar` body: `{ 'connect_type' : 'office|google' }` to set attendance information after meeting started (is_admin only).

    Meeting details (`/{pk}/`):

    * `?date=YYYY-MM-DD` to view RSVP information for specific date, for recurring meetings
    * `details` object in result is pretty much the same date used to render meeting details page, it has several fields, most notably:
        * `next`/`previous` - is next/previous meeting id for navigation
        * `rsvp_responses` - for responses from different members
        * `agenda`/`minutes`/`board_book`/`other_docs` - documents information (NOTE: currently download/view links require SESSION auth)
        * `future_repetitions` - this field contains next 10 dates for recurring meetings + RSVP information for *current* user
        * `is_*_connected` - calendar connection information
    """
    serializer_class = MeetingDetailsSerializer
    permission_model = Meeting
    permission_classes = [CheckAccountUrl]
    page_size = 100

    def is_event(self):
        return self.request.query_params.get('event', '0') == '1'

    @atomic
    def perform_create(self, serializer):
        meeting = serializer.save(account=self.get_current_account())

        self.save_recent_activity(action_flag=RecentActivity.ADDITION, obj=meeting)

    @atomic
    def perform_update(self, serializer):
        meeting = serializer.save(account=self.get_current_account())

        self.save_recent_activity(action_flag=RecentActivity.CHANGE, obj=meeting)

    def retrieve(self, request, *args, **kwargs):
        meeting = self.get_object()
        serializer = self.get_serializer(meeting)
        details = MeetingDetailView.get_meeting_details(meeting, self.get_queryset(),
                                                        self.request.user, self.get_current_account(),
                                                        self.request.query_params.get('date'))
        result = dict(serializer.data)
        result['details'] = details
        details['current_repetition'] = MeetingRepetitionSerializer(details['current_repetition']).data
        details['future_repetitions'] = None if not details['future_repetitions'] else \
            [MeetingRepetitionSerializer(r).data for r in details['future_repetitions']]

        details['next'] = None if not details['next'] else details['next'].id
        details['previous'] = None if not details['previous'] else details['previous'].id

        return Response(result)

    @detail_route(methods=['POST'], permission_classes=[CheckAccountUrl, RequireObjectEdit])
    def publish(self, request, url, pk):
        meeting = self.get_object()
        meeting.publish()
        meeting.send_details_email()
        return Response({'result': 'ok'})

    @detail_route(methods=['POST'], permission_classes=[CheckAccountUrl, RequireObjectEdit])
    def reminder(self, request, url, pk):
        meeting = self.get_object()
        if not meeting.is_published:
            return Response({'result': 'error', 'message': _("Can't send reminder for not published meeting")}, status=403)

        meeting.send_details_email(template_name=TemplateModel.MEETING_REMINDER, exclude_user=request.user)
        return Response({'result': 'ok'})

    @detail_route(methods=['POST'], permission_classes=[CheckAccountUrl, IsAuthenticated], serializer_class=RsvpResponseSerializer)
    def rsvp(self, request, url, pk):
        meeting = self.get_object()
        if not meeting.check_user_is_member(request.user):
            raise PermissionDenied(_("You can't RSVP for this meeting as you're not a member of it"))

        serializer = RsvpResponseSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save(meeting=meeting, user=request.user)

        return Response({'result': 'ok'}, status=status.HTTP_201_CREATED)

    @detail_route(methods=['POST'], permission_classes=[CheckAccountUrl, IsAccountAdmin], serializer_class=MeetingAttendanceSerializer)
    def attendance(self, request, url, pk):
        meeting = self.get_object()

        if meeting.start > timezone.now():
            raise PermissionDenied(_("Can't set attendance results for meeting that hasn't yet started"))

        serializer = MeetingAttendanceSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)

        if not meeting.check_user_is_member(serializer.validated_data['user']):
            raise PermissionDenied(_("Can't set attendance for not member"))

        MeetingAttendance.objects.update_or_create(meeting=meeting, user=request.user,
                                                   defaults={'present': serializer.validated_data['present']})

        return Response({'result': 'ok'}, status=status.HTTP_201_CREATED)

    def list(self, request, url):

        queryset = MeetingRepetition.objects\
            .for_membership(self.get_current_membership(), only_own_meetings=True)\
            .select_related('meeting', 'meeting__account')
        queryset = queryset.filter(meeting__status=Meeting.STATUSES.published)

        today = timezone.localdate(timezone.now())
        past = 'past' in request.query_params
        if past:
            queryset = queryset.filter(date__lt=today)
        else:
            queryset = queryset.filter(date__gte=today)

        is_event = 'event' in request.query_params
        queryset = queryset.filter(meeting__is_event=is_event)

        order_by = request.query_params.get('order_by', 'asc')
        if order_by == 'desc' or (order_by == 'near' and past):
            queryset = queryset.order_by('-date', '-meeting__start')

        elif order_by == 'asc'or (order_by == 'near' and not past):
            queryset = queryset.order_by('date', 'meeting__start')

        else:
            queryset = queryset.order_by('date')

        committee = request.query_params.get('committee', None)
        if committee == '__full__':
            queryset = queryset.filter(meeting__committee=None)
        elif committee and committee != '__all__' and committee.isdigit():
            queryset = queryset.filter(meeting__committee__id=int(committee))

        page = request.query_params.get('page', None)
        if not page or not page.isdigit():
            page = 0
        else:
            page = int(page)

        # get all dates
        meeting_dates_count = queryset.count()
        meeting_dates = queryset[self.page_size * page:self.page_size * (page + 1)]

        # get all meetings (some meetings are reccurrent, so may appear more than one)
        meetings = [r.to_meeting_with_repetition_date() for r in meeting_dates]
        serializer = MeetingSerializer(meetings, many=True, context=self.get_serializer_context())

        base_link = self.request.build_absolute_uri()
        if page > 0:
            previous_link = replace_query_param(base_link, 'page', page - 1)
        else:
            previous_link = None

        if meeting_dates_count > self.page_size * (page + 1):
            next_link = replace_query_param(base_link, 'page', page + 1)
        else:
            next_link = None

        # return Response(serializer.data)
        return Response({
            'next': next_link,
            'previous': previous_link,
            'count': meeting_dates_count,
            'results': serializer.data
        })

    @list_route(methods=['GET'], permission_classes=[CheckAccountUrl])
    def calendar_data(self, request, url):
        queryset = MeetingRepetition.objects\
            .for_membership(self.get_current_membership(), only_own_meetings=True)\
            .select_related('meeting', 'meeting__account')
        queryset = queryset.filter(meeting__status=Meeting.STATUSES.published)
        month = request.query_params.get('month')
        if month is None:
            try:
                queryset = queryset.filter(date__gte=self._str_to_date(request.query_params['from']))
            except (KeyError, ValueError):
                queryset = queryset.filter(date__gte=date.today() - timedelta(days=100))

            try:
                queryset = queryset.filter(date__lte=self._str_to_date(request.query_params['to']))
            except (KeyError, ValueError):
                pass
        else:
            year, month = [int(x) for x in month.split('-')]
            queryset = queryset.filter(date__gte=date(year, month, 1), date__lt=date(year, month, 1) + relativedelta(months=1))

        queryset = queryset.order_by('date')
        repetitions = queryset.distinct()
        meetings = [r.to_meeting_with_repetition_date() for r in repetitions]
        serializer = CalendarMeetingSerializer(meetings, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @staticmethod
    def _str_to_date(date_str):
        year, month, day = [int(x) for x in date_str.split('-')]
        return date(year, month, day)

    @detail_route(methods=['POST'], permission_classes=[CheckAccountUrl], serializer_class=AddToCalendarSerializer)
    def add_to_online_calendar(self, request, url, pk):
        serializer = AddToCalendarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        connect_type = serializer.validated_data['connect_type']

        meeting = self.get_object()
        if not meeting.check_user_is_member(request.user):
            raise PermissionDenied(_("Current user must be member of meeting to add it to calendar."))

        try:
            result = do_add_event_to_calendar(cur_account=self.get_current_account(),
                                              meeting=meeting,
                                              connect_type=connect_type,
                                              google_redirect_uri=request.build_absolute_uri(reverse('google_token')),
                                              office_redirect_uri=request.build_absolute_uri(reverse('office_token')))
        except Exception as e:
            logger.error(e)
            return Response({'result': 'error',
                             'msg': _('Failed to add event to calendar: %s' % e)})

        if result.get('result') == 'fail':
            return Response(result)
        elif 'error' in result:
            return Response({'result': 'error',
                             'msg': "Failed add to {0} calendar: {1}!".format(connect_type, result['error'])})
        else:
            return Response({'result': 'success',
                             'msg': "This meeting has been added successfully to {0} calendar !".format(connect_type)})
