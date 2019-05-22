# -*- coding: utf-8 -*-
import os

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core import mail
from django.core.files import File

from django.core.urlresolvers import reverse
from django.utils import lorem_ipsum
from django.db.models import F
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from accounts.account_helper import get_current_account
from .models import Account
from accounts.factories import AccountFactory
from committees.factories import CommitteeFactory
from common.utils import BaseTestCase as TestCase, us_timezones
from billing.factories import InvoiceFactory, BillingSettingsFactory
from billing.models import Plan
from profiles.models import User, Membership
from profiles.factories import AdminFactory, UserFactory, ChairpersonFactory


class AccountTest(TestCase):

    def setUp(self):
        self.create_init_data()
        self.billingsettings = BillingSettingsFactory(account=self.account, card_number='5105105105105100')

    def assertEqualDate(self, dt1, dt2):
        self.assertEqual(dt1.date(), dt2.date())

    def test_get_next_pay_date(self):
        self.assertEqualDate(self.account.last_invoice_created + relativedelta(months=+1), self.account.get_next_pay_date())
        self.billingsettings.cycle = self.billingsettings.YEAR
        self.billingsettings.save()
        self.assertEqualDate(self.account.last_invoice_created + relativedelta(years=+1), self.account.get_next_pay_date())
        self.invoice = InvoiceFactory(account=self.account)
        self.assertEqualDate(self.account.invoices.all().latest().payed_period_end, self.account.get_next_pay_date())
        self.assertEqualDate(self.invoice.created_at, self.account.last_invoice_created)

    def test_next_subscr_up_to(self):
        self.assertEqualDate(self.account.get_next_pay_date() + relativedelta(months=+1), self.account.next_subscr_up_to())
        self.billingsettings.cycle = self.billingsettings.YEAR
        self.billingsettings.save()
        self.assertEqualDate(self.account.get_next_pay_date() + relativedelta(years=+1), self.account.next_subscr_up_to())

    def test_check_trial(self):
        self.assertTrue(self.account.is_trial())
        self.account.date_created = self.account.date_created - relativedelta(days=+31)
        self.account.save()
        self.assertFalse(self.account.is_trial())

    def test_get_last_numbers_card(self):
        self.assertEqual(self.account.get_last_numbers_card(), 'XXXX-XXXX-XXXX-{}'.format(self.billingsettings.card_number[12:16]))

    def test_account_settings_view(self):
        resp = self.client.get(reverse('board_detail', kwargs={'url': self.account.url}))
        self.assertEqual(resp.status_code, 302, 200)
        self.login_admin()
        url = reverse('board_detail', kwargs={'url': self.account.url})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.login_member()
        url = reverse('board_detail', kwargs={'url': self.account.url})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)
        self.login_admin()
        url = reverse('board_detail', kwargs={'url': self.account.url})
        resp = self.client.get(url)
        self.assertContains(resp, 'Board Settings')

    def test_current_plan(self):
        self.login_admin()
        self.account.plan = Plan.objects.get(name=Plan.PREMIER)
        self.account.save()
        resp = self.client.get(reverse('board_detail', kwargs={'url': self.account.url}))
        self.assertContains(resp, '{} package with up to {} users and {} GB storage'.format(self.account.plan.get_name_display(),
                                                                                            unicode(self.account.get_max_members()),
                                                                                            unicode(self.account.get_max_storage())))
        self.assertContains(resp, 'Your next charge is ${} on'.format(self.account.get_next_pay_charge()))
        self.assertContains(resp, 'Your credit card on file is {}'.format(self.account.get_last_numbers_card()))
        self.assertContains(resp, 'Each time you are billed, an invoice is emailed to <strong>{}</strong>'.format(self.account.billing_settings.mail))
        self.billingsettings.cycle = self.billingsettings.YEAR
        self.billingsettings.save()
        resp = self.client.get(reverse('board_detail', kwargs={'url': self.account.url}))
        self.assertContains(resp, 'Your next charge is ${} on'.format(self.account.get_next_pay_charge()))

    def test_cancel_reactivate_account(self):
        self.login_admin()
        current_account = get_current_account(self)
        url = reverse('accounts:cancel')
        resp = self.ajax(url)
        self.assertEqual(resp.status_code, 200)
        canceled_account = Account.objects.get(id=current_account.id)
        self.assertFalse(canceled_account.is_active)
        self.assertTrue(canceled_account.can_be_activated())
        # reactivate
        url = reverse('accounts:reactivate')
        data = {
            'account_id': canceled_account.id
        }
        resp = self.ajax(url, data)
        self.assertEqual(resp.status_code, 200)
        reactivated_account = Account.objects.get(id=canceled_account.id)
        self.assertTrue(reactivated_account.is_active)

    def test_reactivate_invalid_account(self):
        self.login_admin()
        # reactivate
        url = reverse('accounts:reactivate')
        data = {
            'account_id': 'text'
        }
        resp = self.ajax(url, data)
        self.assertEqual(resp.status_code, 400)

    def test_forbidden_cancel_account_by_member(self):
        self.login_member()
        url = reverse('accounts:cancel')
        resp = self.ajax(url)
        self.assertEqual(resp.status_code, 403)

    def test_forbidden_reactivation_account_by_member(self):
        self.login_admin()
        current_account = get_current_account(self)
        url = reverse('accounts:cancel')
        resp = self.ajax(url)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()
        self.login_member()
        # reactivate
        url = reverse('accounts:reactivate')
        data = {
            'account_id': current_account.id
        }
        resp = self.ajax(url, data)
        self.assertEqual(resp.status_code, 403)

    def test_account_cant_be_reactivated(self):
        self.login_admin()
        current_account = get_current_account(self)
        url = reverse('accounts:cancel')
        resp = self.ajax(url)
        self.assertEqual(resp.status_code, 200)
        Account.objects.filter(id=current_account.id).update(date_cancel=F('date_cancel') - timezone.timedelta(days=50))
        updated_account = Account.objects.get(id=current_account.id)
        self.assertFalse(updated_account.can_be_activated())

    def test_add_logo(self):
        logo_path = os.path.join('logotypes', timezone.now().strftime('%Y%m%d'))
        logo_full_path = os.path.join(settings.MEDIA_ROOT, logo_path)
        if os.path.exists(logo_full_path):
            for f in os.listdir(logo_full_path):
                if f.startswith("default_avatar_"):
                    os.remove(os.path.join(logo_full_path, f))
        url = reverse('accounts:logo')
        path = os.path.join(settings.STATIC_ROOT, settings.DEFAULT_AVATAR)
        img_path = os.path.join(logo_path, 'default_avatar_1.png')
        self.login_member()
        resp = self.ajax(url)
        self.assertEqual(resp.status_code, 403)
        self.login_admin()
        resp = self.ajax(url, {'logo': File(open(path))})
        account = Account.objects.get(id=self.account.id)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(account.logo.name in img_path)
        resp = self.client.get(reverse('accounts:boards'))
        self.assertContains(resp, img_path)
        os.remove(account.logo.path)

    def test_change_logo(self):
        logo_path = os.path.join('logotypes', timezone.now().strftime('%Y%m%d'))
        logo_full_path = os.path.join(settings.MEDIA_ROOT, logo_path)
        if os.path.exists(logo_full_path):
            for f in os.listdir(logo_full_path):
                if f.startswith("default_avatar_"):
                    os.remove(os.path.join(logo_full_path, f))
        url = reverse('accounts:logo')
        path = os.path.join(settings.STATIC_ROOT, settings.DEFAULT_LIST_AVATAR)
        img_path = os.path.join(logo_path, 'default_list_avatar.png')
        self.account.logo = File(open(os.path.join(settings.STATIC_ROOT, settings.DEFAULT_AVATAR)))
        self.account.save()
        self.login_admin()
        resp = self.ajax(url, {'logo': File(open(path))})
        account = Account.objects.get(id=self.account.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(account.logo.name, os.path.join('logotypes', timezone.now().strftime('%Y%m%d'), 'default_list_avatar.png'))
        resp = self.client.get(reverse('accounts:boards'))
        self.assertContains(resp, img_path)
        os.remove(account.logo.path)

    def test_remove_logo(self):
        url = reverse('accounts:remove-logo')
        self.account.logo = File(open(os.path.join(settings.STATIC_ROOT, settings.DEFAULT_AVATAR)))
        self.account.save()
        self.login_admin()
        resp = self.ajax(url)
        account = Account.objects.get(id=self.account.id)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(account.logo.name)
        resp = self.client.get(reverse('accounts:boards'))
        self.assertNotContains(resp, 'logo-img')


class MembersListTest(TestCase):

    def setUp(self):
        pass

    def test_leader(self):
        self.create_init_data()
        self.login_admin()
        resp = self.client.get(reverse('board_members', kwargs={'url': self.account.url}))
        self.assertContains(resp, 'Members')
        self.assertContains(resp, 'data-chairman="true"')
        self.assertContains(resp, 'data-chairman="true"', self.account.committees.filter(
            account=self.account).values('chairman').distinct().count())

    def test_members_count(self):
        self.account = AccountFactory()
        self.admin = AdminFactory(accounts=[self.account])
        self.login_admin()
        resp = self.client.get(reverse('board_members', kwargs={'url': self.account.url}))
        self.assertContains(resp, 'class="member"', 1)
        UserFactory.create_batch(5, accounts=[self.account])
        resp = self.client.get(reverse('board_members', kwargs={'url': self.account.url}))
        self.assertContains(resp, 'class="member"', 6)
        self.account = AccountFactory()
        self.user = UserFactory(accounts=[self.account])
        resp = self.client.get(reverse('board_members', kwargs={'url': self.account.url}))
        self.assertContains(resp, 'class="member"', 6)
        self.client.logout()
        self.login_member()
        self.membership = self.user.get_membership(account=self.account)
        resp = self.client.get(reverse('board_members', kwargs={'url': self.account.url}))
        self.assertContains(resp, 'class="member"', 1)
        self.assertNotContains(resp, 'data-chairman="true"')
        CommitteeFactory(chairman=self.membership)
        resp = self.client.get(reverse('board_members', kwargs={'url': self.account.url}))
        self.assertContains(resp, 'class="member"', 1)
        self.assertContains(resp, 'data-chairman="true"')


class BoardsListTest(TestCase):

    def test_list_view(self):
        self.account = AccountFactory()
        self.user = UserFactory(accounts=[self.account])
        self.login_member()
        resp = self.client.get(reverse('accounts:boards'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-account', 1)

    def test_session_set(self):
        self.account = AccountFactory()
        self.user = UserFactory(accounts=[self.account])
        self.client.login(username=self.user.email, password='member')
        url = reverse('accounts:boards')
        data = {
            'account_id': self.account.id
        }
        resp = self.ajax(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_current_account(self.client), self.account)


class MemberCreateTest(TestCase):

    def setUp(self):
        self.create_init_data()

    def test_member_create_with_invitation(self):
        self.account = AccountFactory()
        self.admin = AdminFactory(accounts=[self.account])
        self.user = UserFactory(accounts=[self.account])
        self.login_admin()
        url = reverse('member_create', kwargs={'url': get_current_account(self).url})
        data = {
            'first_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'last_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'email': u'{}_{}@example.com'.format(
                self.account.id,
                lorem_ipsum.words(38, False)[:75-len(str(self.account.id))-len('_@example.com')].replace(' ', '_')
            ),
            'password': User.objects.make_random_password(),
            'date_joined_board': '{:%b. %d, %Y}'.format(timezone.now()),
            'timezone': us_timezones[0],
            'account': get_current_account(self),
            'role': Membership.ROLES.member,
            'invitation': True
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('Member was added successfully.'))
        new_user = User.objects.all().order_by('-pk')[0]
        self.assertEqual(new_user.email, data['email'])
        self.assertEqual(len(mail.outbox), 0)

    def test_add_existed_member_with_invitation(self):
        self.account = AccountFactory()
        self.admin = AdminFactory(accounts=[self.account])
        self.login_admin()
        old_acc = list(self.user.accounts.all().values_list('id', flat=True))
        old_acc.append(get_current_account(self).id)
        url = reverse('member_create', kwargs={'url': get_current_account(self).url})
        data = {
            'first_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'last_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'email': self.user.email,
            'password': User.objects.make_random_password(),
            'date_joined_board': '{:%b. %d, %Y}'.format(timezone.now()),
            'timezone': us_timezones[0],
            'account': get_current_account(self),
            'role': Membership.ROLES.member,
            'invitation': True
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('Member was added successfully.'))
        self.assertItemsEqual(list(self.user.accounts.all().values_list('id', flat=True)), old_acc)

    def test_wrong_email(self):
        self.account = AccountFactory()
        self.admin = AdminFactory(accounts=[self.account])
        self.login_admin()
        url = reverse('member_create', kwargs={'url': get_current_account(self).url})
        data = {
            'first_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'last_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'email': u'{}_{}'.format(self.account.id, lorem_ipsum.words(1, False)),
            'password': User.objects.make_random_password(),
            'date_joined_board': '{:%b. %d, %Y}'.format(timezone.now()),
            'timezone': us_timezones[0],
            'account': get_current_account(self),
            'role': Membership.ROLES.member,
            'invitation': True
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('Enter a valid email address.'))

    def test_wrong_data(self):
        self.account = AccountFactory()
        self.admin = AdminFactory(accounts=[self.account])
        self.login_admin()
        url = reverse('member_create', kwargs={'url': get_current_account(self).url})
        data = {
            'email': self.user.email,
            'account': get_current_account(self)
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('This field is required.'), 3)

    def test_limit_members(self):
        self.login_admin()
        UserFactory.create_batch(3, accounts=[self.account])
        url = reverse('member_create', kwargs={'url': get_current_account(self).url})
        data = {
            'first_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'last_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'email': self.user.email,
            'password': User.objects.make_random_password(),
            'date_joined_board': '{:%b. %d, %Y}'.format(timezone.now()),
            'timezone': us_timezones[0],
            'account': get_current_account(self),
            'role': Membership.ROLES.member,
            'invitation': True
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('Limit of members amount for your billing plan is exceeded, '
                                        'you can upgrade it in your profile!'))

    def test_member_add_form_errors(self):
        self.login_admin()
        url = reverse('member_create', kwargs={'url': get_current_account(self).url})
        data = {
            'first_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'last_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'email': self.user.email,
            'password': User.objects.make_random_password(),
            'timezone': us_timezones[0],
            'account': get_current_account(self),
            'role': Membership.ROLES.member,
            'invitation': True
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, _('Enter a valid email address.'))

    def test_chairperson_permission(self):
        self.account = AccountFactory()
        user_chairperson = ChairpersonFactory(accounts=[self.account])
        self.login_member(user_chairperson.email)
        data = {
            'role': Membership.ROLES.chair,
            'email': u'{}_{}@example.com'.format(self.account.id, lorem_ipsum.words(1, False)),
            'first_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'last_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'password': 'member',
            'date_joined_board': '{:%b. %d, %Y}'.format(timezone.now()),
            'timezone': us_timezones[0],
            'account': get_current_account(self),
            'invitation': True
        }

        url = reverse('member_create', kwargs={'url': get_current_account(self).url})
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('Member was added successfully.'))

        url = reverse('profiles:edit', kwargs={'pk': self.membership.pk})
        data['email'] = u'{}_{}@example.com'.format(self.account.id, lorem_ipsum.words(1, False)),
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('Profile was changed successfully.'))
        self.assertEqual(Membership.ROLES.chair, Membership.objects.get(pk=self.membership.pk).role)

        url = reverse('profiles:edit', kwargs={'pk': user_chairperson.get_membership(self.account).pk})
        data['role'] = Membership.ROLES.admin
        data['email'] = u'{}_{}@example.com'.format(self.account.id, lorem_ipsum.words(1, False)),
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _('Profile was changed successfully.'))
        self.assertEqual(Membership.ROLES.chair, Membership.objects.get(pk=user_chairperson.get_membership(self.account).pk).role)

    def test_member_permission(self):
        self.account = AccountFactory()
        user_member = UserFactory(accounts=[self.account])
        self.login_member(user_member.email)
        data = {
            'role': Membership.ROLES.chair,
            'email': u'{}_{}@example.com'.format(self.account.id, lorem_ipsum.words(1, False)),
            'first_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'last_name': lorem_ipsum.words(1, False).capitalize()[:50],
            'password': 'member',
            'date_joined_board': '{:%b. %d, %Y}'.format(timezone.now()),
            'timezone': us_timezones[0],
            'account': get_current_account(self),
            'invitation': True
        }

        url = reverse('member_create', kwargs={'url': get_current_account(self).url})
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 403)

        url = reverse('profiles:edit', kwargs={'pk': self.user.pk})
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 404)
