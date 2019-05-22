# -*- coding: utf-8 -*-
import calendar
import stripe

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _

from .models import BillingSettings, Plan
from .factories import BillingSettingsFactory, InvoiceFactory
from accounts.models import Account
from common.utils import BaseTestCase as TestCase


class BillingTest(TestCase):

    def setUp(self):
        self.create_init_data()
        self.login_admin()
        self.billingsettings = BillingSettingsFactory(card_number='5105105105105100')
        self.invoice = InvoiceFactory()
        mail.outbox = []

    def test_change_billing_cycle(self):
        url = reverse('billing:change_cycle')
        response = self.client.post(url)
        updated_billing_settings = BillingSettings.objects.get(id=self.billingsettings.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_billing_settings.cycle, BillingSettings.YEAR)

    def test_change_plan(self):
        url = reverse('billing:change_plan')
        data = {'plan': Plan.PREMIER}
        response = self.client.post(url, data, follow=True)
        updated_account = Account.objects.get(id=self.account.id)
        self.assertContains(response, updated_account.plan.max_storage_size)
        self.assertContains(response, _('Plan was changed successfully.'))
        self.assertEqual(updated_account.plan.name, Plan.PREMIER)
        # Starter Plan
        data = {'plan': Plan.STARTER}
        response = self.client.post(url, data, follow=True)
        updated_account = Account.objects.get(id=self.account.id)
        self.assertContains(response, updated_account.plan.max_storage_size)
        self.assertContains(response, _('Plan was changed successfully.'))
        self.assertEqual(updated_account.plan.name, Plan.STARTER)

    def test_billing_settings_update_forbidden(self):
        # wrong account id
        url = '{}?account_id=test'.format(reverse('billing:update_settings'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # user is not admin
        self.client.logout()
        self.login_member()
        url = '{}?account_id={}'.format(reverse('billing:update_settings'), self.account.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # not auth user
        self.client.logout()
        url = reverse('billing:update_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, 200)

    def test_billing_settings_update(self):
        url = reverse('billing:update_settings')
        data = {
            'cvv': '123',
            'cycle': BillingSettings.MONTH,
            'creditcardnumber': '5555-5555-5555-4444',
            'monthpicker': ''
        }
        # empty monthpicker
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, _('This field is required.'))

        # Invalid monthpicker format
        data['monthpicker'] = 'Jun 2065'
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, _('Invalid format.'))

        # create subscription
        data['monthpicker'] = '{:%B %Y}'.format(timezone.now() + timezone.timedelta(days=365))
        self.account.date_created = timezone.now() - timezone.timedelta(days=35)
        self.account.save()

        response = self.client.post(url, data, follow=True)
        updated_billing_settings = BillingSettings.objects.get(id=self.billingsettings.id)
        self.billingsettings = updated_billing_settings
        self.account = updated_billing_settings.account

        # check stripe customer email
        if updated_billing_settings.account.stripe_customer_id:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            c = stripe.Customer.retrieve(self.account.stripe_customer_id)
            self.assertEqual(c.email, updated_billing_settings.mail)
        self.assertContains(response, _('Billing Settings were changed successfully.'))

        # update cycle of subscription
        url = reverse('billing:update_settings')
        data = {
            'cvv': self.billingsettings.cvv,
            'cycle': BillingSettings.YEAR,
            'creditcardnumber': '5555-5555-5555-4444',
            'monthpicker': '{} {}'.format(calendar.month_name[self.billingsettings.expiration_month],
                                          self.billingsettings.expiration_year)
        }
        response = self.client.post(url, data, follow=True)
        updated_billing_settings = BillingSettings.objects.get(id=self.billingsettings.id)
        self.billingsettings = updated_billing_settings
        self.account = updated_billing_settings.account
        if self.account.stripe_customer_id:
            c = stripe.Customer.retrieve(self.account.stripe_customer_id)
            self.assertEqual(c.subscription.plan.interval, 'year')
        self.assertContains(response, _('Billing Settings were changed successfully.'))

        # reactivate account
        self.account.is_active = False
        self.account.save()
        url = reverse('billing:update_settings')
        response = self.client.post(url, data, follow=True)
        updated_account = Account.objects.get(id=self.account.id)
        self.assertContains(response, _('Billing Settings were changed successfully.'))
        self.assertTrue(updated_account.is_active)

        # update email
        url = reverse('billing:update_address')
        new_email = 'new_email@example.com'
        data = {
            'mail': new_email,
            'name': updated_account.name
        }
        response = self.client.post(url, data, follow=True)
        updated_billing_settings = BillingSettings.objects.get(id=self.billingsettings.id)
        if updated_billing_settings.account.stripe_customer_id:
            c = stripe.Customer.retrieve(updated_billing_settings.account.stripe_customer_id)
            self.assertEqual(c.email, new_email)
        self.assertEqual(response.status_code, 200)

    def test_coupon_add(self):
        account = self.account
        account.date_created = timezone.now() - timezone.timedelta(days=50)
        account.save()
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            coupon1 = stripe.Coupon.retrieve('coupon_number_repeat')
            coupon1.delete()
        except stripe.InvalidRequestError:
            pass
        coupon1 = stripe.Coupon.create(
            percent_off=25,
            duration='repeating',
            duration_in_months=3,
            id='coupon_number_repeat'
        )
        url = reverse('billing:update_settings')
        data = {
            'cvv': '123',
            'cycle': BillingSettings.MONTH,
            'creditcardnumber': '5555-5555-5555-4444',
            'monthpicker': '{} {}'.format(calendar.month_name[self.billingsettings.expiration_month],
                                          self.billingsettings.expiration_year),
            'discount': 'coupon_number'
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('No such coupon'))
        data['discount'] = 'coupon_number_repeat'
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, _('Billing Settings were changed successfully.'))
        updated_billing_settings = BillingSettings.objects.get(id=self.billingsettings.id)
        account = updated_billing_settings.account
        c = stripe.Customer.retrieve(account.stripe_customer_id)
        self.assertEqual(c.discount.coupon.id, data['discount'])
        coupon1.delete()

    def test_coupon_add_once(self):
        account = self.account
        account.date_created = timezone.now() - timezone.timedelta(days=50)
        account.save()
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            coupon2 = stripe.Coupon.retrieve('once')
            coupon2.delete()
        except stripe.InvalidRequestError:
            pass
        coupon2 = stripe.Coupon.create(
            amount_off=25,
            currency='usd',
            duration='once',
            id='once',
        )
        url = reverse('billing:update_settings')
        data = {
            'cvv': '123',
            'cycle': BillingSettings.MONTH,
            'creditcardnumber': '5555-5555-5555-4444',
            'monthpicker': '{} {}'.format(calendar.month_name[self.billingsettings.expiration_month],
                                          self.billingsettings.expiration_year),
            'discount': 'once'
        }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, _('Billing Settings were changed successfully.'))
        updated_billing_settings = BillingSettings.objects.get(id=self.billingsettings.id)
        account = updated_billing_settings.account
        c = stripe.Invoice.all(customer=account.stripe_customer_id)['data'][0]
        self.assertEqual(c.discount.coupon.amount_off, coupon2.amount_off)
        coupon2.delete()

    def test_card_update_error(self):
        url = reverse('billing:update_settings')
        data = {
            'cvv': '123',
            'creditcardnumber': '4000-0000-0000-0069',
            'monthpicker': '{:%B %Y}'.format(timezone.now() + timezone.timedelta(days=365))
        }
        self.account.date_created = timezone.now() - timezone.timedelta(days=35)
        self.account.save()
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your card has expired.')

    def test_billing_address_update(self):
        url = reverse('billing:update_address')
        data = {
            'address': 'One Bowling Green, 3rd Floor',
            'city': 'New York',
            'state': 'NY',
            'zip': '10004',
            'country': 'USA',
            'mail': 'new_email@example.com',
            'name': 'Test billing'
        }
        response = self.client.post(url, data, follow=True)
        updated_billing_settings = BillingSettings.objects.get(id=self.billingsettings.id)
        self.assertContains(response, updated_billing_settings.get_full_address())

    def test_invalid_request_error_stripe(self):
        self.account.stripe_customer_id = 'invalid'
        self.account.save()
        url = reverse('billing:update_address')
        data = {
            'mail': 'new_email@example.com',
            'name': self.account.name
        }
        self.client.post(url, data, follow=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Django] Stripe API Error')
