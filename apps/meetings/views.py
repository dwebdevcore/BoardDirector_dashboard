# -*- coding: utf-8 -*-
from collections import OrderedDict

import dateutil.parser
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction
from django.http.response import HttpResponse, JsonResponse, Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, gettext
from django.views.generic import DetailView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from accounts.account_helper import get_current_account
from common import signals
from common.ajax import mailto_email
from common.mixins import (ActiveTabMixin, CurrentAccountMixin, RecentActivityMixin,
                           SelectBoardRequiredMixin, AjaxableResponseMixin, DocumentFormInvalidMixin,
                           CurrentMembershipMixin, GetMembershipMixin)
from common.models import TemplateModel
from dashboard.models import RecentActivity
from documents.models import Document, Folder
from meetings.forms import MeetingFilter, MeetingPublishForm, MeetingAddForm
from meetings.models import Meeting, MeetingManager, MeetingRepetition, CalendarConnection, MeetingAttendance
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin
from permissions.shortcuts import has_role_permission, get_object_permissions
from rsvp.models import RsvpResponse
from rsvp.rsvp_helpers import fill_rsvp_responses
from profiles.models import User
import re


class MeetingTypeMixin(object):
    def is_event(self):
        return self.kwargs.get('type', 'meeting') == 'event'

    def get_context_data(self, **kwargs):
        context = super(MeetingTypeMixin, self).get_context_data(**kwargs)
        context['is_event'] = self.is_event()
        context['meeting_type_namespace'] = 'events' if self.is_event() else 'meetings'
        context['meeting_type'] = 'Event' if self.is_event() else 'Meeting'
        context['meeting_translated'] = _('Event') if self.is_event() else _('Meeting')
        context['meetings_translated'] = _('Events') if self.is_event() else _('Meetings')
        return context


class MeetingTabMixin(object):
    @property
    def active_tab(self):
        return 'events' if self.is_event() else 'meetings'


class MeetingsQuerysetMixin(object):
    def get_queryset(self):
        membership = self.request.user.get_membership(get_current_account(self.request))
        queryset = Meeting.objects.for_membership(membership=membership, only_own_meetings=True)

        # Apply event
        queryset = queryset.filter(is_event=self.is_event())

        return queryset


class MeetingsFilteredQuerysetMixin(MeetingsQuerysetMixin):
    def get_queryset(self):
        queryset = super(MeetingsFilteredQuerysetMixin, self).get_queryset()
        if not has_role_permission(self.get_current_membership(), Meeting, PERMISSIONS.edit):
            queryset = queryset.filter(status=Meeting.STATUSES.published)

        default_filters = {'order_by': 'asc', 'committee': '__all__'}
        self.form = MeetingFilter(self.get_current_membership(), self.request.GET, initial=default_filters)
        filters = self.form.cleaned_data if self.form.is_valid() else default_filters

        if filters['committee'] == '__full__':
            queryset = queryset.filter(committee=None)
        elif filters['committee'] != '__all__' and filters['committee'].isdigit():
            queryset = queryset.filter(committee=filters['committee'])

        if filters['order_by'] == 'desc':
            queryset = queryset.order_by('-next_repetition__date')
        else:
            queryset = queryset.order_by('next_repetition__date')

        return queryset.select_related('committee')


class MeetingsViewBase(MeetingTabMixin, ActiveTabMixin, SelectBoardRequiredMixin,
                       MeetingTypeMixin, MeetingsFilteredQuerysetMixin, PermissionMixin, ListView,
                       GetMembershipMixin):
    permission = (Meeting, PERMISSIONS.view)
    context_object_name = 'meetings'

    def get_context_data(self, **kwargs):
        context = super(MeetingsViewBase, self).get_context_data(**kwargs)
        context['form'] = self.form
        return context


class MeetingsView(MeetingsViewBase):
    template_name = 'meetings/meeting_list.html'

    # def get_queryset(self):
    #     return super(MeetingsView, self).get_queryset().extra(**MeetingManager.future_meetings_predicate())

    def get_queryset(self):
        return super(MeetingsView, self).get_queryset()


class PastMeetingsView(MeetingsViewBase):
    template_name = 'meetings/past_meeting_list.html'

    def get_queryset(self):
        return super(PastMeetingsView, self).get_queryset().extra(**MeetingManager.past_meetings_predicate())


class ProcessMeetingActionMixin(object):
    @staticmethod
    def _process_action(meeting, action):
        send_emails = False
        published = False
        if action == 'update-no-email':
            pass
        elif action == 'update':
            send_emails = False  # True
        elif action == 'publish':
            meeting.publish()
            published = True
            # send_emails = True
        elif action == 'revert-to-draft':
            meeting.unpublish()
        else:
            raise AssertionError("Unknown action %s" % (action,))

        return send_emails, published

    def _process_emails(self, meeting, send_emails):
        if send_emails:
            if meeting.account.send_notification:
                meeting.send_details_email(save=False, exclude_user=self.request.user)
                messages.success(self.request, _('Meeting details were mailed successfully.'))
            else:
                messages.warning(self.request,
                                 _("Email wasn't sent because notifications are switched off for the board."))


class MeetingCreateView(MeetingTabMixin, CurrentAccountMixin, CurrentMembershipMixin, ActiveTabMixin, SelectBoardRequiredMixin, PermissionMixin,
                        MeetingTypeMixin, DocumentFormInvalidMixin, CreateView, RecentActivityMixin, GetMembershipMixin, ProcessMeetingActionMixin):
    permission = (Meeting, PERMISSIONS.add)
    form_class = MeetingAddForm
    template_name = 'meetings/meeting_add.html'

    def get_form_kwargs(self):
        kwargs = super(MeetingCreateView, self).get_form_kwargs()
        kwargs['is_event'] = self.is_event()
        return kwargs

    def get_initial(self):
        initial = super(MeetingCreateView, self).get_initial()
        return initial

    @transaction.atomic
    def form_valid(self, form):

        meeting = self.object = form.save(commit=False)
        print(meeting.id, meeting.created_at, meeting.updated_at)
        meeting_is_new = meeting.id is None

        meeting.account = get_current_account(self.request)

        if not meeting.id and not meeting.created_by:
            meeting.created_by = self.request.user.membership_set.get(account=meeting.account)

        start = '{0}T{1}'.format(form.cleaned_data['date'], form.cleaned_data['time_start'])
        end = '{0}T{1}'.format(form.cleaned_data['date'], form.cleaned_data['time_end'])
        meeting.start = timezone.make_aware(dateutil.parser.parse(start), timezone.get_current_timezone())
        meeting.end = timezone.make_aware(dateutil.parser.parse(end), timezone.get_current_timezone())
        meeting.is_event = self.is_event()

        send_emails, _ = self._process_action(meeting, form.cleaned_data['action'])

        meeting.save()
        if form.cleaned_data['uploaded']:
            Folder.objects.update_or_create_meeting_folder(meeting)
            docs = form.cleaned_data['uploaded'].split(',')
            Document.objects.filter(id__in=docs).update(folder=self.object.folder)

        self.save_recent_activity(action_flag=self.get_action_flag())
        self.get_success_message()
        signals.view_create.send(sender=self.__class__, instance=self.object, request=self.request)

        form.save_m2m()

        try:
            self._process_emails(meeting, send_emails)
            meeting.notify_admins_email(created=meeting_is_new)
        except:
            pass

        meeting.save()  # Once more to save date changes

        return super(MeetingCreateView, self).form_valid(form)

    def get_success_message(self):
        messages.success(self.request, _('Event was added successfully.')
                         if self.is_event() else _('Meeting was added successfully.'))

    def get_success_url(self):
        return reverse('events:detail' if self.is_event() else 'meetings:detail',
                       kwargs={'pk': self.object.pk, 'url': get_current_account(self.request).url})

    def get_action_flag(self):
        return RecentActivity.ADDITION


class MeetingUpdateView(MeetingsQuerysetMixin, MeetingCreateView, UpdateView):
    permission = (Meeting, PERMISSIONS.edit)
    form_class = MeetingAddForm
    template_name = 'meetings/meeting_update.html'

    def get_success_message(self):
        messages.success(self.request, _('Event was changed successfully.')
                         if self.is_event() else _('Meeting was changed successfully.'))

    def get_action_flag(self):
        return RecentActivity.CHANGE


class MeetingDetailView(MeetingTabMixin, ActiveTabMixin, SelectBoardRequiredMixin, MeetingsQuerysetMixin, MeetingTypeMixin,
                        PermissionMixin, DetailView, GetMembershipMixin):
    permission = (Meeting, PERMISSIONS.view)
    context_object_name = 'meeting'
    template_name = 'meetings/meeting_detail.html'

    def post(self, request, *args, **kwargs):
        """
        process ajax request for recording meeting attendance.
        """
        try:
            meeting = Meeting.objects.get(id=request.POST['meeting'])
            if not (self.get_current_membership().is_admin and meeting.start < timezone.now()):
                raise PermissionDenied(_("Can't set attendance: not admin or meeting hasn't yet started"))

            user = User.objects.get(id=request.POST['user'])

            obj, created = MeetingAttendance.objects.get_or_create(meeting=meeting, user=user)
            obj.present = request.POST['present']
            obj.save()
            return HttpResponse('success')

        except Exception as e:
            print('%s (%s)' % (e, type(e)))
            return HttpResponse("Backend Error")

    def get_context_data(self, **kwargs):
        context = super(MeetingDetailView, self).get_context_data(**kwargs)
        account = get_current_account(self.request)

        meeting = self.object
        context.update(self.get_meeting_details(meeting, self.get_queryset(),
                                                self.request.user, account, self.request.GET.get('date')))
        context["publish_form"] = MeetingPublishForm(meeting, self.get_current_membership())
        return context

    @staticmethod
    def get_meeting_details(meeting, queryset, for_user, account, for_date):
        """
        Method is extracted into static to be reused for REST serializer
        """
        context = OrderedDict()
        # next/previous meeting
        previous_meeting = queryset.filter(start__lte=meeting.start).exclude(id=meeting.id).order_by('-start')
        next_meeting = queryset.filter(start__gt=meeting.start).exclude(id=meeting.id).order_by('start')
        context['next'] = next_meeting[0] if next_meeting else None
        context['previous'] = previous_meeting[0] if previous_meeting else None

        # members_email
        membership = for_user.get_membership(account)
        permissions = get_object_permissions(membership, meeting)

        if meeting.committee:
            context['members_email'] = mailto_email((meeting.committee,))
        else:
            members_email = 'mailto:'
            for member in meeting.account.memberships.all():
                if member.user.email not in members_email:
                    members_email += '{},'.format(member.user.email)
            context['members_email'] = members_email[:-1]

        # if the user is assistant to board member, then we should use boss data
        boss_users = [boss.user for boss in membership.get_bosses()]

        # rsvp
        repetition = None
        if for_date:
            try:
                date = dateutil.parser.parse(for_date)

                repetition = meeting.repetitions.filter(date=date).get()
            except (MeetingRepetition.DoesNotExist, ValueError):
                pass

        if repetition is None:
            repetition = meeting.closest_repetition

        assert isinstance(repetition, MeetingRepetition)

        # Query and process the RSVP responses
        # Implementation note: pull all RSVP records for this meeting from the database in one query.
        # Processing into current and historical RSVP data is done in python because it's faster than chatty DB queries.
        rsvp_for_all_repetitions = meeting.rsvp_responses.filter(user__is_active=True, meeting_repetition=None) \
            .order_by("timestamp") \
            .select_related("user")
        rsvp_for_repetition = repetition.rsvp_responses.filter(user__is_active=True) \
            .order_by("timestamp") \
            .select_related("user")
        rsvp_by_user = {}
        meeting_members = meeting.members
        meeting_members_by_user_id = {m.user.id: m for m in meeting_members}

        rsvp = sorted(list(rsvp_for_all_repetitions) + list(rsvp_for_repetition), key=lambda r: r.timestamp)

        for r in rsvp:
            if r.user.pk not in meeting_members_by_user_id:
                # Filter out situation where user rsvped and then was removed from members for meeting.
                continue

            obj = {
                "timestamp": r.timestamp,
                "user_id": r.user.pk,
                "name": r.user.get_full_name(),
                "email": r.user.email,
                "is_attending": r.response == RsvpResponse.ACCEPT,
                "attending": r.get_response_display(),
                "accept_type": r.accept_type,
                "accept_type_display": r.get_accept_type_display(),
                "note": r.note,
                "is_invited": meeting_members_by_user_id[r.user.pk].is_meeting_member_invited,
                "icon": (r.response == RsvpResponse.ACCEPT) and "check.png" or
                        (r.response == RsvpResponse.DECLINE) and "cancel.png" or "question.png",
            }
            if r.user.pk in rsvp_by_user:
                rsvp_by_user[r.user.pk].append(obj)
            else:
                rsvp_by_user[r.user.pk] = [obj]

        # Also include pseudo-rsvp-responses for the users who did not respond to the RSVP
        no_rsvp = [m for m in meeting_members if m.user.id not in rsvp_by_user.keys()]
        for r in no_rsvp:
            obj = {
                "timestamp": timezone.now(),
                "user_id": r.user.pk,
                "name": r.user.get_full_name(),
                "email": r.user.email,
                "is_attending": False,
                "attending": _('No reply'),
                "is_invited": r.is_meeting_member_invited,
                "icon": "question.png",
            }
            rsvp_by_user[r.user.pk] = [obj]

        context["rsvp_responses"] = [user_responses[-1] for user_responses in rsvp_by_user.values()]
        for r in context["rsvp_responses"]:
            r["history"] = rsvp_by_user.get(r["user_id"], [])[:-1]
        context["rsvp_responses"] = sorted(context["rsvp_responses"], key=lambda r: r["name"])

        context["rsvp_attendance"] = len([r for r in context["rsvp_responses"] if r["is_attending"]])

        context["current_repetition"] = repetition
        fill_rsvp_responses([repetition], for_user if len(boss_users) == 0 else boss_users[0])

        future_repetitions = meeting.future_repetitions()[:10]
        if meeting.repeat_type:
            fill_rsvp_responses(future_repetitions, for_user if len(boss_users) == 0 else boss_users[0])
            # and [m for m in meeting_members if m.user_id == for_user.id]:
            # fill_rsvp_responses(future_repetitions, for_user)

        context["future_repetitions"] = future_repetitions

        # Add actual attendance records
        context['record_attendance'] = False

        if membership.is_admin and meeting.start < timezone.now():
            context['record_attendance'] = True
            context['attendance_choice'] = MeetingAttendance.PRESENT_TYPES

        ma_values = MeetingAttendance.objects.filter(meeting=meeting).values("user_id", "present")
        ma = {x["user_id"]: x["present"] for x in ma_values}

        for r in context["rsvp_responses"]:
            r["present"] = ma.get(r["user_id"], None)

        # get calendar connections
        context['has_social_connections'] = False
        context['is_google_connected'] = False
        context['is_office_connected'] = False
        context['is_ical_connected'] = False

        cal_connections = CalendarConnection.objects.filter(account=account)
        for conn in cal_connections:
            context['has_social_connections'] = True
            if conn.provider == 'google':
                context['is_google_connected'] = True
                context['checked_google_add'] = conn.checked_add

            if conn.provider == 'office':
                context['is_office_connected'] = True
                context['checked_office_add'] = conn.checked_add

            if conn.provider == 'ical':
                context['is_ical_connected'] = True
                context['checked_ical_add'] = conn.checked_add

        # approved documents list
        agenda = meeting.get_agenda()
        context['agenda_approved'] = list(agenda.approved_user_ids() if agenda else [])
        context['any_approved'] = set(context['agenda_approved'])
        bbook = meeting.get_board_book()
        context['boardbook_approved'] = list(bbook.approved_user_ids() if bbook else [])
        context['any_approved'].update(context['boardbook_approved'])
        minutes = meeting.get_minutes()
        context['minutes_approved'] = list(minutes.approved_user_ids() if minutes else [])
        context['any_approved'].update(context['minutes_approved'])

        return context


class MeetingDeleteView(AjaxableResponseMixin, SelectBoardRequiredMixin, MeetingsQuerysetMixin, MeetingTypeMixin, PermissionMixin, DeleteView):
    permission = (Meeting, PERMISSIONS.delete)

    def delete(self, request, *args, **kwargs):
        """
        Remove all Meeting's documents
        """
        self.object = self.get_object()
        try:
            documents = Document.objects.filter(folder=self.object.folder)
            RecentActivity.objects.filter(
                object_id__in=documents.values_list('id', flat=True),
                content_type_id=ContentType.objects.get_for_model(Document)
            ).delete()
            documents.delete()
        except Folder.DoesNotExist:
            pass
        RecentActivity.objects.filter(
            object_id=self.object.id,
            content_type_id=ContentType.objects.get_for_model(self.object)
        ).delete()
        self.object.delete()
        messages.success(request, _('Event was deleted.') if self.is_event() else _('Meeting was deleted.'))
        return self.render_to_json_response({'url': self.get_success_url()})

    def get_success_url(self):
        url_name = 'events:list' if self.is_event() else 'meetings:list'
        return reverse(url_name, kwargs={'url': get_current_account(self.request).url})


class MeetingMailView(AjaxableResponseMixin, SelectBoardRequiredMixin, MeetingsQuerysetMixin,
                      MeetingTypeMixin, PermissionMixin, UpdateView):
    permission = (Meeting, PERMISSIONS.edit)

    def post(self, request, *args, **kwargs):

        meeting = self.get_object()

        if not meeting.account.send_notification:
            messages.warning(request, _('Email notifications are disabled for this board.'))

        else:

            ctx = {}

            pmessage = request.POST.get('pmessage', '').strip()
            pmessage = re.sub('[\n\r]+', '\n', pmessage)
            if len(pmessage) > 0:
                ctx['pmessage'] = pmessage

            ctx['attachdocs'] = 'attachdocs' in request.POST

            if meeting.last_email_sent is not None and request.POST.get('kind') == 'reminder':
                template_name = TemplateModel.MEETING_REMINDER
            else:
                template_name = TemplateModel.MEETING

            meeting.send_details_email(template_name=template_name,
                                       extra_ctx=ctx)  # exclude_user=request.user)
            msg = self.get_success_message()
            messages.success(request, msg)  # There'll be a refresh.

        if 'ajax' in request.POST:
            return self.render_to_json_response({'url': meeting.get_absolute_url(),
                                                 'message': msg})

        return redirect(meeting.get_absolute_url())

    def get_success_message(self):
        msg = gettext('Meeting details were mailed successfully.')
        return msg


class MeetingPublishView(SelectBoardRequiredMixin, MeetingsQuerysetMixin, MeetingTypeMixin,
                         PermissionMixin, UpdateView, ProcessMeetingActionMixin, GetMembershipMixin):
    permission = (Meeting, PERMISSIONS.edit)

    def post(self, request, *args, **kwargs):
        meeting = self.get_object()
        form = MeetingPublishForm(meeting, self.get_current_membership(), request.POST)
        if form.is_valid():
            send_emails, published = self._process_action(meeting, form.cleaned_data['action'])
            self._process_emails(meeting, send_emails)
            meeting.save()

            if published:
                messages.success(self.request, _('Meeting was published.'))
            else:
                messages.success(self.request, _('Meeting was reverted to draft.'))
        else:
            messages.warning(self.request, _('Form has errors and meeting can\'t be updated.'))

        return redirect(meeting.get_absolute_url())


class MeetingDownloadCardView(SelectBoardRequiredMixin, MeetingsQuerysetMixin, MeetingTypeMixin, PermissionMixin, DetailView, GetMembershipMixin):
    permission = (Meeting, PERMISSIONS.view)

    def get(self, request, *args, **kwargs):
        meeting = self.get_object()
        assert isinstance(meeting, Meeting)

        ics = meeting.generate_ics(meeting.creator.user, self.get_current_membership())

        response = HttpResponse(content_type='application/force-download', content=ics)
        response['Content-Disposition'] = 'attachment; filename=meeting-{id}.ics'.format(id=meeting.id)
        return response
