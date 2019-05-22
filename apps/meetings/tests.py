# -*- coding: utf-8 -*-
import json
import urllib

from django.core.urlresolvers import reverse
from django.utils import lorem_ipsum
from django.utils import timezone
from django.utils.timezone import timedelta
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from accounts.account_helper import set_current_account, get_current_account
from accounts.factories import AccountFactory
from common.utils import BaseTestCase as TestCase
from committees.factories import CommitteeFactory
from documents.models import Document, Folder
from documents.factories import DocumentFactory
from meetings.factories import MeetingFactory
from meetings.models import Meeting
from profiles.factories import ChairpersonFactory


class MeetingsViewTest(TestCase):

    def setUp(self):
        self.create_init_data()
        self.meeting = Meeting.objects.latest('pk')
        self.client.login(username=self.admin.email, password='admin')
        self.session = self.client.session
        set_current_account(self, self.account)
        self.session.save()

    def test_404(self):
        response = self.client.get('/meetings/detail/test')
        self.assertEqual(response.status_code, 404)

    def test_detail_view(self):
        url = reverse('meetings:detail', kwargs={'pk': self.meeting.pk, 'url': get_current_account(self).url})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.meeting.name)
        self.assertContains(response, self.meeting.location)

    def test_list_view_anonymous(self):
        self.client.logout()
        url = reverse('meetings:list', kwargs={'url': self.account.url})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('auth_login') + '?next={}'.format(
            reverse('meetings:list', kwargs={'url': self.account.url})), 302, 200)

    def test_list_view(self):
        url = reverse('meetings:list', kwargs={'url': get_current_account(self).url})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        meetings = Meeting.objects.filter(account=get_current_account(self))
        self.assertEqual(len(meetings), 2)
        for meeting in meetings:
            self.assertContains(response, meeting.name)

    def test_create(self):
        # TODO: Add Board Book testing once 
        url = reverse('meetings:create', kwargs={'url': get_current_account(self).url})
        agenda = DocumentFactory(user=self.admin, type=Document.AGENDA)
        minutes = DocumentFactory(user=self.admin, type=Document.MINUTES)
        other_docs = DocumentFactory(user=self.admin, type=Document.OTHER)
        docs = '{},{},{}'.format(agenda.id, minutes.id, other_docs.id)
        date = timezone.now() + timedelta(days=2)
        data = {
            'name': lorem_ipsum.words(2, False).capitalize()[:50],
            'description': 'Any description',
            'date': date.date().strftime("%b. %d, %Y"),
            'time_start':  date.time().strftime("%I:%M %p"),
            'time_end':  (date + timedelta(hours=3)).time().strftime("%I:%M %p"),
            'location': '709 Sixth Street, Newark, DE 19711',
            'committee': self.membership.committees.all()[0].id,
            'account': get_current_account(self),
            'uploaded': docs,
            'repeat_end_type': 'never',
            'action': 'publish',
        }
        response = self.client.post(url, data, follow=True)
        self.assertNoFormErrors(response)

        meeting = Meeting.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Meeting was added successfully.')
        self.assertEqual(meeting.name, data['name'])
        self.assertContains(response, '709 Sixth Street, Newark, DE 19711')

        # All Board Members Meeting
        data['committee'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All Board Members Meeting')

        # No Agenda Available
        data['uploaded'] = '{},{}'.format(minutes.id, other_docs.id)
        response = self.client.post(url, data, follow=True)
        meeting = Meeting.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(meeting.get_agenda())

        # No Minutes Available
        data['uploaded'] = '{},{}'.format(agenda.id, other_docs.id)
        response = self.client.post(url, data, follow=True)
        meeting = Meeting.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(meeting.get_minutes())

        # No Other Docs Available
        data['uploaded'] = '{},{}'.format(agenda.id, minutes.id)
        response = self.client.post(url, data, follow=True)
        meeting = Meeting.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(meeting.get_other_docs())

    def test_create_chairman_of_committee(self):
        self.login_member(self.membership.user.email)
        url = reverse('meetings:create', kwargs={'url': get_current_account(self).url})
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
            'committee': '',
            'account': get_current_account(self),
            'uploaded': docs
        }
        response = self.client.post(url, data, follow=True)
        meeting = Meeting.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(meeting.name, data['name'])
        self.assertContains(response, 'Meeting was added successfully.')
        self.assertContains(response, '709 Sixth Street, Newark, DE 19711')

        # All Board Members Meeting
        data['committee'] = ''
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All Board Members Meeting')

        # No Agenda Available
        data['uploaded'] = '{},{}'.format(minutes.id, other_docs.id)
        response = self.client.post(url, data, follow=True)
        meeting = Meeting.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(meeting.get_agenda())

        # No Minutes Available
        data['uploaded'] = '{},{}'.format(agenda.id, other_docs.id)
        response = self.client.post(url, data, follow=True)
        meeting = Meeting.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(meeting.get_minutes())

        # No Other Docs Available
        data['uploaded'] = '{},{}'.format(agenda.id, minutes.id)
        response = self.client.post(url, data, follow=True)
        meeting = Meeting.objects.all().order_by('-pk')[0]
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(meeting.get_other_docs())

    def test_create_error(self):
        url = reverse('meetings:create', kwargs={'url': get_current_account(self).url})
        agenda = DocumentFactory(user=self.admin, type=Document.AGENDA)
        minutes = DocumentFactory(user=self.admin, type=Document.MINUTES)
        other_docs = DocumentFactory(user=self.admin, type=Document.OTHER)
        docs = '{},{},{}'.format(agenda.id, minutes.id, other_docs.id)
        date = timezone.now() + timedelta(days=2)
        data = {
            'date': date.date().strftime("%b %d, %Y"),
            'time_start':  date.time().strftime("%I:%M %p"),
            'time_end':  (date + timedelta(hours=3)).time().strftime("%I:%M %p"),
            'location': '709 Sixth Street, Newark, DE 19711',
            'committee': self.membership.committees.all()[0].id,
            'account': get_current_account(self),
            'uploaded': docs,
            'description': 'Any description',
            'repeat_end_type': 'never',
            'action': 'publish',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['name'][0], _('This field is required.'))
        self.assertIn('other_docs', response.context)
        self.assertIn('doc_agenda', response.context)
        self.assertIn('doc_minutes', response.context)

    def test_ajax_filter(self):
        self.skipTest("dajaxice is no more. So this test must be replaced into URL checks and validation of output order.")
        url = '/dajaxice/common.meeting_filter/'
        data = {'filter_by': self.meeting.committee.id}
        argv = {'argv': json.dumps(data)}
        response = self.ajax(url, data=urllib.urlencode(argv), content_type='application/x-www-form-urlencoded')
        obj = json.loads(response.content)
        meetings = Meeting.objects.filter(committee=self.meeting.committee.id)
        self.assertEqual(obj[0]['val']['meetings'],
                         render_to_string('meetings/includes/meetings.html', {'meetings': meetings}))
        # desc
        data = {'filter_by': 'desc'}
        argv = {'argv': json.dumps(data)}
        response = self.ajax(url, data=urllib.urlencode(argv), content_type='application/x-www-form-urlencoded')
        obj = json.loads(response.content)
        meetings = Meeting.objects.filter(account=get_current_account(self)).order_by('-start')
        self.assertEqual(obj[0]['val']['meetings'],
                         render_to_string('meetings/includes/meetings.html', {'meetings': meetings}))
        # asc
        data = {'filter_by': 'asc'}
        argv = {'argv': json.dumps(data)}
        response = self.ajax(url, data=urllib.urlencode(argv), content_type='application/x-www-form-urlencoded')
        obj = json.loads(response.content)
        meetings = Meeting.objects.filter(account=get_current_account(self)).order_by('start')
        self.assertEqual(obj[0]['val']['meetings'],
                         render_to_string('meetings/includes/meetings.html', {'meetings': meetings}))

    def test_update(self):
        url = reverse('meetings:update', kwargs={'pk': self.meeting.pk, 'url': get_current_account(self).url})
        data = {
            'name': self.meeting.name,
            'description': self.meeting.description,
            'committee': self.meeting.committee.id,
            'date': self.meeting.start.strftime("%b. %d, %Y"),
            'time_start': self.meeting.start.strftime("%I:%M %p"),
            'time_end': self.meeting.end.strftime("%I:%M %p"),
            'location': '709 Sixth Street, Newark, DE 19711',
            'account': get_current_account(self),
            'repeat_end_type': 'never',
            'action': 'update',
        }
        response = self.client.post(url, data, follow=True)
        self.assertNoFormErrors(response)

        updated_location = Meeting.objects.get(id=self.meeting.id).location
        self.assertEqual(updated_location, data['location'])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Meeting was changed successfully.')

    def test_update_meeting_user_forbidden(self):
        chairperson = ChairpersonFactory(accounts=[self.account])
        self.login_member(chairperson.email)
        url = reverse('meetings:update', kwargs={'pk': self.meeting.pk, 'url': get_current_account(self).url})
        data = {
            'name': self.meeting.name,
            'committee': '',
            'date': self.meeting.start.strftime("%b %d, %Y"),
            'time_start': self.meeting.start.strftime("%I:%M %p"),
            'time_end': self.meeting.end.strftime("%I:%M %p"),
            'location': '709 Sixth Street, Newark, DE 19711',
            'account': get_current_account(self)
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_delete_meeting_forbidden(self):
        self.login_admin()
        new_acc = AccountFactory()
        new_committee = CommitteeFactory(chairman=self.membership_admin, account=new_acc)
        new_meeting = MeetingFactory(committee=new_committee, account=new_acc)
        url = reverse('meetings:delete', kwargs={'pk': new_meeting.pk, 'url': get_current_account(self).url})
        response = self.ajax(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_meeting_user_forbidden(self):
        chairperson = ChairpersonFactory(accounts=[self.account])
        self.login_member(chairperson.email)
        url = reverse('meetings:delete', kwargs={'pk': self.meeting.pk, 'url': get_current_account(self).url})
        response = self.ajax(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_meeting(self):
        self.login_admin()
        Folder.objects.update_or_create_meeting_folder(self.meeting)
        new_document = DocumentFactory(folder=self.meeting.folder)
        url = reverse('meetings:delete', kwargs={'pk': self.meeting.pk, 'url': get_current_account(self).url})
        response = self.ajax(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Meeting.objects.filter(id=self.meeting.pk).exists())
        self.assertFalse(Document.objects.filter(id=new_document.pk).exists())
