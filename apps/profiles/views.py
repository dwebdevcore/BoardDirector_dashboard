# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth import views as auth_views
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _, gettext
from django.views.generic import DetailView, View
from django.views.generic.edit import FormView, DeleteView

from accounts.account_helper import get_current_account
from .models import Membership, User, TemporaryUserPassword
from .forms import MembershipEditForm, MembershipAdminEditForm, AssistantEditForm
from accounts.mixins import MembershipQuerysetMixin, MemberEditMixin
from common.mixins import (ActiveTabMixin, SelectBoardRequiredMixin, AjaxableResponseMixin,
                           CurrentAccountMixin, CurrentMembershipMixin, GetMembershipMixin)
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin

from django.contrib.contenttypes.models import ContentType
from dashboard.models import RecentActivity
from documents.models import Document, Folder
from meetings.models import CalendarConnection
from common.authhelper import get_google_signin_url, get_office_signin_url
import django.contrib.auth


class MemberView(ActiveTabMixin, SelectBoardRequiredMixin, MembershipQuerysetMixin, PermissionMixin, DetailView, GetMembershipMixin):
    permission = (Membership, PERMISSIONS.view)
    context_object_name = 'membership_object'
    template_name = 'profiles/members_bio.html'
    active_tab = 'members'

    def get_context_data(self, **kwargs):
        context = super(MemberView, self).get_context_data(**kwargs)
        context['social_mapping'] = settings.SOCIAL_MAPPING
        if context['object'].pk != self.get_current_membership().pk:
            if context['object'].is_guest:
                context['active_tab'] = 'guests'
            else:
                context['active_tab'] = 'members'
        return context

    def get_object(self, queryset=None):
        if 'pk' in self.kwargs:
            return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        else:
            return self.request.user.get_membership(get_current_account(self.request))


class AssistantView(ActiveTabMixin, SelectBoardRequiredMixin, MembershipQuerysetMixin, PermissionMixin, DetailView):
    permission = (Membership, PERMISSIONS.view)
    context_object_name = 'membership_object'
    template_name = 'profiles/members_bio.html'  # 'profiles/assistants_bio.html' ?
    active_tab = 'guests'

    def get_context_data(self, **kwargs):
        ctx = super(AssistantView, self).get_context_data(**kwargs)
        ctx['member'] = self.get_queryset().get(pk=self.kwargs['member_pk'])
        return ctx

    def get_object(self, queryset=None):
        assistant = get_object_or_404(self.get_queryset(), pk=self.kwargs['member_pk']).assistant
        if assistant.is_active:
            return assistant
        return None

    def get(self, request, *args, **kwargs):
        response = super(AssistantView, self).get(request, *args, **kwargs)
        if self.object:
            return response
        return redirect(reverse('assistant_create', kwargs={'url': get_current_account(self.request).url,
                                                            'pk': self.kwargs['pk']}))


class InviteMemberView(AjaxableResponseMixin, SelectBoardRequiredMixin, PermissionMixin, View):
    permission = (Membership, PERMISSIONS.add)

    def process_invite_view(self, request, user_pk, *args, **kwargs):
        current_account = get_current_account(request)
        membership = request.user.get_membership(current_account)
        user = get_object_or_404(User, pk=user_pk, accounts=current_account)
        try:
            password = user.tmppswd.password
        except TemporaryUserPassword.DoesNotExist:
            password = None
        user.send_invitation_email(
            account=current_account,
            password=password,
            message=kwargs.get('message', None),
            from_member=membership
        )
        member = user.get_membership(current_account)
        member.invitation_status = Membership.INV_SENT
        member.save()
        return redirect(reverse('profiles:detail', kwargs={'pk': user.get_membership(current_account).pk}))

    def get(self, request, user_pk, *args, **kwargs):
        resp = self.process_invite_view(request, user_pk, **kwargs)
        messages.success(request, _('Invitation was sent successfully.'))
        return resp

    def post(self, request, user_pk, *args, **kwargs):
        kwargs.update({'message': request.POST.get('personal-message')})
        self.process_invite_view(request, user_pk, **kwargs)
        msg = gettext('Invitation was sent successfully.')
        return self.render_to_json_response({'msg': str(msg)})


class EditProfileView(CurrentAccountMixin, CurrentMembershipMixin, MemberEditMixin, SelectBoardRequiredMixin,
                      MembershipQuerysetMixin, PermissionMixin, FormView):

    permission = (Membership, PERMISSIONS.edit)
    template_name = 'profiles/edit_profile.html'

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])

    def get_form_class(self):
        current_account = get_current_account(self.request)
        membership = self.request.user.get_membership(current_account)
        if membership.is_admin:
            self.form_class = MembershipAdminEditForm
        else:
            self.form_class = MembershipEditForm
        return super(EditProfileView, self).get_form_class()

    def get_success_url(self):
        if self.object.is_active:
            return reverse('profiles:detail', kwargs={'pk': self.kwargs['pk']})
        else:
            return reverse('board_members', kwargs={'url': self.object.account.url})

    def get_context_data(self, **kwargs):
        context = super(EditProfileView, self).get_context_data(**kwargs)

        current_account = get_current_account(self.request)

        context['role_choice'] = Membership.ROLES

        # connected calendars
        calendars = CalendarConnection.objects.filter(account=current_account)
        available_providers = [c.provider for c in calendars]
        context['is_google_connected'] = 'google' in available_providers
        context['is_office_connected'] = 'office' in available_providers
        context['is_ical_connected'] = 'ical' in available_providers

        redirect_google_uri = self.request.build_absolute_uri(reverse('google_token'))
        redirect_office_uri = self.request.build_absolute_uri(reverse('office_token'))
        context['google_url'] = get_google_signin_url(redirect_google_uri)
        context['office_url'] = get_office_signin_url(redirect_office_uri)
        context['ical_url'] = '#'

        context['social_mapping'] = settings.SOCIAL_MAPPING

        return context


class EditAssistantView(CurrentAccountMixin, CurrentMembershipMixin, MemberEditMixin, SelectBoardRequiredMixin,
                        MembershipQuerysetMixin, PermissionMixin, FormView):
    permission = (Membership, PERMISSIONS.edit)
    template_name = 'profiles/assistant_profile.html'
    form_class = AssistantEditForm

    def get_permission_object(self):
        assistant = get_object_or_404(self.get_queryset(), pk=self.kwargs['member_pk']).assistant
        if assistant.is_active:
            return assistant
        return None

    def get_success_url(self):
        return reverse('profiles:assistant_detail', kwargs={'pk': self.kwargs['pk'], 'member_pk': self.kwargs['member_pk']})


class MembershipDeleteView(AjaxableResponseMixin, SelectBoardRequiredMixin, MembershipQuerysetMixin, PermissionMixin, DeleteView):
    permission = (Membership, PERMISSIONS.delete)

    def and_permission(self, account, membership):
        membership_to_delete = self.get_object()
        # can't delete your own membership, only admin can delete admin
        return (membership_to_delete.user_id != membership.user_id and
                (not membership_to_delete.is_admin or membership.is_admin))

    def delete(self, request, *args, **kwargs):
        membership = self.get_object()

        try:
            documents = Document.objects.filter(folder=membership.private_folder)
            RecentActivity.objects.filter(
                object_id__in=documents.values_list('id', flat=True),
                content_type_id=ContentType.objects.get_for_model(Document)
            ).delete()
            documents.delete()
        except Folder.DoesNotExist:
            pass
        RecentActivity.objects.filter(
            object_id=membership.id,
            content_type_id=ContentType.objects.get_for_model(membership)
        ).delete()

        membership.user.delete()
        membership.delete()

        messages.success(request, _('Profile was deleted.'))

        self.object = membership  # for AjaxableResponseMixin
        return self.render_to_json_response({'url': self.get_success_url()})

    def get_success_url(self):
        if self.object.is_guest:
            return reverse('board_guests', kwargs={'url': get_current_account(self.request).url})
        else:
            return reverse('board_members', kwargs={'url': get_current_account(self.request).url})


class AssistantDeleteView(AjaxableResponseMixin, SelectBoardRequiredMixin, MembershipQuerysetMixin, PermissionMixin, DeleteView):
    permission = (Membership, PERMISSIONS.delete)

    def delete(self, request, *args, **kwargs):
        """
        Hide this user's membership
        """
        member = get_object_or_404(self.get_queryset(), pk=self.kwargs['member_pk'])
        assistant = self.get_object()
        member.assistant = None
        member.save()
        if not Membership.objects.filter(assistant=assistant):
            # if has no other bosses, deactivate
            assistant.deactivate()

        messages.success(request, _('Profile was deactivated.'))
        self.object = assistant  # for AjaxableResponseMixin
        return self.render_to_json_response({'url': self.get_success_url()})

    def get_success_url(self):
        return reverse('board_members', kwargs={'url': get_current_account(self.request).url})


class LoginView(View):
    def login(self, *args, **kwargs):
        """
        when set_expiry(0)
        the user’s session cookie will expire when the user’s Web browser is closed.
        """
        if self.request.method == 'POST':
            if not self.request.POST.get('rememberme'):
                self.request.session.set_expiry(0)

        redirect_to = self.request.GET.get(REDIRECT_FIELD_NAME, self.request.POST.get(REDIRECT_FIELD_NAME, ''))
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

        auth_response = auth_views.login(self.request, *args, **kwargs)
        if isinstance(auth_response, TemplateResponse):
            auth_response.context_data['social_mapping'] = settings.SOCIAL_MAPPING

        if not self.request.user.is_anonymous:
            memberships = self.request.user.membership_set.filter(
                is_active=True).exclude(invitation_status=Membership.INV_INVITED)
            memberships.update(invitation_status=Membership.INV_INVITED)

        if self.request.is_ajax():
            if self.request.user.is_anonymous:
                data = json.dumps({
                    'logged_in': False,
                    'html': auth_response.rendered_content,
                })
            else:
                data = json.dumps({
                    'logged_in': True,
                    'redirect': redirect_to,
                })

            return HttpResponse(data, content_type='application/json')

        if auth_response:
            return auth_response
        else:
            return redirect(redirect_to)

    def get(self, request, *args, **kwargs):
        return self.login(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.login(*args, **kwargs)


def switch_user(request):
    if 'user_id' in request.GET:
        if request.user.is_superuser:
            previous_user_id = request.user.id
            user = get_object_or_404(User, pk=int(request.GET['user_id']))
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            request.session['previous_user'] = previous_user_id
            return redirect('accounts:boards')
        else:
            raise PermissionDenied('Only superuser has this powers.')
    else:
        return HttpResponse("user_id is required GET param.", status=400)
