# -*- coding: utf-8 -*-
import json
import urllib

from django.core.urlresolvers import reverse
from django.utils import lorem_ipsum
from django.template.loader import render_to_string

from accounts.account_helper import set_current_account, get_current_account
from accounts.factories import AccountFactory
from committees.models import Committee
from documents.factories import DocumentFactory
from documents.models import Document
from meetings.factories import MeetingFactory
from meetings.models import Meeting
from profiles.factories import UserFactory
from common.utils import BaseTestCase as TestCase
from .factories import CommitteeFactory


class CommitteesViewTest(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.create_init_data()
        self.committee = Committee.objects.latest('pk')
        self.membership.committees.add(self.committee)
        self.client.login(username=self.admin.email, password='admin')
        self.session = self.client.session
        set_current_account(self, self.account)
        self.session.save()

    def test_detail_view(self):
        url = reverse('committees:detail', kwargs={'pk': self.committee.pk, 'url': get_current_account(self).url})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.committee.name)
        self.assertContains(response, self.committee.description)

    def test_list_view(self):
        committee2 = CommitteeFactory(chairman=self.membership_admin, account=self.account)
        url = reverse('committees:list', kwargs={'url': get_current_account(self).url})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.committee.name)
        self.assertContains(response, committee2.name)

    def test_create(self):
        url = reverse('committees:create', kwargs={'url': get_current_account(self).url})
        data = {
            'name': lorem_ipsum.words(2, False).capitalize()[:50],
            'chairman': self.membership_admin.id,
            'members': [self.membership_admin.id, self.membership.id],
            'summary': lorem_ipsum.words(5, True),
            'description': lorem_ipsum.words(20, True),
            'account': get_current_account(self)}

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Committee was added successfully.')

    def test_update(self):
        url = reverse('committees:update', kwargs={'pk': self.committee.pk, 'url': get_current_account(self).url})
        self.committee.chairman.add(self.admin.get_membership(self.account))
        data = {
            'name': self.committee.name,
            'chairman': list(self.committee.chairman.all().values_list('id', flat=True)),
            'members': list(self.committee.memberships.all().values_list('id', flat=True)),
            'summary':  self.committee.summary,
            'description': self.committee.description,
            'account': get_current_account(self)}
        user2 = UserFactory(accounts=[get_current_account(self)])
        membership_user2 = user2.get_membership(account=get_current_account(self))
        data['members'].append(membership_user2.id)
        response = self.client.post(url, data, follow=True)
        updated_committee_members = list(
            Committee.objects.get(id=self.committee.id).memberships.all().values_list('id', flat=True))
        self.assertItemsEqual(updated_committee_members, data['members'])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Committee was changed successfully.')

    def test_update_wrong(self):
        user = UserFactory(accounts=[self.account])
        self.login_member(user.email)
        url = reverse('committees:update', kwargs={'pk': self.committee.pk, 'url': get_current_account(self).url})
        data = {
            'name': self.committee.name,
            'chairman': self.committee.chairman.all(),
            'members': list(self.committee.memberships.all().values_list('id', flat=True)),
            'summary':  self.committee.summary,
            'description': self.committee.description,
            'account': get_current_account(self)}
        user2 = UserFactory(accounts=[get_current_account(self)])
        membership_user2 = user2.get_membership(account=get_current_account(self))
        data['members'].append(membership_user2.id)
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_permission_denied(self):
        self.login_admin()
        new_acc = AccountFactory()
        new_committee = CommitteeFactory(chairman=self.membership_admin, account=new_acc)
        url = reverse('committees:detail', kwargs={'pk': new_committee.pk, 'url': get_current_account(self).url})
        resp = self.client.get(url)
        self.assertRedirects(resp, reverse('accounts:boards'))

    def test_delete_committee_forbidden(self):
        self.login_admin()
        new_acc = AccountFactory()
        committee2 = CommitteeFactory(chairman=self.membership_admin, account=new_acc)
        url = reverse('committees:delete', kwargs={'pk': committee2.pk, 'url': get_current_account(self).url})
        response = self.ajax(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_committee(self):
        self.login_admin()
        new_meeting = MeetingFactory(account=self.account, committee=self.committee)
        new_document = DocumentFactory(meeting=new_meeting)
        url = reverse('committees:delete', kwargs={'pk': self.committee.pk, 'url': get_current_account(self).url})
        response = self.ajax(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Committee.objects.filter(id=self.committee.pk).exists())
        self.assertFalse(Meeting.objects.filter(id=new_meeting.pk).exists())
        self.assertFalse(Document.objects.filter(id=new_document.pk).exists())

    def test_ajax_committees_filter(self):
        url = '/dajaxice/common.committees_filter/'
        data = {'committee_id': self.committee.id}
        argv = {'argv': json.dumps(data)}
        response = self.ajax(url, data=urllib.urlencode(argv), content_type='application/x-www-form-urlencoded')
        obj = json.loads(response.content)
        self.assertEqual(obj[0]['val']['committees'],
                         render_to_string('committees/includes/committees.html', {'committees': [self.committee]}))
