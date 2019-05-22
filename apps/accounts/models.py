# -*- coding: utf-8 -*-
import os
import stripe
import time

from dateutil.relativedelta import relativedelta
from datetime import datetime

from django.db import models
from django.conf import settings
from django.core.mail import mail_admins
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.utils import timezone

from billing.models import BillingSettings, Invoice
from documents.models import file_storage

import logging
logger = logging.getLogger(__name__)


class Account(models.Model):
    name = models.CharField(_('name'), max_length=255)
    url = models.SlugField(_('url'), max_length=255, unique=True)
    plan = models.ForeignKey('billing.Plan', verbose_name=_('plan'), null=True)
    total_storage = models.BigIntegerField(_('total storage'), default=0)
    date_created = models.DateTimeField(_('date created'), auto_now_add=True)
    is_active = models.BooleanField(_('active'), default=True)
    date_cancel = models.DateTimeField(_('cancellation date'), null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    unlimited_trial = models.BooleanField(_('unlimited trial'), default=False)
    logo = models.ImageField(_('logotype'), upload_to='logotypes/%Y%m%d', storage=file_storage, null=True, blank=True)
    send_notification = models.BooleanField(_('send automatic email notifications'), default=True)
    view_email = models.BooleanField(_('view email'), default=True)
    show_guide = models.BooleanField(_('getting started'), default=True)
    date_trial_ends = models.DateTimeField(_('trial end date'), blank=True, null=True,
                                           help_text='if this date is not set, then trial period ends %s days after account creation date' % settings.TRIAL_PERIOD)
    default_meetings_location = models.CharField(max_length=255, blank=True, null=True)

    @property
    def last_invoice_created(self):
        if not self.invoices.all().count():
            return self.date_created
        return self.invoices.all().latest('created_at').created_at

    @property
    def total_storage_size(self):
        bytes = float(self.total_storage)
        if bytes >= 1099511627776:
            terabytes = bytes / 1099511627776
            total_storage = '{:.2f} Tb'.format(terabytes)
        elif bytes >= 1073741824:
            gigabytes = bytes / 1073741824
            total_storage = '{:.2f} Gb'.format(gigabytes)
        elif bytes >= 1048576:
            megabytes = bytes / 1048576
            total_storage = '{:.2f} Mb'.format(megabytes)
        elif bytes >= 1024:
            kilobytes = bytes / 1024
            total_storage = '{:.2f} Kb'.format(kilobytes)
        else:
            total_storage = '{:.2f} b'.format(bytes)
        return total_storage

    def get_next_billing_date(self):
        if not self.invoices.all().count():
            if self.billing_settings.cycle == self.billing_settings.MONTH:
                return timezone.now() + relativedelta(months=+1)
            elif self.billing_settings.cycle == self.billing_settings.YEAR:
                return timezone.now() + relativedelta(years=+1)
        return self.invoices.all().latest().payed_period_end

    def get_next_pay_date(self):
        if not self.invoices.all().count():
            if self.billing_settings.cycle == self.billing_settings.MONTH:
                return timezone.now() + relativedelta(months=+1)
            elif self.billing_settings.cycle == self.billing_settings.YEAR:
                return timezone.now() + relativedelta(years=+1)
        return self.invoices.all().latest().payed_period_end

    def next_subscr_up_to(self):
        if self.billing_settings.cycle == self.billing_settings.MONTH:
            return self.get_next_pay_date() + relativedelta(months=+1)
        elif self.billing_settings.cycle == self.billing_settings.YEAR:
            return self.get_next_pay_date() + relativedelta(years=+1)

    def get_next_pay_charge(self):
        if self.billing_settings.cycle == self.billing_settings.MONTH:
            return self.plan.month_price
        elif self.billing_settings.cycle == self.billing_settings.YEAR:
            return self.plan.year_price

    def get_last_numbers_card(self):
        return 'XXXX-XXXX-XXXX-{}'.format(self.billing_settings.card_number[12:16])

    def has_card_number(self):
        return bool(self.billing_settings.card_number)

    def get_max_storage(self):
        return self.plan.max_storage_size

    def get_max_members(self):
        return self.plan.max_members_str

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('board_detail', kwargs={'url': self.url})

    def can_be_activated(self):
        return self.date_cancel is None or self.date_cancel + timezone.timedelta(days=30) >= timezone.now()

    def trial_till_date(self):

        if self.date_trial_ends:
            return self.date_trial_ends

        return self.date_created + timezone.timedelta(days=settings.TRIAL_PERIOD)

    def is_trial(self):
        return self.unlimited_trial or self.trial_till_date() >= timezone.now()

    def trial_days_left(self):

        if self.unlimited_trial:
            return 999

        now = timezone.now()
        if self.date_trial_ends:
            return (self.date_trial_ends - now).days

        return settings.TRIAL_PERIOD - (now - self.date_created).days

    def get_admin_memberships(self):
        from profiles.models import Membership

        return self.memberships.filter(is_admin=True,
                                       is_active=True,
                                       invitation_status=Membership.INV_INVITED)

    def _create_subscription(self, elements_token=None):
        data = {}
        stripe_plan = self.plan.stripe_month_plan_id
        plan_fee = self.plan.month_price
        if self.billing_settings.cycle == BillingSettings.YEAR:
            stripe_plan = self.plan.stripe_year_plan_id
            plan_fee = self.plan.year_price

        stripe.api_key = settings.STRIPE_SECRET_KEY

        old_stripe_customer_id = self.stripe_customer_id

        try:
            # create card token
            if elements_token is None:
                # old-style with saved credentials, should be removed
                token_response = stripe.Token.create(
                    card={
                        'number': self.billing_settings.card_number,
                        'exp_month': self.billing_settings.expiration_month,
                        'exp_year': self.billing_settings.expiration_year,
                        'cvc': self.billing_settings.cvv,
                    },
                )
            else:
                token_response = elements_token
                self.billing_settings.last4 = token_response['card']['last4']
                self.billing_settings.expiration_month = token_response['card']['exp_month']
                self.billing_settings.expiration_year = token_response['card']['exp_year']
                self.billing_settings.card_type = token_response['card']['type']
                self.billing_settings.save()

            # create stripe subscription
            parameters = {
                'description': self.name,
                'email': self.billing_settings.mail,
                'card': token_response['id'],
                'plan': stripe_plan,
            }

            if self.is_trial():
                # So that user will be first charged at this date.
                parameters['trial_end'] = int(time.mktime(self.trial_till_date().timetuple()))

            if self.billing_settings.discount:
                parameters['coupon'] = self.billing_settings.discount

            customer = stripe.Customer.create(**parameters)
            self.stripe_customer_id = customer.id
            self.save()

            logger.info("new stripe customer created id=%s, parameters=%s",
                        customer.id, parameters)

            # create invoice
            timestamp_period_end = datetime.fromtimestamp(int(customer.subscription.current_period_end))
            period_end = timestamp_period_end.replace(tzinfo=timezone.utc)
            Invoice.objects.create(payment=plan_fee, status=Invoice.PAID, account=self, payed_period_end=period_end)
            data = {
                'status': 'success',
                'account': self
            }

            # delete subscriptions old credit cards, if it was
            if old_stripe_customer_id:
                try:
                    c = stripe.Customer.retrieve(old_stripe_customer_id)
                    c.cancel_subscription()
                    logger.info('old subscription canceled for stripe customer %s',
                                old_stripe_customer_id)
                except Exception as e:
                    # Just in case it doesn't fall in items below:
                    mail_admins('Stripe API Error',
                                'Problem with cancelling subscription for customer %s' %
                                (old_stripe_customer_id,),
                                fail_silently=True)
                    raise e

        except stripe.StripeError as e:
            data = {'status': 'error', 'msg': e.json_body['error']['message']}
            mail_admins('Stripe Error', e.json_body['error']['message'], fail_silently=True)

        return data

    def _update_card(self, token=None):

        if not self.stripe_customer_id:
            return {'status': 'error', 'msg': 'No subscription to update.'}

        if 'card' not in token or 'id' not in token:
            return {'status': 'error', 'msg': 'Invalid token.'}

        try:

            # update stripe
            c = stripe.Customer.retrieve(self.stripe_customer_id)
            c.source = token.get('id')
            c.save()

            # update local billing settings
            card = token.get('card', {})
            self.billing_settings.last4 = card.get('last4')
            self.billing_settings.expiration_month = card.get('exp_month')
            self.billing_settings.expiration_year = card.get('exp_year')
            self.billing_settings.card_type = card.get('type')
            self.billing_settings.save()

            logger.info("card updated: customer=%s, token=%s card=%s",
                        self.stripe_customer_id, token.get('id'), card)

            return {'status': 'success', 'msg': 'source card updated'}

        except stripe.error.StripeError as e:
            return {'status': 'error', 'msg': e.json_body['error']['message']}

        except Exception as e:
            return {'status': 'error', 'msg': str(e)}

    def _update_subscription(self):
        stripe_plan = self.plan.stripe_month_plan_id
        if self.billing_settings.cycle == BillingSettings.YEAR:
            stripe_plan = self.plan.stripe_year_plan_id

        stripe.api_key = settings.STRIPE_SECRET_KEY

        if self.stripe_customer_id:
            try:
                c = stripe.Customer.retrieve(self.stripe_customer_id)
                c.update_subscription(plan=stripe_plan, prorate=True)
                logger.info("subscription updated: customer=%s, plan=%s",
                            self.stripe_customer_id, stripe_plan)
                return {'status': 'success'}
            except stripe.InvalidRequestError as e:
                mail_admins('Stripe Invalid Request Error',
                            e.json_body['error']['message'], fail_silently=True)
                self.stripe_customer_id = ''
                self.save()

                return {'status': 'error', 'msg': e.json_body['error']['message']}
        else:
            return {'status': 'error', 'msg': 'No subscription to update.'}

    def _cancel_subscription(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        if self.stripe_customer_id:
            try:
                c = stripe.Customer.retrieve(self.stripe_customer_id)
                c.cancel_subscription()
            except stripe.InvalidRequestError as e:
                mail_admins('Stripe Invalid Request Error',
                            e.json_body['error']['message'], fail_silently=True)

    def extension(self):
        name, extension = os.path.splitext(self.logo.name)
        ext = extension[1:]
        if ext == 'png':
            return ext
        elif ext in ['jpg', 'jpeg']:
            return 'jpeg'
        else:
            return 'gif'

    @property
    def type(self):
        return 'logo'

    def clean(self):
        self.send_notification = not self.send_notification
