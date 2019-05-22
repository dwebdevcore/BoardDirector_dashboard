# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from accounts.account_helper import get_current_account
from committees.forms import CommitteeFilter
from common import signals
from common.ajax import mailto_email
from common.mixins import (ActiveTabMixin, CurrentAccountMixin, RecentActivityMixin,
                           SelectBoardRequiredMixin, AjaxableResponseMixin, GetMembershipMixin)
from dashboard.models import RecentActivity
from documents.forms import DocumentAddForm
from documents.models import Document, Folder
from documents.views.folder import FolderContextMixin
from meetings.models import Meeting
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin
from .forms import CommitteeAddForm
from .models import Committee


class CommitteeQuerysetMixin(object):
    def get_queryset(self):
        membership = self.request.user.get_membership(get_current_account(self.request))
        queryset = Committee.objects.for_membership(membership=membership)
        return queryset


class CommitteesView(ActiveTabMixin, SelectBoardRequiredMixin, CommitteeQuerysetMixin, PermissionMixin, ListView, GetMembershipMixin):
    permission = (Committee, PERMISSIONS.view)
    context_object_name = 'committees'
    template_name = 'committees/committee_list.html'
    active_tab = 'committees'

    def get_queryset(self):
        default_filters = {'committee': ''}
        self.form = CommitteeFilter(self.get_current_membership(), self.request.GET, initial=default_filters)
        filters = self.form.cleaned_data if self.form.is_valid() else default_filters

        queryset = super(CommitteesView, self).get_queryset()
        if filters['committee']:
            queryset = queryset.filter(pk=filters['committee'])

        return queryset.prefetch_related('chairman')

    def get_context_data(self, **kwargs):
        context = super(CommitteesView, self).get_context_data(**kwargs)
        context['members_email'] = mailto_email(context['committees'])
        context['form'] = self.form
        return context


class CommitteeCreateView(CurrentAccountMixin, ActiveTabMixin, SelectBoardRequiredMixin, RecentActivityMixin,
                          CommitteeQuerysetMixin, PermissionMixin, CreateView):
    permission = (Committee, PERMISSIONS.add)
    form_class = CommitteeAddForm
    template_name = 'committees/committee_update.html'
    active_tab = 'committees'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.account = get_current_account(self.request)
        self.object.save()
        for membership in form.cleaned_data['members']:
            membership.committees.add(self.object)
        chairman_memberships = form.cleaned_data['chairman'].all()
        for chairman_membership in chairman_memberships:
            chairman_membership.committees.add(self.object)
        self.save_recent_activity(action_flag=RecentActivity.ADDITION)
        messages.success(self.request, _('Committee was added successfully.'))
        signals.view_create.send(sender=self.__class__, instance=self.object, request=self.request)
        return super(CommitteeCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('committees:list', kwargs={'url': get_current_account(self.request).url})


class CommitteeUpdateView(CurrentAccountMixin, ActiveTabMixin, SelectBoardRequiredMixin, RecentActivityMixin,
                          CommitteeQuerysetMixin, PermissionMixin, UpdateView):
    permission = (Committee, PERMISSIONS.edit)
    form_class = CommitteeAddForm
    template_name = 'committees/committee_update.html'
    active_tab = 'committees'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.account = get_current_account(self.request)
        self.object.save()
        for membership in self.object.memberships.exclude(Q(pk__in=form.cleaned_data['members']) |
                                                          Q(pk__in=form.cleaned_data['chairman'].all())):
            membership.committees.remove(self.object)
        for membership in form.cleaned_data['members']:
            if not membership.committees.filter(id=self.object.id).exists():
                membership.committees.add(self.object)
        self.save_recent_activity(action_flag=RecentActivity.CHANGE)
        messages.success(self.request, _('Committee was changed successfully.'))
        return super(CommitteeUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('committees:detail', kwargs={'pk': self.object.pk,
                                                    'url': get_current_account(self.request).url})


class CommitteeDetailView(ActiveTabMixin, SelectBoardRequiredMixin,
                          CommitteeQuerysetMixin, PermissionMixin, FolderContextMixin, DetailView):
    permission = (Committee, PERMISSIONS.view)
    context_object_name = 'committee'
    template_name = 'committees/committee_detail.html'
    active_tab = 'committees'

    def get_folder(self):
        self.folder = Folder.objects.filter(account=get_current_account(self.request), committee=self.object).first()
        return self.folder

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Committee.DoesNotExist:
            messages.error(self.request, _('Sorry, you have no permissions to view this committee.'))
            return redirect('accounts:boards')

        context = self.get_context_data(object=self.object)
        context['chairman'] = self.object.chairman.all()
        context['ordinary_members'] = self.object.ordinary_members()
        context['members_email'] = mailto_email([self.object])
        context['folder'] = self.folder
        context['add_document_form'] = DocumentAddForm()

        return self.render_to_response(context)


class CommitteeDeleteView(AjaxableResponseMixin, SelectBoardRequiredMixin,
                          CommitteeQuerysetMixin, PermissionMixin, DeleteView):
    permission = (Committee, PERMISSIONS.delete)

    def delete(self, request, *args, **kwargs):
        """
        Remove all Committee's meetings and documents
        """
        self.object = self.get_object()
        related_meetings_list = self.object.meetings.all().values_list('id', flat=True)
        RecentActivity.objects.filter(
            object_id__in=Document.objects.filter(
                folder__meeting_id__in=related_meetings_list).values_list('id', flat=True),
            content_type_id=ContentType.objects.get_for_model(Document)).delete()
        Document.objects.filter(folder__meeting_id__in=related_meetings_list).delete()
        RecentActivity.objects.filter(
            object_id__in=related_meetings_list,
            content_type_id=ContentType.objects.get_for_model(Meeting)).delete()
        Meeting.objects.filter(id__in=related_meetings_list).delete()
        RecentActivity.objects.filter(
            object_id=self.object.id,
            content_type_id=ContentType.objects.get_for_model(self.object)).delete()
        self.object.delete()
        messages.success(request, _('Committee was deleted.'))
        return self.render_to_json_response({'url': self.get_success_url()})

    def get_success_url(self):
        return reverse('committees:list', kwargs={'url': get_current_account(self.request).url})
