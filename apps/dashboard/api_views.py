from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.mixins import AccountSerializerContextMixin, GetMembershipWithURLFallbackMixin
from dashboard.views import DashboardQuerysetMixin
from meetings.models import Meeting
from meetings.serializers import DashboardMeetingSerializer
from permissions.mixins import RestPermissionMixin
from permissions.rest_permissions import CheckAccountUrl
from rsvp.rsvp_helpers import fill_rsvp_responses


class DashboardMeetingViewSet(DashboardQuerysetMixin, AccountSerializerContextMixin, GetMembershipWithURLFallbackMixin, RestPermissionMixin,
                              viewsets.ReadOnlyModelViewSet):
    """
    Dashboard meetings are somewhat specific. This view returns it (reusing logic of Dashboard view):

    - closest repetition of meeting is returned
    - only future meetings are returned (but also for current day)
    - only for next 65 days (current setup)
    - also returns `current_repetition` field which is `rsvp_*` information for this meeting for current user
    """
    serializer_class = DashboardMeetingSerializer
    permission_classes = [IsAuthenticated, CheckAccountUrl]
    permission = [Meeting, 'view']

    def get_queryset(self):
        return self.get_dashboard_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        repetitions = [r for r in page]
        fill_rsvp_responses(repetitions, self.request.user)
        meetings = [r.to_meeting_with_repetition_date() for r in repetitions]

        serializer = self.get_serializer(meetings, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return Response({'result': 'Not supported'}, status=status.HTTP_501_NOT_IMPLEMENTED)
