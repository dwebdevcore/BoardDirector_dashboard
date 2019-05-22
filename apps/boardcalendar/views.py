# -*- coding: utf-8 -*-
from datetime import date, timedelta
from django.views.generic.list import ListView

from accounts.account_helper import get_current_account
from common.mixins import ActiveTabMixin, SelectBoardRequiredMixin
from meetings.models import Meeting, MeetingRepetition
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin


class CalendarView(ActiveTabMixin, SelectBoardRequiredMixin, PermissionMixin, ListView):
    permission = (Meeting, PERMISSIONS.view)
    context_object_name = 'repetitions'
    template_name = 'calendar/calendar_list.html'
    active_tab = 'calendar'

    def get_queryset(self):
        membership = self.request.user.get_membership(get_current_account(self.request))
        queryset = MeetingRepetition.objects.for_membership(membership, only_own_meetings=True).select_related('meeting', 'meeting__account')
        queryset = queryset.filter(meeting__status=Meeting.STATUSES.published)
        queryset = queryset.filter(date__gt=date.today() - timedelta(days=100))
        meetings_list = queryset.distinct()
        return meetings_list

    def get_context_data(self, **kwargs):
        context = super(CalendarView, self).get_context_data(**kwargs)

        context['meetings'] = [r.to_meeting_with_repetition_date() for r in context['repetitions']]

        return context
