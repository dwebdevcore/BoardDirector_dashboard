# -*- coding: utf-8 -*-
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core import mail
from django.forms import ValidationError
from django.http import Http404
from django.utils.translation import ugettext as _
from django.template import Context, Template

from .forms import UserCreationForm
from .models import User, Membership, TemporaryUserPassword
from accounts.factories import AccountFactory
from common.utils import BaseTestCase as TestCase, get_temporary_image, us_timezones
from profiles.factories import UserFactory
from profiles.templatetags.user_tags import avatar


class ProfilesTest(TestCase):
    USER_DATA = {
        'first_name': 'First',
        'last_name': 'Lastovich',
        'intro': 'This is testo intro',
        'timezone': us_timezones[0],
    }

    def setUp(self):
        self.create_init_data()
        mail.outbox = []

    def test_profile_member_view(self):
        resp = self.client.get(reverse('profiles:edit', kwargs={'pk': self.membership.pk}))
        self.assertEqual(resp.status_code, 302, 200)
        resp = self.client.get(reverse('profiles:detail', kwargs={'pk': self.membership.pk}))
        self.assertEqual(resp.status_code, 302, 200)
        self.login_admin()
        url = reverse('profiles:detail', kwargs={'pk': self.membership.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        user = UserFactory(accounts=[self.account])
        self.login_member(user.email)
        url = reverse('profiles:detail', kwargs={'pk': self.admin.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Edit Profile')
        self.login_admin()
        url = reverse('profiles:detail')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Edit Profile')

    def test_profile_edit_view(self):
        self.login_admin()
        url = reverse('profiles:edit', kwargs={'pk': self.membership.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(reverse('profiles:edit', kwargs={'pk': self.admin.pk}), self.USER_DATA, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Testing that admin can edit other profiles
        another_profile_url = reverse('profiles:edit', kwargs={'pk': (self.membership.pk)})
        resp = self.client.post(another_profile_url, self.USER_DATA, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Testing if email is already in use
        self.USER_DATA['email'] = self.admin.email
        resp = self.client.post(another_profile_url, self.USER_DATA, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, _('This email is already in use.'))
        # Testing that member cant edit other profiles
        self.login_member()
        url = reverse('profiles:edit', kwargs={'pk': self.membership.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        admin_membership = self.admin.get_membership(self.account)
        resp = self.client.post(reverse('profiles:edit', kwargs={'pk': admin_membership.pk}), self.USER_DATA, follow=True)
        self.assertEqual(resp.status_code, 403)

    def test_profile_login_view(self):
        self.client.post(reverse('auth_login'), {'username': self.admin.email,
                                                 'password': 'admin',
                                                 'rememberme': ''})
        self.assertEqual(self.client.session.get_expire_at_browser_close(), True)
        resp = self.client.get(reverse('auth_login'))
        self.assertEqual(resp.status_code, 200)

    def test_create_user(self):
        email_lowercase = 'normal@normal.com'
        user = User.objects.create_user(email_lowercase)
        self.assertEqual(user.email, email_lowercase)

    def test_empty_username(self):
        self.assertRaisesMessage(ValueError,
                                 'The given email must be set',
                                 User.objects.create_user, email='')

    def test_create_superuser(self):
        email_lowercase = 'normal@normal.com'
        password = 'password'
        user = User.objects.create_superuser(email_lowercase, password)
        self.assertEqual(user.email, email_lowercase)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_superuser)

    def test_email_user(self):
        self.user.email_user('Subject here', 'Here is the message.',
                             'from@example.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Subject here')

    def test_get_full_name(self):
        email_lowercase = 'normal@normal.com'
        user = User.objects.create_user(email_lowercase)
        self.assertEqual(user.get_full_name(), email_lowercase)

    def test_get_short_name(self):
        email_lowercase = 'normal@normal.cmo'
        user = User.objects.create_user(email_lowercase)
        self.assertEqual(user.get_short_name(), 'normal')

    def test_has_module_perms(self):
        self.assertTrue(self.user.has_module_perms('profiles'))

    def test_has_perm(self):
        self.assertTrue(self.user.has_perm('perm'))

    def test_avatar_url(self):
        self.assertEqual(settings.DEFAULT_AVATAR_URL, self.membership.avatar_url())
        self.login_member()
        temp_image = get_temporary_image()
        self.membership.avatar.save(temp_image.name, ContentFile(temp_image.read()), save=True)
        self.membership.save()
        resp = self.client.get(reverse('profiles:detail', kwargs={'pk': self.membership.pk}))
        self.assertContains(resp, avatar(self.membership, '360x270'))
        # without crops
        data = {
            'x1': 0,
            'y1': 0,
            'x2': 40,
            'y2': 40,
            'timezone': us_timezones[0],
            'date_joined_board': '{:%m/%d/%Y}'.format(timezone.now())
        }
        self.client.post(reverse('profiles:edit', kwargs={'pk': self.membership.pk}), data)
        resp = self.client.get(reverse('profiles:detail', kwargs={'pk': self.membership.pk}))
        self.assertNotContains(resp, settings.DEFAULT_AVATAR_URL)
        # with crop
        data = {
            'x1': 0,
            'y1': 0,
            'x2': 360,
            'y2': 270,
            'timezone': us_timezones[0],
            'date_joined_board': '{:%b %d, %Y}'.format(timezone.now())
        }
        self.client.post(reverse('profiles:edit', kwargs={'pk': self.membership.pk}), data)
        resp = self.client.get(reverse('profiles:detail', kwargs={'pk': self.membership.pk}))
        self.assertNotContains(resp, settings.DEFAULT_AVATAR_URL)
        # without geometry
        self.assertEqual(self.membership.avatar.url, self.membership.avatar_url())

        self.membership.avatar.delete()

    def test_clean_password2(self):
        data = {
            'email': self.user.email,
            'password1': 'member',
            'password2': 'member2',
        }
        form = UserCreationForm(data)
        form.is_valid()
        self.assertRaises(ValidationError(_("The two password fields didn't match.")))
        data = {
            'email': self.user.email,
            'password1': 'member',
            'password2': 'member',
        }
        form = UserCreationForm(data)
        form.is_valid()
        self.assertEqual(data['password2'], form.clean_password2())

    def test_form_save(self):
        data = {
            'email': 'aaa@gmail.com',
            'password1': 'member',
            'password2': 'member',
        }
        form = UserCreationForm(data)
        form.is_valid()
        u = form.save()
        self.assertEqual(data['email'], u.email)

    def test_user_tags(self):
        c = Context({'user': self.membership})
        t = Template("{% load user_tags %}{{ user|avatar:'90x90' }}")
        self.assertEqual(settings.DEFAULT_AVATAR_URL, t.render(c))

    def test_delete_membership_forbidden(self):
        self.login_admin()
        new_acc = AccountFactory()
        new_member = UserFactory(accounts=[new_acc])
        url = reverse('profiles:delete', kwargs={'pk': new_member.get_membership(new_acc).pk})
        response = self.ajax(url)
        self.assertEqual(response.status_code, 404)  # Currently this would be 404 as it'll simply be not found in queryset

    def test_delete_membership(self):
        self.login_admin()

        # deleted_membership = Membership.objects.get(id=self.membership.pk)
        url = reverse('profiles:delete', kwargs={'pk': self.membership.pk})
        response = self.ajax(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Membership.objects.filter(id=self.membership.pk).exists())

        # self.client.logout()
        # self.login_member(email=deleted_membership.user.email)
        # resp = self.client.get(reverse('accounts:boards'))
        # self.assertNotContains(resp, 'data-account')

    def test_get_membership_error(self):
        account = AccountFactory()
        with self.assertRaises(Http404):
            self.user.get_membership(account)

    def test_send_invitation_email_forbidden(self):
        url = reverse('profiles:invite', kwargs={'user_pk': self.membership.user.pk})
        self.login_member()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_send_invitation_email(self):
        self.login_admin()
        url = reverse('profiles:invite', kwargs={'user_pk': self.membership.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn(mail.outbox[0].subject, _('BoardDirector invitation'))

    def test_send_invitation_email_with_existing_password(self):
        self.login_admin()
        url = reverse('profiles:invite', kwargs={'user_pk': self.membership.user.pk})
        TemporaryUserPassword.objects.create(user=self.membership.user, password='user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)
        self.assertIn(mail.outbox[0].subject, _('BoardDirector invitation'))

    def test_user_get_absolute_url(self):
        self.assertEqual(self.admin.get_absolute_url(), '/profile/{}/'.format(self.admin.pk))

    def test_member_short_name(self):
        name = 'test name'
        self.membership.first_name = name
        self.membership.save()
        self.assertEqual(self.membership.get_short_name(), name)
