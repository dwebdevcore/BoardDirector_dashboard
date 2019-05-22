# -*- coding: utf-8 -*-
from django.utils import lorem_ipsum
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.timezone import timedelta

from committees.factories import CommitteeFactory
from common.utils import BaseTestCase as TestCase
from documents.factories import DocumentFactory
from documents.models import Document
from meetings.factories import MeetingFactory
from profiles.factories import UserFactory
from committees.models import Committee

from .models import RecentActivity


class DashboardTest(TestCase):

    def setUp(self):
        self.create_init_data()
        self.committee = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        self.user.get_membership(self.account).committees.add(self.committee)
        self.admin.get_membership(self.account).committees.add(self.committee)
        self.membership.committees.add(self.committee)
        self.meetings = MeetingFactory(account=self.account, committee=self.committee)
        mail.outbox = []

    def test_dashboard_security(self):
        resp = self.client.get(reverse('dashboard:dashboard', kwargs={'url': self.account.url}))
        self.assertRedirects(resp, reverse('auth_login') + '?next={}'.format(
            reverse('dashboard:dashboard', kwargs={'url': self.account.url})), 302, 200)
        self.login_admin()
        resp = self.client.get(reverse('dashboard:dashboard', kwargs={'url': self.account.url}))
        self.assertEqual(resp.status_code, 200)
        self.login_member()
        url = reverse('dashboard:dashboard', kwargs={'url': self.account.url})
        self.client.get(url)

    def test_dashboard_recent_save_meeting_create(self):
        self.login_admin()
        self.client.get(reverse('meetings:create', kwargs={'url': self.account.url}))
        agenda = DocumentFactory(user=self.admin, type=Document.AGENDA)
        minutes = DocumentFactory(user=self.admin, type=Document.MINUTES)
        other_docs = DocumentFactory(user=self.admin, type=Document.OTHER)
        docs = '{},{},{}'.format(agenda.id, minutes.id, other_docs.id)
        date = timezone.now() + timedelta(days=2)
        data = {
            'name': lorem_ipsum.words(2, False).capitalize()[:50],
            'date': date.date().strftime("%b. %d, %Y"),
            'time_start':  date.time().strftime("%I:%M %p"),
            'time_end':  (date + timedelta(hours=3)).time().strftime("%I:%M %p"),
            'location': '709 Sixth Street, Newark, DE 19711',
            'committee': self.committee.id,
            'account': self.account,
            'uploaded': docs
        }
        resp = self.client.post(reverse('meetings:create', kwargs={'url': self.account.url}), data, follow=True)
        self.assertContains(resp, 'Meeting was added successfully.')
        self.assertTrue(len(RecentActivity.objects.all()) > 0)
        for item in RecentActivity.objects.all():
            self.assertEqual(item.content_object.name, data['name'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, self.account.name)

    def test_dashboard_recent_save_meeting_create_without_notify(self):
        self.login_admin()
        self.account.send_notification = False
        self.account.save()
        self.client.get(reverse('meetings:create', kwargs={'url': self.account.url}))
        agenda = DocumentFactory(user=self.admin, type=Document.AGENDA)
        minutes = DocumentFactory(user=self.admin, type=Document.MINUTES)
        other_docs = DocumentFactory(user=self.admin, type=Document.OTHER)
        docs = '{},{},{}'.format(agenda.id, minutes.id, other_docs.id)
        date = timezone.now() + timedelta(days=2)
        data = {
            'name': lorem_ipsum.words(2, False).capitalize()[:50],
            'date': date.date().strftime("%b. %d, %Y"),
            'time_start':  date.time().strftime("%I:%M %p"),
            'time_end':  (date + timedelta(hours=3)).time().strftime("%I:%M %p"),
            'location': '709 Sixth Street, Newark, DE 19711',
            'committee': self.committee.id,
            'account': self.account,
            'uploaded': docs
        }
        resp = self.client.post(reverse('meetings:create', kwargs={'url': self.account.url}), data, follow=True)
        self.assertContains(resp, 'Meeting was added successfully.')
        self.assertTrue(len(RecentActivity.objects.all()) > 0)
        for item in RecentActivity.objects.all():
            self.assertEqual(item.content_object.name, data['name'])
        self.assertEqual(len(mail.outbox), 0)

    def test_dashboard_recent_save_committee_create(self):
        self.login_admin()
        url = reverse('committees:create', kwargs={'url': self.account.url})
        data = {
            'name': lorem_ipsum.words(2, False).capitalize()[:50],
            'chairman': [self.membership_admin.id],
            'members': [self.membership_admin.id, self.membership.id],
            'summary': lorem_ipsum.words(5, True),
            'description': lorem_ipsum.words(20, True),
            'account': self.account}

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Committee was added successfully.')
        self.assertTrue(len(RecentActivity.objects.all()) > 0)
        for item in RecentActivity.objects.all():
            self.assertEqual(item.content_object.name, data['name'])
            self.assertEqual(item.content_object.account, data['account'])
            self.assertEqual(item.init_user, self.admin)
        self.assertEqual(len(mail.outbox), 0)

    def test_dashboard_recent_save_committee_change(self):
        self.login_admin()
        url = reverse('committees:update', kwargs={'pk': self.committee.pk, 'url': self.account.url})
        data = {
            'name': self.committee.name,
            'chairman': list(self.committee.chairman.all().values_list('id', flat=True)),
            'members': list(self.committee.memberships.all().values_list('id', flat=True)),
            'summary':  self.committee.summary,
            'description': self.committee.description,
            'account': self.account}
        user2 = UserFactory(accounts=[self.account])
        data['members'].append(user2.get_membership(account=self.account).id)
        mail.outbox = []
        response = self.client.post(url, data, follow=True)
        updated_committee_members = list(
            Committee.objects.get(id=self.committee.id).memberships.all().values_list('id', flat=True))
        self.assertItemsEqual(updated_committee_members, data['members'])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Committee was changed successfully.')
        self.assertTrue(len(RecentActivity.objects.all()) > 0)
        for item in RecentActivity.objects.all():
            self.assertEqual(item.content_object.name, data['name'])
            self.assertEqual(item.content_object.account, data['account'])
            self.assertEqual(item.init_user, self.admin)
            self.assertEqual(item.action_flag, RecentActivity.CHANGE)
        self.assertEqual(len(mail.outbox), 0)
