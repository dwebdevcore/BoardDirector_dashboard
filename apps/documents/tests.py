# -*- coding: utf-8 -*-
import json

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from accounts.account_helper import set_current_account, get_current_account
from .models import Document, Folder
from .factories import DocumentFactory

from accounts.factories import AccountFactory
from meetings.models import Meeting
from profiles.factories import UserFactory
from committees.models import Committee
from common.utils import BaseTestCase as TestCase
from common.utils import get_temporary_image


class DocumentsViewTest(TestCase):

    def setUp(self):
        self.create_init_data()
        self.meeting = Meeting.objects.latest('pk')
        self.committee = Committee.objects.latest('pk')
        self.client.login(username=self.admin.email, password='admin')
        self.session = self.client.session
        set_current_account(self, self.account)
        self.session.save()

    def test_ajax_create_agenda(self):
        url = reverse('documents:create')
        temp_image = get_temporary_image()
        data = {'agenda': temp_image, 'type': 'agenda'}
        response = self.ajax(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertTrue(Document.objects.filter(id=json_response['pk']).exists())
        created_doc = Document.objects.get(id=json_response['pk'])
        self.assertEqual(created_doc.extension(), 'jpeg')
        self.assertEqual(created_doc.filename, _('Meeting Agenda'))

    def test_ajax_delete(self):
        url = reverse('documents:delete')
        document = DocumentFactory(type=Document.OTHER, account=get_current_account(self))
        data = {'document_id': document.id}
        response = self.ajax(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['doc_id'], data['document_id'])
        self.assertFalse(Document.objects.filter(id=data['document_id']).exists())

    def test_ajax_delete_400(self):
        url = reverse('documents:delete')
        response = self.ajax(url)
        self.assertEqual(response.status_code, 404)

    def test_ajax_delete_charter_on_update(self):
        url = reverse('documents:delete')
        Folder.objects.update_or_create_meeting_folder(self.meeting)
        document = DocumentFactory(type=Document.AGENDA, account=get_current_account(self), folder=self.meeting.folder)
        data = {'document_id': document.id, 'action': 'update'}
        response = self.ajax(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertEqual(json_response['doc_id'], data['document_id'])
        updated_meeting = Meeting.objects.get(id=self.meeting.id)
        self.assertFalse(Document.objects.filter(id=data['document_id'], folder__id=updated_meeting.folder.id).exists())

    def test_update_meeting_agenda(self):
        url = reverse('documents:create')
        temp_image = get_temporary_image('pdf')
        data = {
            'agenda': temp_image,
            'type': 'agenda',
            'action': 'update',
            'meeting': self.meeting.id,
        }
        response = self.ajax(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertIn(self.meeting.get_committee_name(), json_response['html'])
        updated_meeting = Meeting.objects.get(id=self.meeting.id)
        self.assertEqual(Document.objects.filter(folder__id=updated_meeting.folder.id, type=Document.AGENDA)[0].id, json_response['pk'])

    def test_update_meeting_minutes(self):
        url = reverse('documents:create')
        temp_image = get_temporary_image('xls')
        data = {
            'minutes': temp_image,
            'type': 'minutes',
            'action': 'update',
            'meeting': self.meeting.id,
        }
        response = self.ajax(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertIn(self.meeting.get_committee_name(), json_response['html'])

    def test_update_meeting_other_docs(self):
        url = reverse('documents:create')
        temp_image = get_temporary_image()
        data = {
            'other': temp_image,
            'type': 'other',
            'action': 'update',
            'meeting': self.meeting.id,
        }
        response = self.ajax(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content)
        self.assertIn(self.meeting.get_committee_name(), json_response['html'])

    def test_download_link(self):
        self.login_admin()
        document = DocumentFactory(user=self.admin, account=self.account, folder=Folder.objects.get_account_root(self.account))
        url = reverse('documents:download', kwargs={'document_id': document.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_link_forbidden(self):
        account = AccountFactory()
        member = UserFactory(accounts=[account])
        self.client.login(username=member.email, password='member')
        session = self.client.session
        session['current_account_id'] = account.id
        session.save()

        document = DocumentFactory(user=self.admin, folder=Folder.objects.get_account_root(self.account))
        url = reverse('documents:download', kwargs={'document_id': document.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)
