# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.test import RequestFactory
from django.urls.resolvers import ResolverMatch
from django.utils import timezone
from django.utils import lorem_ipsum
from django.core import mail
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template import Template, RequestContext
from django.template.base import TemplateSyntaxError
from django.utils.translation import ugettext as _
from django.core.management import call_command

from accounts.account_helper import set_current_account
from accounts.models import Account

from billing.factories import BillingSettingsFactory, InvoiceFactory
from billing.models import Invoice, BillingSettings, Plan
from common.models import Feedback
from common.utils import BaseTestCase as TestCase


class ContactTest(TestCase):
    def test_contact(self):
        mail.outbox = []
        data = {
            'email': 'aaa@gmail.com',
            'message': lorem_ipsum.words(300, False)
        }
        resp = self.client.post(reverse('contactus'), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn(mail.outbox[0].subject, _('Feedback from: {}'.format(data['email'])))
        self.assertEqual(Feedback.objects.latest('id').__unicode__(), 'Feedback from {}'.format(data['email']))


class PricingTest(TestCase):
    def test_pricing(self):
        resp = self.client.get(reverse('pricing'))
        self.assertEqual(resp.status_code, 200)
        self.assertSequenceEqual(
            [p.id for p in resp.context['plans']],
            [p.id for p in Plan.list_available_plans()],
        )
        for plan in Plan.list_available_plans():
            self.assertContains(resp, plan.name_str)


class TemplateTagTest(TestCase):
    def setUp(self):
        self.create_init_data()
        self.login_member()
        request = RequestFactory().get('/{}/dashboard/'.format(self.account.url))
        request.session = {}
        set_current_account(request, self.account)
        request.user = self.user
        request.resolver_match = ResolverMatch(self.setUp, [], {}, app_names=['dashboard'])
        self.c = RequestContext(request)

    def test_acc_url_success(self):
        t = Template('{% load common_tags %}{% acc_url "dashboard:dashboard" %}')
        self.assertEqual(t.render(self.c), reverse("dashboard:dashboard", kwargs={'url': self.account.url}))

    def test_acc_url_wrong_parameter(self):
        with self.assertRaises(TemplateSyntaxError) as e:
            t = Template('{% load common_tags %}{% acc_url %}')
            t.render(self.c)
        self.assertEqual(e.exception.args[0], u"'acc_url' takes at least one argument (path to a view)")

        with self.assertRaises(NoReverseMatch) as e:
            t = Template('{% load common_tags %}{% acc_url value with "dashboard:dashboard" %}')
            t.render(self.c)
        self.assertEqual(e.exception.args[0], u"'url' requires a non-empty first argument. The syntax changed in Django 1.5, see the docs.")


class CommandsTest(TestCase):
    def setUp(self):
        self.create_init_data()
        self.billing_settings = BillingSettingsFactory(card_number='5105105105105100')

    def call_command_null(self, command):
        """Redirect stdout to null."""
        with open(os.devnull, 'w') as f:
            call_command(command, stdout=f)

    def test_check_payments_month(self):
        self.account._create_subscription()
        invoice = Invoice.objects.filter(account=self.account)[0]
        invoice.payed_period_end = timezone.now()-timezone.timedelta(days=1)
        invoice.save()
        count = Invoice.objects.count()
        self.call_command_null('check_payments')
        self.assertEqual(count + 1, Invoice.objects.count())

    def test_check_payments_year(self):
        self.billing_settings.cycle = BillingSettings.YEAR
        self.billing_settings.save()
        self.account._create_subscription()
        invoice = Invoice.objects.filter(account=self.account)[0]
        invoice.payed_period_end = timezone.now()-timezone.timedelta(days=1)
        invoice.save()
        count = Invoice.objects.count()
        self.call_command_null('check_payments')
        self.assertEqual(count + 1, Invoice.objects.count())

    def test_check_payments_wrong(self):
        count = Invoice.objects.count()
        self.account.invoice_set = []
        self.account.save()
        self.call_command_null('check_payments')
        self.assertEqual(count, Invoice.objects.count())

    def test_check_trial_notice(self):
        self.account.date_created = timezone.now()-timezone.timedelta(days=settings.TRIAL_PERIOD - 3)
        self.account.stripe_customer_id = ''
        self.account.save()
        self.call_command_null('check_trial')
        self.assertTrue(self.account.is_active)
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn(mail.outbox[0].subject, _('BoardDirector - Trial period for {} is coming to the end').format(self.account.name))

    def test_check_trial_finish(self):
        self.account.date_created = timezone.now()-timezone.timedelta(days=50)
        self.account.stripe_customer_id = ''
        self.account.is_active = True
        self.account.billing_settings.delete()
        self.account.save()
        self.billing_settings = BillingSettingsFactory(card_number='', account=self.account)
        self.call_command_null('check_trial')
        self.account = Account.objects.get(pk=self.account.pk)
        self.assertFalse(self.account.is_active)
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn(mail.outbox[0].subject, _('BoardDirector - Trial period for {} Account has expired').format(self.account.name))

    def test_check_trial_paid_is_over(self):
        self.account.date_created = timezone.now()-timezone.timedelta(days=50)
        self.account.is_active = True
        self.account.stripe_customer_id = ''
        self.account.save()
        self.invoice = InvoiceFactory(account=self.account, payed_period_end=timezone.now()-timezone.timedelta(days=50))
        self.call_command_null('check_trial')
        self.account = Account.objects.get(pk=self.account.pk)
        self.assertTrue(self.account.is_active)
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn(mail.outbox[0].subject, _('BoardDirector - Paid period for {} Account has expired').format(self.account.name))
