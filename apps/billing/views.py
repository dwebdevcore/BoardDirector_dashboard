# -*- coding: utf-8 -*-
import calendar
import json
import stripe

from django.contrib import messages
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic.edit import View, UpdateView
from django.utils.translation import ugettext_lazy as _

from accounts.account_helper import get_current_account, set_current_account
from .businessrules import ChangePlan
from .forms import PlanChangeForm, BillingSettingsEditForm, BillingAddressEditForm, ChangePlanForm
from .models import BillingSettings
from accounts.forms import AccountReactivateForm
from accounts.models import Account
from billing.models import Plan
from common.mixins import LoginRequiredMixin, SelectBoardRequiredMixin, AjaxableResponseMixin
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin
from permissions.shortcuts import has_role_permission

import logging
logger = logging.getLogger(__name__)


class ChangeBillingCycleView(AjaxableResponseMixin, SelectBoardRequiredMixin, PermissionMixin, View):
    permission = (Account, PERMISSIONS.edit)

    def post(self, request):
        account = get_current_account(request)

        # update stripe subscription
        account._update_subscription()

        BillingSettings.objects.filter(account=account).update(cycle=BillingSettings.YEAR)
        messages.success(request, _('Billing cycle was changed successfully.'))
        data = {'url': reverse('board_detail', kwargs={'url': account.url})}

        return self.render_to_json_response(data)


class AccountObjectMixin(object):
    def get_object(self, queryset=None):
        # can't use PermissionMixin because there's no current_account when reactivating
        if 'account_id' in self.request.GET:
            form = AccountReactivateForm(self.request.GET)
            if form.is_valid():
                account = get_object_or_404(self.request.user.accounts.all(), id=form.cleaned_data['account_id'])
            else:
                raise PermissionDenied()
        elif get_current_account(self.request):
            account = get_current_account(self.request)
        else:
            raise PermissionDenied()  # !!! should redirect to /accounts/ in future. Fix in WEB-160.

        # handle permissions manually
        membership = self.request.user.get_membership(account=account)
        if not has_role_permission(membership, Account, PERMISSIONS.edit):
            raise PermissionDenied()
        return account


class PlanDataMixin(object):
    def get_context_data(self, **kwargs):
        context = super(PlanDataMixin, self).get_context_data(**kwargs)
        account = context.get('account')
        if account:
            current_plan = Account.objects.get(pk=account.pk).plan
            current_plan_id = current_plan and current_plan.pk or None
        else:
            current_plan_id = None
        context['plans'] = Plan.list_available_plans()
        context['current_plan_id'] = current_plan_id
        context['selectable_plan_ids'] = ChangePlan.allowed_plans(current_plan_id)
        context['show_change_plan_form'] = True
        return context


class BillingSettingsUpdateView(LoginRequiredMixin, AccountObjectMixin, PlanDataMixin, UpdateView):
    form_class = BillingSettingsEditForm
    template_name = 'billing/billing_settings.html'
    context_object_name = 'billing'

    def get_object(self, queryset=None):
        account = super(BillingSettingsUpdateView, self).get_object()
        billing = BillingSettings.objects.get(account=account)
        if not billing.country:
            billing.country = "United States of America (USA)"

        return billing

    def get_context_data(self, **kwargs):
        context = super(BillingSettingsUpdateView, self).get_context_data(**kwargs)
        context['change_plan_form'] = ChangePlanForm(initial={
            'plan': self.object.account.plan,
            'cycle': self.object.cycle,
        })
        context['account'] = context['billing'].account
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        return context

    def form_valid(self, form):
        billing = self.object = form.save(commit=False)
        assert isinstance(billing, BillingSettings)

        # save cycle
        cycle_form = ChangePlanForm(self.request.POST)
        need_save_account = False
        if cycle_form.is_valid():
            billing.cycle = cycle_form.cleaned_data['cycle']
            billing.account.plan = cycle_form.cleaned_data['plan']
            need_save_account = True

        subscription_result = None
        # card created or updated
        if form.cleaned_data['stripe_token']:
            token = json.loads(form.cleaned_data['stripe_token'])
            if not billing.account.stripe_customer_id:
                # customer does not exist
                subscription_result = billing.account._create_subscription(token)
            else:
                # stripe customer exists -- update card data
                subscription_result = billing.account._update_card(token)

        elif cycle_form.has_changed() and billing.account.stripe_customer_id:
            subscription_result = billing.account._update_subscription()

        if subscription_result:
            logger.info(subscription_result)
            if subscription_result['status'] == 'error':
                messages.error(self.request, subscription_result['msg'])

        if not billing.account.is_active or need_save_account:
            billing.account.is_active = True
            billing.account.save()

        messages.success(self.request, _('Billing Settings were changed successfully.'))
        return super(BillingSettingsUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('billing:update_settings')


class ChangePlanView(LoginRequiredMixin, AccountObjectMixin, PlanDataMixin, UpdateView):
    form_class = PlanChangeForm
    template_name = 'billing/pricing.html'
    context_object_name = 'account'

    def form_valid(self, form):
        self.object = form.save()

        # update stripe subscription
        self.object._update_subscription()

        messages.success(self.request, _('Plan was changed successfully.'))
        return super(ChangePlanView, self).form_valid(form)

    def get_success_url(self):
        return reverse('billing:change_plan')


class BillingAddressUpdateView(SelectBoardRequiredMixin, PermissionMixin, UpdateView):
    permission = (Account, PERMISSIONS.edit)
    model = BillingSettings
    form_class = BillingAddressEditForm
    template_name = 'billing/billing_address.html'
    context_object_name = 'billing'

    def get_object(self, queryset=None):
        return BillingSettings.objects.get(account=get_current_account(self.request))

    def form_valid(self, form):
        self.object = form.save()

        # update stripe customer email
        if self.object.account.stripe_customer_id:
            stripe.api_key = settings.STRIPE_SECRET_KEY

            try:
                c = stripe.Customer.retrieve(self.object.account.stripe_customer_id)
                c.email = self.object.mail
                c.save()
            except stripe.InvalidRequestError as e:
                mail_admins('Stripe API Error', e.json_body['error']['message'], fail_silently=True)

        messages.success(self.request, _('Billing details were changed successfully.'))
        return super(BillingAddressUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('billing:update_settings')
