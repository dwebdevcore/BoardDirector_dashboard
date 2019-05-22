import json
from datetime import timedelta
from encodings.base64_codec import base64_encode

import pytz
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.utils import timezone
from django.utils.timezone import now

from committees.factories import CommitteeFactory
from committees.models import Committee
from common.api.exception_handler import WRONG_REQUEST
from common.utils import AccJsonRequestsTestCase
from dashboard.models import RecentActivity
from documents.models import Folder, Document
from meetings.models import Meeting, MeetingAttendance
from rsvp.models import RsvpResponse


class MeetingApiTestCase(AccJsonRequestsTestCase):
    def setUp(self):
        self.create_init_data()
        self.maxDiff = None

    def test_create(self):
        self.init_second_account()
        self.login_admin()

        required = self.acc_post_json('api-meetings-meetings-list', {}, assert_status_code=400).json()
        fail_check = {f: ['This field is required.'] for f in ['name', 'description', 'start', 'end', 'location']}
        fail_check['detail'] = WRONG_REQUEST
        self.assertEqual(fail_check, required)

        # Create
        meeting_json = self._create_simple_meeting()
        self.assertEqual('Test meeting', meeting_json['name'])

        meeting = Meeting.objects.get(pk=meeting_json['id'])
        self.assertEqual([self.membership.id], list(meeting.extra_members.values_list('id', flat=True)))

        # Verify misc options are created
        self.assertFalse(Folder.objects.filter(meeting=meeting).exists(), "Meetings folder is not created until there is some doc in it.")
        self.assertTrue(RecentActivity.objects.filter(
            content_type=ContentType.objects.get_for_model(meeting),
            object_id=meeting.id,
            action_flag=RecentActivity.ADDITION).exists(), "Recent activity should be logged.")

    def test_update(self):
        self.init_second_account()
        self.login_admin()

        meeting_json = self._create_simple_meeting()
        meeting = Meeting.objects.get(pk=meeting_json['id'])

        # Update
        _, m3 = self.create_membership()
        meeting_json['extra_members'] = [m3.id]
        meeting_json['name'] = 'Update it!'
        committee = Committee.objects.filter(account=self.account).first()
        meeting_json['committee'] = committee.id
        meeting_json = self.acc_put_json('api-meetings-meetings-detail', pk=meeting.id, json_data=meeting_json).json()

        meeting = Meeting.objects.get(pk=meeting_json['id'])
        self.assertEqual([m3.id], list(meeting.extra_members.values_list('id', flat=True)))
        self.assertEqual('Update it!', meeting.name)
        self.assertEqual(committee, meeting.committee)

        self.assertTrue(RecentActivity.objects.filter(
            content_type=ContentType.objects.get_for_model(meeting),
            object_id=meeting.id,
            action_flag=RecentActivity.CHANGE).exists(), "Recent activity should be logged.")

        # Wrong committee/membership - from other account:
        c2 = CommitteeFactory(account=self.account2)

        mm1 = dict(meeting_json)
        mm1['committee'] = c2.id
        error = self.acc_put_json('api-meetings-meetings-detail', pk=meeting.id, json_data=mm1, assert_status_code=400).json()
        self.assertEqual({'committee': ['Invalid pk "%d" - object does not exist.' % c2.id],
                          'detail': WRONG_REQUEST}, error)

        mm2 = dict(meeting_json)
        mm2['extra_members'] = [self.membership2.id]
        error = self.acc_put_json('api-meetings-meetings-detail', pk=meeting.id, json_data=mm2, assert_status_code=400).json()
        self.assertEqual({'extra_members': ['Invalid pk "%d" - object does not exist.' % self.membership2.id],
                          'detail': WRONG_REQUEST}, error)

        # Can reset those values
        mm3 = dict(meeting_json)
        mm3['committee'] = None
        mm3['extra_members'] = []
        meeting_json = self.acc_put_json('api-meetings-meetings-detail', pk=meeting.id, json_data=mm3).json()
        meeting = Meeting.objects.get(pk=meeting_json['id'])
        self.assertEqual([], list(meeting.extra_members.values_list('id', flat=True)))
        self.assertEqual(None, meeting.committee)

    def test_delete(self):
        self.login_admin()
        meeting_json = self._create_simple_meeting()
        self.assertTrue(Meeting.objects.filter(pk=meeting_json['id']).exists())
        self.acc_delete('api-meetings-meetings-detail', pk=meeting_json['id'])
        self.assertFalse(Meeting.objects.filter(pk=meeting_json['id']).exists())

    def test_list_next_repetition_date(self):
        self.login_admin()

        # Committee both to have predictable memberships count and also to overcome current permissions issue: to edit meetings
        # one needs to be either meeting's committee chair or chair of any other committee (if meetings doesn't have any selected)
        committee = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        committee.memberships.add(self.membership_admin)

        meeting_json = self.acc_post_json('api-meetings-meetings-list', {
            # Note: dates are in past
            'start': (now().replace(tzinfo=pytz.utc, hour=12, minute=0, second=0, microsecond=0) - timedelta(days=3)).isoformat(),
            'end': (now().replace(tzinfo=pytz.utc, hour=13, minute=0, second=0, microsecond=0) - timedelta(days=3)).isoformat(),
            'name': 'Test meeting',
            'description': 'describe it! Now.',
            'location': 'in memory',
            'committee': None,
            'extra_members': [],
            'repeat_type': Meeting.REPEAT_TYPES.every_day,
            'repeat_interval': 1,
            'repeat_max_count': 100,
        }).json()

        self.acc_post_json('api-meetings-meetings-publish', json_data={}, pk=meeting_json['id'], assert_status_code=200)

        meetings = self.acc_get('api-meetings-meetings-list').json()
        meeting = next(m for m in meetings['results'] if m['id'] == meeting_json['id'])
        self.assertEqual(now().replace(tzinfo=pytz.utc).date().isoformat(), meeting['next_repetition_date'])

    def test_details(self):
        self.login_admin()
        meeting_json = self._create_simple_meeting()
        meeting_json['repeat_type'] = Meeting.REPEAT_TYPES.every_week
        meeting_json['repeat_max_count'] = 100
        self.acc_put_json('api-meetings-meetings-detail', pk=meeting_json['id'], json_data=meeting_json)

        meeting_json = self.get_meeting(meeting_json['id'])
        details = meeting_json['details']

        self.assertEqual('No reply', next(r for r in details['rsvp_responses'] if r['user_id'] == self.user.id)['attending'])
        self.assertEqual(10, len(details['future_repetitions']))
        self.assertTrue(details['current_repetition'])

    def test_publish_and_reminder(self):
        self.login_admin()

        # Committee both to have predictable memberships count and also to overcome current permissions issue: to edit meetings
        # one needs to be either meeting's committee chair or chair of any other committee (if meetings doesn't have any selected)
        committee = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        committee.memberships.add(self.membership)
        committee.memberships.add(self.membership_admin)

        meeting_json = self._create_simple_meeting(committee=committee.id)

        # Test reminder can't be send for unpublished meetings
        self.acc_post_json('api-meetings-meetings-reminder', json_data={}, pk=meeting_json['id'], assert_status_code=403)

        mail.outbox = []
        self.acc_post_json('api-meetings-meetings-publish', json_data={}, pk=meeting_json['id'], assert_status_code=200)
        meeting_json = self.get_meeting(meeting_json['id'])
        self.assertEqual(1, meeting_json['status'])
        self.assertEqual(2, len(mail.outbox))

        mail.outbox = []
        self.acc_post_json('api-meetings-meetings-reminder', json_data={}, pk=meeting_json['id'], assert_status_code=200)
        self.assertEqual(1, len(mail.outbox))  # 1 because currently reminder isn't sent to initiating user

    def test_rsvp(self):
        self.login_admin()

        committee = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        committee.memberships.add(self.membership)
        committee.memberships.add(self.membership_admin)

        meeting_json = self._create_simple_meeting(committee=committee.id, publish=True)

        meeting_json['repeat_type'] = Meeting.REPEAT_TYPES.every_week
        meeting_json['repeat_max_count'] = 20
        self.acc_put_json('api-meetings-meetings-detail', pk=meeting_json['id'], json_data=meeting_json)
        meeting_json = self.get_meeting(meeting_json['id'])

        self.assertEqual(None, meeting_json['details']['current_repetition']['rsvp_response'])

        # Global rsvp for all dates
        self.acc_post_json('api-meetings-meetings-rsvp', pk=meeting_json['id'], json_data={
            'response': RsvpResponse.ACCEPT,
            'accept_type': RsvpResponse.IN_PERSON,
            'note': 'Rsvp note here!',
            'meeting_repetition': None
        })
        meeting_json = self.get_meeting(meeting_json['id'])

        details = meeting_json['details']
        self.assertEqual(RsvpResponse.ACCEPT, details['current_repetition']['rsvp_response'])
        self.assertEqual(RsvpResponse.IN_PERSON, details['current_repetition']['rsvp_accept_type'])
        self.assertEqual('Rsvp note here!', details['current_repetition']['rsvp_note'])

        self.assertEqual(RsvpResponse.ACCEPT, details['future_repetitions'][2]['rsvp_response'])
        self.assertEqual(RsvpResponse.IN_PERSON, details['future_repetitions'][2]['rsvp_accept_type'])
        self.assertEqual('Rsvp note here!', details['future_repetitions'][2]['rsvp_note'])

        # Now local RSVP for single date
        self.acc_post_json('api-meetings-meetings-rsvp', pk=meeting_json['id'], json_data={
            'response': RsvpResponse.TENTATIVE,
            'accept_type': 0,
            'note': 'Sorry guys',
            'meeting_repetition': details['future_repetitions'][2]['id'],
        })
        meeting_json = self.get_meeting(meeting_json['id'])

        details = meeting_json['details']
        # as it was before
        self.assertEqual(RsvpResponse.ACCEPT, details['current_repetition']['rsvp_response'])
        self.assertEqual(RsvpResponse.IN_PERSON, details['current_repetition']['rsvp_accept_type'])
        self.assertEqual('Rsvp note here!', details['current_repetition']['rsvp_note'])

        # changed
        self.assertEqual(RsvpResponse.TENTATIVE, details['future_repetitions'][2]['rsvp_response'])
        self.assertEqual(RsvpResponse.IN_PERSON, details['future_repetitions'][2]['rsvp_accept_type'])
        self.assertEqual('Sorry guys', details['future_repetitions'][2]['rsvp_note'])

    def get_meeting(self, meeting_id):
        return self.acc_get('api-meetings-meetings-detail', pk=meeting_id).json()

    def test_meeting_attendance(self):
        self.login_admin()

        committee = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        committee.memberships.add(self.membership)
        committee.memberships.add(self.membership_admin)

        meeting_json = self._create_simple_meeting(committee=committee.id, publish=True)

        # Not allowed for future meetings
        meeting_id = meeting_json['id']
        self.acc_post_json('api-meetings-meetings-attendance', pk=meeting_id, json_data={
            'user': self.user.id,
            'present': MeetingAttendance.PRESENT_TYPES.attended_in_person
        }, assert_status_code=403)

        Meeting.objects.filter(pk=meeting_id).update(start=timezone.now() - timedelta(hours=2))

        meeting_json = self.get_meeting(meeting_id)
        self.assertEqual(None, meeting_json['details']['rsvp_responses'][0]['present'])
        self.assertEqual(None, meeting_json['details']['rsvp_responses'][1]['present'])

        self.acc_post_json('api-meetings-meetings-attendance', pk=meeting_id, json_data={
            'user': self.user.id,
            'present': MeetingAttendance.PRESENT_TYPES.attended_in_person
        })

        meeting_json = self.get_meeting(meeting_id)
        responses = sorted(meeting_json['details']['rsvp_responses'], key=lambda r: r['user_id'] == self.user.id)  # put him first
        self.assertEqual(MeetingAttendance.PRESENT_TYPES.attended_in_person, responses[0]['present'])
        self.assertEqual(None, responses[1]['present'])

    def test_meeting_documents(self):
        self.login_admin()

        document = self.acc_post_json('api-documents-documents-list', {
            'body': base64_encode('test document')[0],
            'name': 'The file.docx',
            'type': Document.BOARD_BOOK,
            'folder': None,
        }).json()

        meeting_json = self.acc_post_json('api-meetings-meetings-list', {
            'start': (now().replace(tzinfo=pytz.utc, hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat(),
            'end': (now().replace(tzinfo=pytz.utc, hour=13, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat(),
            'name': 'Test meeting',
            'description': 'describe it! Now.',
            'location': 'in memory',
            'committee': None,
            'documents': [document['id']],
            'extra_members': [],
        }).json()

        details = self.acc_get('api-meetings-meetings-detail', pk=meeting_json['id']).json()

        self.assertTrue(details['board_book'])
        document = self.client.get(details['board_book']['download_url'])
        self.assertEqual('test document', document.content)

    def test_calendar_data(self):
        self.login_admin()
        Meeting.objects.all().delete()

        meeting1 = self._create_simple_meeting()
        meeting2 = self._create_simple_meeting()

        m1 = Meeting.objects.get(pk=meeting1['id'])
        m1.repeat_max_count = 10
        m1.repeat_type = Meeting.REPEAT_TYPES.every_month
        m1.repeat_interval = 1
        m1.publish()
        m1.save()

        m2 = Meeting.objects.get(pk=meeting2['id'])
        m2.start += relativedelta(months=1)
        m2.end += relativedelta(months=1)
        m2.publish()
        m2.save()

        data = self.acc_get('api-meetings-meetings-calendar-data').json()
        self.assertEqual(11, len(data))  # 10 x m1 + m2
        self.assertEqual({m1.id, m2.id}, {m['id'] for m in data})

        data = self.acc_get('api-meetings-meetings-calendar-data', data={'month': m1.start.strftime('%Y-%m')}).json()
        self.assertEqual(1, len(data))  # m1 only
        self.assertEqual({m1.id}, {m['id'] for m in data})

        data = self.acc_get('api-meetings-meetings-calendar-data', data={'month': m2.start.strftime('%Y-%m')}).json()
        self.assertEqual(2, len(data))  # m1 repetition + m2
        self.assertEqual({m1.id, m2.id}, {m['id'] for m in data})

        data = self.acc_get('api-meetings-meetings-calendar-data', data={'from': m2.start.strftime('%Y-%m-%d'), 'to': m2.start.strftime('%Y-%m-%d')}).json()
        self.assertEqual(1, len(data))  # m1 repetition + m2
        self.assertEqual({m2.id}, {m['id'] for m in data})

    def _create_simple_meeting(self, committee=None, extra_memberships=None, publish=False):
        meeting_json = self.acc_post_json('api-meetings-meetings-list', {
            'start': (now().replace(tzinfo=pytz.utc, hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat(),
            'end': (now().replace(tzinfo=pytz.utc, hour=13, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat(),
            'name': 'Test meeting',
            'description': 'describe it! Now.',
            'location': 'in memory',
            'committee': committee,
            'extra_members': [self.membership.id] if extra_memberships is None else extra_memberships,
        }).json()

        if publish:
            self.acc_post_json('api-meetings-meetings-publish', json_data={}, pk=meeting_json['id'], assert_status_code=200)

        meeting_json = self.get_meeting(meeting_json['id'])

        return meeting_json
