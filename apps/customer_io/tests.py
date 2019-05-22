# -*- coding: utf-8 -*-
import os
from mock import patch

from django.utils import lorem_ipsum
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.timezone import timedelta

from accounts.account_helper import set_current_account, get_current_account
from billing.factories import InvoiceFactory
from billing.models import Invoice
from common.utils import BaseTestCase as TestCase
from common.utils import get_temporary_image
from documents.factories import DocumentFactory
from documents.models import Document
from profiles.models import Membership
from registration.models import RegistrationProfile


class CustomerIOSignalsTest(TestCase):
    USER_DATA = {
        'email': '{}@gmail.ru'.format(lorem_ipsum.words(1, False)),
        'password1': lorem_ipsum.words(1, False),
        'name': lorem_ipsum.words(2, False)[:255],
        'url': lorem_ipsum.words(1, False)[:255]
    }

    def setUp(self):
        self.create_init_data()
        self.client.login(username=self.admin.email, password='admin')
        self.session = self.client.session
        set_current_account(self, self.account)
        self.session.save()

    @patch('customer_io.api.CIOApi.track_event')
    def test_event_user_activated(self, mock_track_event):
        # Activate User
        self.client.post(reverse('registration_register'), self.USER_DATA)
        profile = RegistrationProfile.objects.get(user__email=self.USER_DATA['email'])
        resp = self.client.get(reverse('registration_activate', kwargs={'activation_key': profile.activation_key}))
        self.assertRedirects(resp, reverse('registration_activation_complete'))
        # Signal fired
        self.assertEquals(mock_track_event.call_count, 1)

    @patch('customer_io.api.CIOApi.create_or_update')
    def test_update_membership(self, mock_create_or_update):
        self.login_member()
        self.assertEquals(mock_create_or_update.call_count, 1)

    @patch('customer_io.api.CIOApi.track_event')
    def test_event_document_created(self, mock_track_event):
        # Create Document
        url = reverse('documents:create')
        temp_image = get_temporary_image()
        data = {'agenda': temp_image, 'type': 'agenda'}
        response = self.ajax(url, data)
        self.assertEqual(response.status_code, 200)
        # Signal fired
        self.assertEquals(mock_track_event.call_count, 1)

    @patch('customer_io.api.CIOApi.track_event')
    def test_event_meeting_created(self, mock_track_event):
        # Create Meeting
        url = reverse('meetings:create', kwargs={'url': get_current_account(self).url})
        agenda = DocumentFactory(user=self.admin, type=Document.AGENDA)
        minutes = DocumentFactory(user=self.admin, type=Document.MINUTES)
        other_docs = DocumentFactory(user=self.admin, type=Document.OTHER)
        docs = '{},{},{}'.format(agenda.id, minutes.id, other_docs.id)
        date = timezone.now() + timedelta(days=2)
        data = {
            'name': lorem_ipsum.words(2, False).capitalize()[:50],
            'date': date.date().strftime('%b. %d, %Y'),
            'time_start':  date.time().strftime('%I:%M %p'),
            'time_end':  (date + timedelta(hours=3)).time().strftime('%I:%M %p'),
            'location': '709 Sixth Street, Newark, DE 19711',
            'committee': self.membership.committees.all()[0].id,
            'account': get_current_account(self),
            'uploaded': docs,
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Signal fired
        self.assertEquals(mock_track_event.call_count, 1)

    @patch('customer_io.api.CIOApi.track_event')
    def test_event_committee_created(self, mock_track_event):
        # Create Committee
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
        # Signal fired
        self.assertEquals(mock_track_event.call_count, 1)

    @patch('customer_io.api.CIOApi.track_event')
    def test_event_invocie_update(self, mock_track_event):
        # Update Invoice
        invoice = InvoiceFactory()
        invoice.status = Invoice.FAILED
        invoice.save()
        invoice.status = Invoice.PAID
        invoice.save()
        # Signal fired
        self.assertEquals(mock_track_event.call_count, 3)

    @patch('customer_io.api.CIOApi.delete')
    def test_delete_membership(self, mock_delete):
        self.membership.delete()
        self.assertEquals(mock_delete.call_count, 1)


class CustomerIOCommandsTest(TestCase):
    def setUp(self):
        self.create_init_data()

    def call_command_null(self, command):
        """Redirect stdout to null."""
        with open(os.devnull, 'w') as f:
            call_command(command, stdout=f)

    @patch('customer_io.api.CIOApi.create_or_update')
    def test_export_customerio(self, mock_create_or_update):
        self.call_command_null('export_customerio')
        self.assertEquals(mock_create_or_update.call_count, Membership.objects.count())


class CustomerIOPageviewTest(TestCase):
    def setUp(self):
        self.create_init_data()

    @override_settings(CUSTOMERIO_ENABLED=True)
    def test_pageview_enabled(self):
        self.login_member()
        url = reverse('dashboard:dashboard', kwargs={'url': self.account.url})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '_cio.identify', 1)

    @override_settings(CUSTOMERIO_ENABLED=False)
    def test_pageview_disabled(self):
        self.login_member()
        url = reverse('dashboard:dashboard', kwargs={'url': self.account.url})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '_cio.identify', 0)
