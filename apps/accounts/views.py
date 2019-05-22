# -*- coding: utf-8 -*-
import json
import os
import mm
import cStringIO as StringIO
import xhtml2pdf.pisa as pisa
from cgi import escape

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.template.loader import render_to_string
from django.views.generic import DetailView, ListView, CreateView
from django.views.generic.edit import BaseFormView, View, BaseUpdateView
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.template.loader import get_template
from django.template import Context

from accounts.account_helper import get_current_account, set_current_account, clear_current_account
from .forms import AccountReactivateForm, AccountLogo, AccountNotify
from .models import Account
from accounts.mixins import MembershipQuerysetMixin, MemberCreateMixin
from common.mixins import (ActiveTabMixin, LoginRequiredMixin, CurrentAccountMixin,
                           RecentActivityMixin, SelectBoardRequiredMixin, AjaxableResponseMixin,
                           AccountGetObjectMixin, GetDataMixin)
from common.mixins import MemberNotificationMixin
from profiles.forms import MemberAddForm, GuestAddForm, AssistantAddForm
from profiles.models import TemporaryUserPassword
from profiles.models import User, Membership
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin
from permissions.shortcuts import has_role_permission


class MembersView(ActiveTabMixin, SelectBoardRequiredMixin, MembershipQuerysetMixin, PermissionMixin, ListView):
    permission = (Membership, PERMISSIONS.view)
    model = Membership
    context_object_name = 'memberships'
    template_name = 'accounts/members_list.html'
    active_tab = 'members'

    def dispatch(self, request, *args, **kwargs):
        self.init_roles()
        return super(MembersView, self).dispatch(request, *args, **kwargs)

    def init_roles(self):
        self.role_values = (Membership.ROLES.chair, Membership.ROLES.ceo,
                            Membership.ROLES.director, Membership.ROLES.member)
        self.role_choices = [r for r in Membership.ROLES if r[0] in self.role_values]

    def get_queryset(self):
        queryset = super(MembersView, self).get_queryset()
        queryset = queryset.filter(role__in=self.role_values)
        # annotation if for define if user is chairman, calculates count of committees where user is chairman, and if
        # grater than 0 he is chairman
        return queryset.annotate(chairman=Count('committee__chairman')).order_by('last_name', 'user__email')

    def get_context_data(self, *args, **kwargs):
        context = super(MembersView, self).get_context_data(*args, **kwargs)
        context['membership_roles'] = self.role_choices
        context['active_members'] = self.get_queryset().filter(is_active=True)
        context['inactive_members'] = self.get_queryset().filter(is_active=False)
        return context


class GuestsView(MembersView):
    template_name = 'accounts/guests_list.html'
    active_tab = 'guests'

    def init_roles(self):
        self.role_values = (Membership.ROLES.guest, Membership.ROLES.vendor, Membership.ROLES.staff,
                            Membership.ROLES.consultant, Membership.ROLES.assistant)
        self.role_choices = [r for r in Membership.ROLES if r[0] in self.role_values]

    def get_context_data(self, *args, **kwargs):
        context = super(GuestsView, self).get_context_data(*args, **kwargs)
        context['active_guests'] = self.get_queryset().filter(is_active=True)
        context['inactive_guests'] = self.get_queryset().filter(is_active=False)
        return context


class ExportMembersPdfView(GetDataMixin, AccountGetObjectMixin, SelectBoardRequiredMixin,
                           MembershipQuerysetMixin, PermissionMixin, View):
    permission = (Membership, PERMISSIONS.add)
    model = Membership

    def get_queryset(self):
        query_set = super(ExportMembersPdfView, self).get_queryset()\
            .filter(is_active=True)\
            .order_by('first_name', 'user__email')
        if self.kwargs['role'] == 'member':
            return [obj for obj in query_set if not obj.is_guest]

        elif self.kwargs['role'] == 'guest':
            return [obj for obj in query_set if obj.is_guest]

    def get(self, request, *args, **kwargs):
        account = self.get_object()
        logo = account.logo.url if account.logo else 'images/logo.png'
        members, headers = self.get_export_data()
        membership = []
        for member in members:
            membership.append(zip(headers, member))
        return self.render_to_pdf('accounts/includes/pdf.html',
                                  {'pagesize': 'A4', 'membership': membership,
                                   'logo': self.fetch_resources(logo)})

    def fetch_resources(self, uri):
        if settings.MEDIA_URL and uri.startswith(settings.MEDIA_URL):
            path = os.path.join(settings.MEDIA_ROOT,
                                uri.replace(settings.MEDIA_URL, ""))
        elif settings.STATIC_URL and uri.startswith(settings.STATIC_URL):
            path = os.path.join(settings.STATIC_ROOT,
                                uri.replace(settings.STATIC_URL, ""))
            if not os.path.exists(path):
                for d in settings.STATICFILES_DIRS:
                    path = os.path.join(d, uri.replace(settings.STATIC_URL, ""))
                    if os.path.exists(path):
                        break
        elif uri.startswith("http://") or uri.startswith("https://"):
            path = uri
        else:
            path = os.path.join(settings.STATIC_ROOT, uri)
        return path

    def render_to_pdf(self, template_src, context_dict):
        template = get_template(template_src)
        html = template.render(context_dict)
        result = StringIO.StringIO()
        pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), result)
        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=full_board_list.pdf'
            return response
        return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


class ExportMembersXlsView(GetDataMixin, SelectBoardRequiredMixin, MembershipQuerysetMixin, PermissionMixin, View):
    permission = (Membership, PERMISSIONS.add)
    model = Membership

    def get_queryset(self):
        query_set = super(ExportMembersXlsView, self).get_queryset()\
            .filter(is_active=True)\
            .order_by('first_name', 'user__email')
        if self.kwargs['role'] == 'member':
            return [obj for obj in query_set if not obj.is_guest]

        elif self.kwargs['role'] == 'guest':
            return [obj for obj in query_set if obj.is_guest]

    def get(self, request, *args, **kwargs):
        members, headers = self.get_export_data()
        config = {
            'header_style': 'background-color: #c5d7ef; font-size: 12pt;',
            'row_styles': (),
            'freeze_row': 0
        }
        mm_doc = mm.Document(members, config_dict=config, order=headers)
        return self.render_to_xls(mm_doc)

    def render_to_xls(self, xls):
        result = xls.writestr()
        response = HttpResponse(content=result)
        response['Content-Type'] = 'application/vnd.ms-excel'
        response['Content-Encoding'] = 'utf-8'
        response['Content-Disposition'] = 'attachment; filename=full_board_list.xls'
        return response


class AssistantCreateView(CurrentAccountMixin, ActiveTabMixin, MemberCreateMixin, SelectBoardRequiredMixin,
                          MembershipQuerysetMixin, PermissionMixin, CreateView):
    permission = (Membership, PERMISSIONS.add)
    form_class = AssistantAddForm
    template_name = 'accounts/add_assistant.html'
    active_tab = 'guests'
    email_dup_error = _('This email is already in use.')

    def and_permission(self, account, membership):
        member = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        return member.account == account

    def or_permission(self, account, membership):
        # regular member can add his own assistant
        return membership.can_have_assistant and int(self.kwargs['pk']) == membership.pk

    def form_invalid(self, form):
        if 'email' in form.errors and self.email_dup_error in form.errors['email']:
            if len(form.errors) == 1:
                # This email is already in use
                email = self.request.POST.get('email').strip()
                user = User.objects.get(email__iexact=email)
                account = get_current_account(self.request)
                for membership in Membership.objects.filter(user=user, account=account):
                    if membership.role != Membership.ROLES.assistant and membership.is_active:
                        break
                else:
                    # No break statement was encountered
                    # email is used by an existing assistant or inactive user
                    member = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])

                    self.object, created = Membership.objects.get_or_create(user=user, account=account)
                    self.object.is_active = True
                    self.object.role = Membership.ROLES.assistant
                    self.object.save()

                    member.assistant = self.object
                    member.save()
                    self.get_success_message()
                    return HttpResponseRedirect(self.get_success_url())
            else:
                index = next((i for i in range(len(form.errors['email']))
                              if form.errors['email'][i] == self.email_dup_error), None)
                if index is not None:
                    form.errors['email'].pop(index)
        return super(AssistantCreateView, self).form_invalid(form)

    def form_valid(self, form):
        member = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        self.form_save(form)
        self.object.role = Membership.ROLES.assistant
        self.object.save()
        member.assistant = self.object
        member.save()

        self.object.user.send_invitation_email(account=self.object.account, password=self.tmppasswd,
                                               from_member=self.request.user.get_membership(self.object.account))
        member = self.object.user.get_membership(self.object.account)
        member.invitation_status = Membership.INV_SENT
        member.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_message(self):
        messages.success(self.request, _('Assistant was added successfully.'))

    def get_success_url(self):
        return reverse('profiles:assistant_detail', kwargs={'pk': self.object.pk, 'member_pk': self.kwargs['pk']})


class MemberCreateView(CurrentAccountMixin, ActiveTabMixin, RecentActivityMixin, MemberCreateMixin, MemberNotificationMixin,
                       SelectBoardRequiredMixin, MembershipQuerysetMixin, PermissionMixin, CreateView):
    permission = (Membership, PERMISSIONS.add)
    form_class = MemberAddForm
    template_name = 'accounts/add_member.html'
    active_tab = 'members'
    email_dup_error = _('This email is already in use.')

    def post(self, request, *args, **kwargs):
        plan_max_members = get_current_account(request).plan.max_members
        acc_members_amount = get_current_account(request).memberships.filter(is_active=True)\
            .exclude(role=Membership.ROLES.assistant).count()
        if plan_max_members and acc_members_amount + 1 > plan_max_members:
            messages.error(request, _('Limit of members amount for your billing plan is exceeded, '
                                      'you can upgrade it in your profile!'))
            return HttpResponseRedirect(self.get_success_url())
        return super(MemberCreateView, self).post(request, *args, **kwargs)

    def form_invalid(self, form):
        if 'email' in form.errors and self.email_dup_error in form.errors['email']:
            if len(form.errors) == 1:
                email = self.request.POST.get('email').strip()
                user = User.objects.get(email__iexact=email)
                account = get_current_account(self.request)
                membership, created = Membership.objects.get_or_create(user=user, account=account)
                membership.committees.add(*form.cleaned_data['committees'])
                membership.is_active = True
                membership.__dict__.update(**form.cleaned_data)
                membership.save()
                self.object = membership
                self.avatar_save(form)
                self.get_success_message()
                return HttpResponseRedirect(self.get_success_url(form.cleaned_data['add_another']))
            else:
                index = next((i for i in range(len(form.errors['email']))
                              if form.errors['email'][i] == self.email_dup_error), None)
                if index is not None:
                    form.errors['email'].pop(index)
        return super(MemberCreateView, self).form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        password = User.objects.make_random_password()
        user = User.objects.create_user(email=form.cleaned_data['email'], password=password)
        self.object.user = user
        self.object.account = get_current_account(self.request)
        self.object.save()
        self.object.committees.add(*form.cleaned_data['committees'])
        self.get_success_message()
        TemporaryUserPassword.objects.create(user=user, password=password)

        user.send_invitation_email(account=self.object.account, password=password,
                                   from_member=self.request.user.get_membership(self.object.account))
        member = user.get_membership(self.object.account)
        member.invitation_status = Membership.INV_SENT
        member.save()

        return HttpResponseRedirect(self.get_success_url(form.cleaned_data['add_another']))

    def get_context_data(self, *args, **kwargs):
        context = super(MemberCreateView, self).get_context_data(*args, **kwargs)
        context['default_avatar_url'] = settings.DEFAULT_AVATAR_URL
        return context

    def get_success_message(self):
        messages.success(self.request, _('Member was added successfully.'))

    def get_success_url(self, add_another=False):
        if add_another:
            return reverse('member_create', kwargs={'url': get_current_account(self.request).url})
        else:
            return reverse('board_members', kwargs={'url': get_current_account(self.request).url})


class GuestCreateView(MemberCreateView):
    form_class = GuestAddForm
    template_name = 'accounts/add_guest.html'
    active_tab = 'guests'

    def get_context_data(self, *args, **kwargs):
        context = super(GuestCreateView, self).get_context_data(*args, **kwargs)
        context['role_choice'] = Membership.ROLES
        return context

    def get_success_message(self):
        messages.success(self.request, _('Guest was added successfully.'))

    def get_success_url(self, add_another=False):
        if add_another:
            return reverse('guest_create', kwargs={'url': get_current_account(self.request).url})
        else:
            return reverse('board_guests', kwargs={'url': get_current_account(self.request).url})


class BoardsListView(LoginRequiredMixin, ListView):
    model = Membership
    template_name = 'accounts/boards_list.html'
    context_object_name = 'memberships'

    def post(self, request, *args, **kwargs):
        if self.request.is_ajax() and 'account_id' in self.request.POST:
            account = get_object_or_404(Account, id=self.request.POST.get('account_id'))
            set_current_account(request, account)
            Membership.objects.filter(user=self.request.user, account=account).update(last_login=timezone.now())
            url = reverse('dashboard:dashboard', kwargs={'url': account.url})
            data = json.dumps({'url': url})
            kwargs['content_type'] = 'application/json'
            return HttpResponse(data, kwargs)

    def get_queryset(self):
        memberships = self.model.objects.filter(user=self.request.user, is_active=True)
        memberships.update(invitation_status=Membership.INV_INVITED)
        return memberships


class AccountSettingsView(SelectBoardRequiredMixin, AccountGetObjectMixin, PermissionMixin, DetailView):
    permission = (Account, PERMISSIONS.view)
    template_name = 'accounts/account_settings.html'


class AccountCancelView(AjaxableResponseMixin, SelectBoardRequiredMixin, PermissionMixin, View):
    permission = (Account, PERMISSIONS.edit)

    def post(self, request):
        account = get_current_account(request)
        account.is_active = False
        account.date_cancel = timezone.now()

        # cancel stripe subscription
        account._cancel_subscription()

        account.save()

        # notify admin
        request.user.admin_notification(account=account, msg_type='cancel_account')
        clear_current_account(request)
        data = {'url': reverse('accounts:boards')}
        return self.render_to_json_response(data)


class AccountLogoView(AjaxableResponseMixin, AccountGetObjectMixin, PermissionMixin, BaseUpdateView):
    permission = (Account, PERMISSIONS.edit)
    form_class = AccountLogo

    def form_valid(self, form):
        self.object = form.save()
        data = {
            'pk': self.object.pk,
            'status': 'success',
            'type': self.object.type,
            'path': self.object.logo.url,
            'html': render_to_string('documents/document_item.html',
                                     {'doc': self.object, 'user': self.request.user, 'no_file_type': True}),
        }
        return self.render_to_json_response(data)


class AccountNotifyView(AjaxableResponseMixin, AccountGetObjectMixin, PermissionMixin, BaseUpdateView):
    permission = (Account, PERMISSIONS.edit)
    form_class = AccountNotify

    def form_valid(self, form):
        self.object = form.save()
        set_current_account(self.request, self.object)
        data = {'status': 'success'}
        return self.render_to_json_response(data)


class AccountLogoRemoveView(AjaxableResponseMixin, AccountGetObjectMixin, PermissionMixin, View):
    permission = (Account, PERMISSIONS.edit)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.logo.delete()
        obj.save()
        data = {'doc_id': obj.id, 'doc_type': obj.type}
        return self.render_to_json_response(data)


class AccountReactivateView(AjaxableResponseMixin, LoginRequiredMixin, BaseFormView):
    form_class = AccountReactivateForm

    def form_invalid(self, form):
        return HttpResponseBadRequest()

    def form_valid(self, form):
        account_id = form.cleaned_data['account_id']
        account = Account.objects.get(id=account_id)
        membership = self.request.user.get_membership(account)

        if not (account.can_be_activated() and has_role_permission(membership, Account, PERMISSIONS.edit)):
            raise PermissionDenied()

        account._update_subscription()
        if account.is_trial() or account.stripe_customer_id:
            account.is_active = True
            account.date_cancel = None
            account.save()
            messages.success(self.request, _('Account was reactivated successfully.'))
        else:
            messages.error(self.request, _('There was a problem with your billing information.'))

        data = {'url': reverse('accounts:boards')}
        return self.render_to_json_response(data)
