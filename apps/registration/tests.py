# -*- coding: utf-8 -*-
import datetime

from django.contrib.sites.models import Site
from django.utils import lorem_ipsum
from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from hashlib import sha1 as sha_constructor
from django.utils.translation import ugettext as _
from django.conf import settings

from accounts.factories import AccountFactory
from accounts.models import Account
from billing.models import BillingSettings, Plan
from common.utils import BaseTestCase as TestCase
from profiles.models import User, Membership
from registration.models import RegistrationProfile


USER_DATA = {
    'email': '{}@gmail.ru'.format(lorem_ipsum.words(1, False)),
    'password1': lorem_ipsum.words(1, False),
    'name': lorem_ipsum.words(2, False)[:255],
    'url': lorem_ipsum.words(1, False)[:255]
}


class RegistrationFormTest(TestCase):

    def setUp(self):
        self.create_init_data()

    def test_existing_url(self):
        data = {'url': self.account.url}
        response = self.client.post(reverse('registration_register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('This url is already in use. Please supply a different url.'), 1)
        self.assertContains(response, _('This field is required.'), 3)
        self.assertContains(response, _('Password not entered'), 1)

    def test_existing_email_with_wrong_data(self):
        data = USER_DATA.copy()
        data.update({
            'email': self.admin.email,
            'name': ''
        })
        response = self.client.post(reverse('registration_register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(_("This email address is already in use. Please supply a different email address."),
                         response.context['form'].errors['email'])
        self.assertContains(response, _('This field is required.'), 1)

    def test_existing_email(self):
        data = USER_DATA.copy()
        data['email'] = self.admin.email
        response = self.client.post(reverse('registration_register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_("This email address is already in use. Please supply a different email address."),
                         response.context['form'].errors['email'][1])
        self.assertEqual(_("Please enter a correct email address and password. Note that both fields may be case-sensitive."),
                         response.context['form'].errors['email'][0])


class RegistrationTest(TestCase):
    def setUp(self):
        self.create_init_data()
        mail.outbox = []

    def test_registration_valid(self):
        response = self.client.post(reverse('registration_register'), USER_DATA)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Account.objects.all().order_by('-pk')[0].url, USER_DATA['url'])
        self.assertEqual(BillingSettings.objects.all().order_by('-pk')[0].mail, USER_DATA['email'])
        self.assertEqual(User.objects.all().order_by('-pk')[0].email, USER_DATA['email'])
        self.assertEqual(Membership.objects.all().order_by('-pk')[0].account.url, USER_DATA['url'])
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn(mail.outbox[0].subject, _('Activation account on: {}'.format(Site.objects.get_current())))

    def test_registration_with_not_existing_plan(self):
        response = self.client.post(reverse('registration_register') + '?plan=25', USER_DATA)
        account = Account.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(account.plan.name, Plan.DEFAULT_PLAN)
        self.assertEqual(account.url, USER_DATA['url'])
        self.assertEqual(BillingSettings.objects.all().order_by('-pk')[0].mail, USER_DATA['email'])
        self.assertEqual(Membership.objects.all().order_by('-pk')[0].account.url, USER_DATA['url'])
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn(mail.outbox[0].subject, _('Activation account on: {}'.format(Site.objects.get_current())))

    def test_add_boards(self):
        data = USER_DATA.copy()
        data['email'] = self.admin.email
        data['password1'] = 'admin'
        response = self.client.post(reverse('registration_register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Account.objects.all().order_by('-pk')[0].url, data['url'])
        self.assertEqual(BillingSettings.objects.all().order_by('-pk')[0].mail, data['email'])
        self.assertEqual(Membership.objects.all().order_by('-pk')[0].account.url, data['url'])
        self.assertEquals(len(mail.outbox), 0)
        self.assertEqual(Membership.objects.filter(user=self.admin).count(), 2)

    def test_add_boards_with_not_existing_plan(self):
        data = USER_DATA.copy()
        data.update({
            'email': self.admin.email,
            'password1': 'admin'
        })
        response = self.client.post(reverse('registration_register') + '?plan=25', data)
        account = Account.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(account.plan.name, Plan.DEFAULT_PLAN)
        self.assertEqual(account.url, data['url'])
        self.assertEqual(BillingSettings.objects.all().order_by('-pk')[0].mail, data['email'])
        self.assertEqual(Membership.objects.all().order_by('-pk')[0].account.url, data['url'])
        self.assertEquals(len(mail.outbox), 0)
        self.assertEqual(Membership.objects.filter(user=self.admin).count(), 2)

    def test_registration_no_sites(self):
        Site._meta.installed = False
        resp = self.client.post(reverse('registration_register'), USER_DATA)
        self.assertEqual(302, resp.status_code)
        new_user = User.objects.get(email__iexact=USER_DATA['email'])
        self.failIf(new_user.is_active)
        self.assertEqual(RegistrationProfile.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        Site._meta.installed = True


class ActivationTest(TestCase):

    def test_activation(self):
        self.client.post(reverse('registration_register'), USER_DATA)
        profile = RegistrationProfile.objects.get(user__email=USER_DATA['email'])
        resp = self.client.get(reverse('registration_activate',
                                       kwargs={'activation_key': profile.activation_key}))
        self.assertRedirects(resp, reverse('registration_activation_complete'))

    def test_activation_expired(self):
        self.client.post(reverse('registration_register'), USER_DATA)
        profile = RegistrationProfile.objects.get(user__email=USER_DATA['email'])
        user = profile.user
        user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        user.save()

        resp = self.client.get(reverse('registration_activate', kwargs={'activation_key': profile.activation_key}))
        self.assertEqual(200, resp.status_code)
        self.assertContains(resp, _('Account activation is failed'))


class RegistrationModelTest(TestCase):

    def setUp(self):
        self.data = {
            'email': '{}@gmail.ru'.format(lorem_ipsum.words(1, False)),
            'password': lorem_ipsum.words(1, False),
            'account': AccountFactory()
        }

    def test_valid_activation(self):
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.data)
        profile = RegistrationProfile.objects.get(user=new_user)
        activated = RegistrationProfile.objects.activate_user(profile.activation_key)

        self.failUnless(isinstance(activated, User))
        self.assertEqual(activated.id, new_user.id)
        self.failUnless(activated.is_active)

        profile = RegistrationProfile.objects.get(user=new_user)
        self.assertEqual(profile.activation_key, RegistrationProfile.ACTIVATED)

    def test_expired_activation(self):
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.data)
        new_user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        new_user.save()

        profile = RegistrationProfile.objects.get(user=new_user)
        activated = RegistrationProfile.objects.activate_user(profile.activation_key)

        self.failIf(isinstance(activated, User))
        self.failIf(activated)

        new_user = User.objects.get(email__iexact=self.data['email'])
        self.failIf(new_user.is_active)

        profile = RegistrationProfile.objects.get(user=new_user)
        self.assertNotEqual(profile.activation_key, RegistrationProfile.ACTIVATED)

    def test_activation_invalid_key(self):
        self.failIf(RegistrationProfile.objects.activate_user('foo'))

    def test_activation_already_activated(self):
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.data)
        profile = RegistrationProfile.objects.get(user=new_user)
        RegistrationProfile.objects.activate_user(profile.activation_key)

        profile = RegistrationProfile.objects.get(user=new_user)
        self.failIf(RegistrationProfile.objects.activate_user(profile.activation_key))

    def test_activation_nonexistent_key(self):
        invalid_key = sha_constructor('foo').hexdigest()
        self.failIf(RegistrationProfile.objects.activate_user(invalid_key))

    def test_management_command(self):
        expired_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(), **self.data)
        expired_user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        expired_user.save()

        call_command('cleanupregistration')
        self.assertEqual(RegistrationProfile.objects.count(), 0)
        self.assertRaises(User.DoesNotExist, User.objects.get, email=USER_DATA['email'])
