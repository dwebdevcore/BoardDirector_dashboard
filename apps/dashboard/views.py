# -*- coding: utf-8 -*-
from __future__ import print_function
import datetime

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from accounts.account_helper import get_current_account
from committees.models import Committee
from common.mixins import LoginRequiredMixin, ActiveTabMixin, SelectBoardRequiredMixin
from documents.models import Document
from meetings.models import Meeting, MeetingNextRepetition, MeetingRepetition
from news.models import News
from profiles.models import Membership
from rsvp.rsvp_helpers import fill_rsvp_responses
from .models import RecentActivity


class DashboardQuerysetMixin(object):
    def get_dashboard_queryset(self):

        membership = self.request.user.get_membership(get_current_account(self.request))

        after_date = timezone.localdate(timezone.now())
        until_date = after_date + datetime.timedelta(days=settings.DASHBOARD_MEETINGS_COUNT)

        queryset = MeetingRepetition.objects.for_membership(membership, only_own_meetings=True)\
            .select_related('meeting', 'meeting__account')\
            .filter(date__gte=after_date)\
            .filter(meeting__status=Meeting.STATUSES.published)

        _queryset = queryset.filter(date__lte=until_date).order_by('date')

        if len(_queryset) < 10:
            return queryset.order_by('date')[:10]
        else:
            return _queryset


class DashboardView(ActiveTabMixin, LoginRequiredMixin, DashboardQuerysetMixin, SelectBoardRequiredMixin, ListView):
    context_object_name = 'repetitions'
    template_name = 'dashboard/dashboard.html'
    active_tab = 'dashboard'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        account = get_current_account(request)
        # redirect to getting started if admins first time
        if account and account.show_guide:
            membership = request.user.membership_set.get(account=account)
            if membership.is_admin and not request.session.get('has_seen_guide', False):
                return redirect('dashboard:getting_started', url=account.url)
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(DashboardView, self).get_context_data(*args, **kwargs)
        account = get_current_account(self.request)
        membership = self.request.user.membership_set.get(account=account)
        context['account'] = account
        context['news'] = News.objects.filter(account=account, is_publish=True)[:3]
        context['activity_list'] = RecentActivity.objects.for_membership(membership)[:4]
        context['now'] = timezone.now()

        repetitions = context['repetitions']
        # [r.repetition for r in context['repetitions']]
        # Note: repetitions is actually a special MeetingNextRepetition class - i.e. only one next repetition per meeting.
        context['meetings'] = [r.to_meeting_with_repetition_date() for r in repetitions]

        fill_rsvp_responses(repetitions, self.request.user)
        if membership.role == membership.ROLES.assistant:
            for boss in membership.get_bosses():
                fill_rsvp_responses(repetitions, boss.user)

        return context

    def get_queryset(self):
        return self.get_dashboard_queryset()


class GettingStartedView(LoginRequiredMixin, SelectBoardRequiredMixin, TemplateView):
    template_name = 'dashboard/getting_started.html'

    def dispatch(self, request, *args, **kwargs):
        account = get_current_account(request)
        if self.request.GET.get('show_guide') == 'false':
            account.show_guide = False
            account.save(update_fields=['show_guide'])
            return redirect('dashboard:dashboard', url=account.url)
        request.session['has_seen_guide'] = True
        return super(GettingStartedView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(GettingStartedView, self).get_context_data(*args, **kwargs)
        account = get_current_account(self.request)
        context['has_memberships'] = Membership.objects.filter(account=account).count() > 1
        context['has_meetings'] = Meeting.objects.filter(account=account).exists()
        context['has_documents'] = Document.objects.filter(account=account).exists()
        context['has_committees'] = Committee.objects.filter(account=account).count() > 1
        return context


class ActivitiesView(ActiveTabMixin, LoginRequiredMixin, SelectBoardRequiredMixin, ListView):
    model = RecentActivity
    context_object_name = 'recent'
    template_name = 'dashboard/activity.html'
    active_tab = 'dashboard'
    paginate_by = 6

    def get_queryset(self):
        membership = self.request.user.get_membership(get_current_account(self.request))
        activity_list = RecentActivity.objects.for_membership(membership)
        return activity_list
