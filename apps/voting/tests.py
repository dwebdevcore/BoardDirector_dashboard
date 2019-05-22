# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

from django.core import mail
from django.urls.base import reverse
from django.utils.functional import partition
from django.utils.timezone import now

from accounts.factories import AccountFactory
from committees.factories import CommitteeFactory
from common.api.exception_handler import WRONG_REQUEST
from common.utils import AccJsonRequestsTestCase
from profiles.factories import UserFactory
from profiles.models import Membership
from voting.models import VotingQuestion, Voting, VoterAnswer, VotingQuestionAnswer, VotingVoter


class VotingTests(AccJsonRequestsTestCase):
    fixtures = ['initial_data']

    def setUp(self):
        self.create_init_data()
        self.login_admin()

    def test_crud(self):
        resp = self.acc_get('api-voting-votings-list')
        self.assertEqual(0, len(resp.json()['results']))

        # Create voting
        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'start_time': (now() + timedelta(days=1)).isoformat(),
            'end_time': now().isoformat(),  # Wrong period
            'state': 0,
            'is_anonymous': False
        }, assert_status_code=400)
        self.assertEqual({'non_field_errors': ['Start time must be before end time'],
                          'detail': WRONG_REQUEST}, resp.json())

        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'description': 'Some description here',
            'start_time': now().isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'state': 0,
            'is_anonymous': False
        })
        id = resp.json()['id']

        # Check it's visible and list and details
        resp = self.acc_get('api-voting-votings-list')
        self.assertEqual(1, len(resp.json()['results']))

        resp = self.acc_get('api-voting-votings-detail', pk=id)
        self.assertEqual('New voting', resp.json()['name'])
        self.assertEqual('Some description here', resp.json()['description'])
        self.assertEqual([], resp.json()['questions'])
        self.assertEqual([], resp.json()['voters'])

        resp = self.acc_put_json('api-voting-votings-detail', pk=id, json_data={
            'name': 'New name',
            'start_time': '2000-01-01T00:00:00Z',
            'end_time': '2000-01-02T00:00:00Z',
            'state': 0,
            'is_anonymous': True
        })

        resp = self.acc_get('api-voting-votings-detail', pk=id)
        self.assertEqual('New name', resp.json()['name'])
        self.assertEqual('2000-01-01T00:00:00Z', resp.json()['start_time'])
        self.assertEqual('2000-01-02T00:00:00Z', resp.json()['end_time'])
        self.assertEqual(True, resp.json()['is_anonymous'])

        # ----
        # Check access
        # ----
        account2 = AccountFactory()
        resp = self.acc_get('api-voting-votings-list', account_url=account2.url, assert_status_code=403)

        # Member access
        self.login_member()
        self.acc_get('api-voting-votings-list', assert_status_code=200)  # Members can view list
        self.acc_get('api-voting-available-votings-list')  # And also available votings

        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'start_time': now().isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'state': 0,
            'is_anonymous': False
        }, assert_status_code=403)

    def test_question_work(self):
        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'start_time': now().isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'state': 0,
            'is_anonymous': False
        })

        voting_id = resp.json()['id']

        # Check required fields
        resp = self.acc_post_json('api-voting-questions-list', voting=voting_id, json_data={}, assert_status_code=400)
        self.assertEqual({
            'question': ['This field is required.'],
            'question_type': ['This field is required.'],
            'detail': WRONG_REQUEST
        }, resp.json())

        # Create a question simple yes/no question
        self.acc_post_json('api-voting-questions-list', voting=voting_id, json_data={
            'question_type': VotingQuestion.TYPE_YES_NO,
            'question': 'To be or not to be?',
            'description': 'Yeah, and some description!',
        })

        resp = self.acc_get('api-voting-votings-detail', pk=voting_id)
        question_id = resp.json()['questions'][0]['id']
        self.assertEqual(1, len(resp.json()['questions']))
        self.assertEqual('To be or not to be?', resp.json()['questions'][0]['question'])
        self.assertEqual('Yeah, and some description!', resp.json()['questions'][0]['description'])
        self.assertEqual(VotingQuestion.TYPE_YES_NO, resp.json()['questions'][0]['question_type'])

        # Create a for/against/abstain question
        self.acc_post_json('api-voting-questions-list', voting=voting_id, json_data={
            'question_type': VotingQuestion.TYPE_FOR_AGAINST_ABSTAIN,
            'question': 'To be or not to be (or doesn\'t matter)?',
        })

        resp = self.acc_get('api-voting-votings-detail', pk=voting_id)
        question_id = resp.json()['questions'][1]['id']
        self.assertEqual(2, len(resp.json()['questions']))
        self.assertEqual('To be or not to be (or doesn\'t matter)?', resp.json()['questions'][1]['question'])
        self.assertEqual(VotingQuestion.TYPE_FOR_AGAINST_ABSTAIN, resp.json()['questions'][1]['question_type'])

        # Change question & validation
        resp = self.acc_put_json('api-voting-questions-detail', voting=voting_id, pk=question_id, json_data={
            'question_type': VotingQuestion.TYPE_MULTIPLE_SELECT,
            'question': 'Something?',
        }, assert_status_code=400)
        self.assertEqual({'non_field_errors': ['Single-select/Multiple-select questions must have at least one answer'],
                          'detail': WRONG_REQUEST}, resp.json())

        resp = self.acc_put_json('api-voting-questions-detail', voting=voting_id, pk=question_id, json_data={
            'question_type': VotingQuestion.TYPE_ELECTION,
            'question': 'Something?',
        }, assert_status_code=400)
        self.assertEqual({'non_field_errors': ['Elections must have at least one candidate'],
                          'detail': WRONG_REQUEST}, resp.json())

        resp = self.acc_put_json('api-voting-questions-detail', voting=voting_id, pk=question_id, json_data={
            'question_type': VotingQuestion.TYPE_YES_NO,
            'question': 'Something?',
        })
        self.assertEqual('Something?', resp.json()['question'])

        # Answers manipulation
        resp = self.acc_post_json('api-voting-questions-list', voting=voting_id, json_data={
            'question_type': VotingQuestion.TYPE_SINGLE_SELECT,
            'question': 'How are you?',
            'answers': [
                {'answer': 'Fine'},
                {'answer': 'So so'},
            ]
        })
        question = resp.json()
        self.assertEqual(2, len(question['answers']))
        self.assertTrue(question['answers'][0]['id'])

        # Modify answers section
        del question['answers'][1]
        question['answers'].append({'answer': 'Very fine!'})

        resp = self.acc_put_json('api-voting-questions-detail', voting=voting_id, pk=question['id'], json_data=question)
        changed_question = resp.json()
        self.assertEqual(2, len(changed_question['answers']))
        self.assertEqual(['Fine', 'Very fine!'], [a['answer'] for a in changed_question['answers']])

        # Verify Candidates manipulation
        admin_membership = self.admin.get_membership(self.account)
        user_membership = self.user.get_membership(self.account)
        resp = self.acc_post_json('api-voting-questions-list', voting=voting_id, json_data={
            'question_type': VotingQuestion.TYPE_ELECTION,
            'question': 'Who is next?',
            'candidates': [
                {'membership': admin_membership.id, 'first_name': admin_membership.first_name, 'last_name': admin_membership.last_name},
                {'membership': user_membership.id, 'first_name': user_membership.last_name, 'last_name': user_membership.last_name},
            ]
        })
        election = resp.json()
        self.assertEqual([admin_membership.id, user_membership.id], [v['membership'] for v in election['candidates']])

        del election['candidates'][0]
        # Change order of candidates
        election['candidates'].append({'membership': admin_membership.id, 'first_name': admin_membership.first_name, 'last_name': admin_membership.last_name})
        resp = self.acc_put_json('api-voting-questions-detail', voting=voting_id, pk=election['id'], json_data=election)
        self.assertEqual([user_membership.id, admin_membership.id], [v['membership'] for v in resp.json()['candidates']])

    def test_voters(self):
        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'start_time': now().isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'state': 0,
            'is_anonymous': False
        })

        voting_id = resp.json()['id']
        self.assertEqual(0, len(resp.json()['voters']))

        # Check validation
        resp = self.acc_post_json('api-voting-voters-add-members', voting=voting_id, json_data={}, assert_status_code=400)
        self.assertEqual({'weight': ['This field is required.'], 'detail': WRONG_REQUEST}, resp.json())

        resp = self.acc_post_json('api-voting-voters-add-members', voting=voting_id, json_data={'weight': 1}, assert_status_code=400)
        self.assertEqual({'non_field_errors': ['Either all members or committee or members is required.'], 'detail': WRONG_REQUEST}, resp.json())

        resp = self.acc_post_json('api-voting-voters-add-members', voting=voting_id, json_data={
            'memberships': [self.membership_admin.id],
            'weight': 0,
        }, assert_status_code=400)
        self.assertEqual({'weight': ['Ensure this value is greater than or equal to 1.'], 'detail': WRONG_REQUEST}, resp.json())

        resp = self.acc_post_json('api-voting-voters-add-members', voting=voting_id, json_data={
            'memberships': [self.membership_admin.id],
            'weight': 1,
        })
        resp = self.acc_get('api-voting-votings-detail', pk=voting_id)
        voters = resp.json()['voters']
        voter = voters[0]
        self.assertEqual(1, len(voters))

        resp = self.acc_put_json('api-voting-voters-detail', voting=voting_id, pk=voter['id'], json_data={
            'weight': 10,  # Only weight can be updated (and names actually)
        })
        voter = resp.json()

        self.assertEqual(10, voter['weight'])

        # Delete it
        self.acc_delete('api-voting-voters-detail', voting=voting_id, pk=voter['id'])

        resp = self.acc_get('api-voting-votings-detail', pk=voting_id)
        self.assertEqual(0, len(resp.json()['voters']))

        # Check security: adding membership from other account
        self.init_second_account()
        resp = self.acc_post_json('api-voting-voters-add-members', voting=voting_id, json_data={
            'memberships': [self.membership2.id],
            'weight': 1,
        }, assert_status_code=400)
        self.assertEqual({'memberships': [['Invalid pk "%d" - object does not exist.' % self.membership2.id]], 'detail': WRONG_REQUEST}, resp.json())

    def test_publishing(self):
        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'start_time': now().isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'state': 1,  # Must be ignored
            'is_anonymous': False
        })

        voting = resp.json()
        self.assertEqual(0, voting['state'])
        self.assertTrue(resp.json()['can_edit'])

        # Check validation
        resp = self.acc_post_json('api-voting-votings-publish', pk=voting['id'], json_data={}, assert_status_code=400)
        self.assertEqual({'voters': ["Voting can't be published without voters"],
                          'detail': WRONG_REQUEST}, resp.json())

        # Create question & voter
        self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'memberships': [self.membership_admin.id],
            'weight': 1,
        })

        resp = self.acc_post_json('api-voting-votings-publish', pk=voting['id'], json_data={}, assert_status_code=400)
        self.assertEqual({'questions': ["Voting can't be published without questions"],
                          'detail': WRONG_REQUEST}, resp.json())

        self.acc_post_json('api-voting-questions-list', voting=voting['id'], json_data={
            'question_type': VotingQuestion.TYPE_YES_NO,
            'question': 'To be or not to be?',
        })

        # Finally publish the thing
        resp = self.acc_post_json('api-voting-votings-publish', pk=voting['id'], json_data={}, assert_status_code=200)
        self.assertEqual(Voting.STATE_PUBLISHED, resp.json()['state'])

        resp = self.acc_get('api-voting-votings-detail', pk=voting['id'])
        self.assertEqual(Voting.STATE_PUBLISHED, resp.json()['state'])
        voting = resp.json()
        self.assertFalse(voting['can_edit'])

        resp = self.acc_put_json('api-voting-questions-detail', voting=voting['id'], pk=voting['questions'][0]['id'], json_data={
            'question_type': VotingQuestion.TYPE_YES_NO,
            'question': 'To be or not to be? CHANGED!',
        }, assert_status_code=403)
        self.assertEqual({'detail': "Can't edit if Voting is already published"}, resp.json())

    def test_available_info(self):
        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'start_time': now().isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'is_anonymous': False
        })

        voting = resp.json()

        self.acc_post_json('api-voting-questions-list', voting=voting['id'], json_data={
            'question_type': VotingQuestion.TYPE_YES_NO,
            'question': 'To be or not to be?',
        })

        # Check short info in list
        resp = self.acc_get('api-voting-votings-list', request_kwargs={'data': {'all': 1}})
        self.assertFalse('questions' in resp.json()['results'][0])

        resp = self.acc_get('api-voting-votings-detail', pk=voting['id'])
        self.assertTrue('questions' in resp.json())

    def test_available_votings(self):
        voting = self._create_voting(voters=[self.membership_admin.id])
        self._publish(voting)

        self.login_member()
        resp = self.acc_get('api-voting-available-votings-list')
        self.assertEqual(0, len(resp.json()['results']))  # Member is not voter

        self.login_admin()
        voting = self._create_voting(voters=[self.membership_admin.id, self.membership.id])
        self._publish(voting)
        resp = self.acc_get('api-voting-available-votings-list')
        self.assertEqual(2, len(resp.json()['results']))  # Admin has 2 to attend

        self.login_member()
        resp = self.acc_get('api-voting-available-votings-list')
        self.assertEqual(1, len(resp.json()['results']))  # Member has 1 voting

        # Test access to other account
        self.init_second_account()
        self.login_admin2()
        other_voting = self._create_voting(voters=[self.membership_admin2.id], account_url=self.account2.url)
        self.acc_post_json('api-voting-votings-publish', pk=other_voting['id'], json_data={}, assert_status_code=200, account_url=self.account2.url)
        resp = self.acc_get('api-voting-available-votings-list', account_url=self.account2.url)
        self.assertEqual(1, len(resp.json()['results']))  # Sees it's own voting
        self.assertEqual(other_voting['id'], resp.json()['results'][0]['id'])

        self.login_admin()
        resp = self.acc_get('api-voting-available-votings-list')
        self.assertEqual(2, len(resp.json()['results']))  # Admin of first board still has 2 votings to attend
        self.assertFalse(next((r for r in resp.json()['results'] if r['id'] == other_voting['id']), False))

    def test_available_voting_process(self):
        wrong_voting = self._create_voting(voters=[self.membership_admin.id, self.membership.id])

        wrong_election = self._create_question(wrong_voting, {
            'question_type': VotingQuestion.TYPE_ELECTION,
            'question': 'Guess who is admin here?',
            'candidates': [{'user': self.membership_admin.id},
                           {'user': self.membership.id}]
        })

        wrong_single_select = self._create_question(wrong_voting, {
            'question_type': VotingQuestion.TYPE_SINGLE_SELECT,
            'question': 'Which is fruit?',
            'answers': [{'answer': 'Apple'}, {'answer': 'Window'}]
        })

        wrong_multi_select = self._create_question(wrong_voting, {
            'question_type': VotingQuestion.TYPE_MULTIPLE_SELECT,
            'question': 'Vote for UI framework?',
            'answers': [{'answer': 'Angular 1.x'}, {'answer': 'Angular 2.x'}, {'answer': 'VueJS'}, {'answer': 'React'}]
        })

        self._publish(wrong_voting)

        voting = self._create_voting(voters=[self.membership_admin.id, self.membership.id])

        yes_no_id = voting['questions'][0]['id']

        faa_id = self._create_question(voting, {
            'question_type': VotingQuestion.TYPE_FOR_AGAINST_ABSTAIN,
            'question': 'To be or not to be or abstain?',
        })['id']

        election = self._create_question(voting, {
            'question_type': VotingQuestion.TYPE_ELECTION,
            'question': 'Guess who is admin here?',
            'candidates': [{'user': self.membership_admin.id},
                           {'user': self.membership.id}]
        })

        single_select = self._create_question(voting, {
            'question_type': VotingQuestion.TYPE_SINGLE_SELECT,
            'question': 'Which is fruit?',
            'answers': [{'answer': 'Apple'}, {'answer': 'Window'}]
        })

        multi_select = self._create_question(voting, {
            'question_type': VotingQuestion.TYPE_MULTIPLE_SELECT,
            'question': 'Vote for UI framework?',
            'answers': [{'answer': 'Angular 1.x'}, {'answer': 'Angular 2.x'}, {'answer': 'VueJS'}, {'answer': 'React'}]
        })

        self._publish(voting)

        resp = self.acc_get('api-voting-available-votings-list')
        self.assertEqual(2, len(resp.json()['results']))  # Sees it's own voting
        voter_key = next(v['voter_key'] for v in resp.json()['results'] if v['id'] == voting['id'])
        self.assertTrue(voter_key)

        resp = self.acc_get('api-voting-vote-voting-detail', pk=voter_key)
        detail = resp.json()
        self.assertEqual(voting['id'], detail['id'])
        self.assertEqual({}, detail['answers'])  # no answers yet
        self.assertEqual(5, len(detail['questions']))

        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': yes_no_id,
            'yes_no': True,
            'vote_note': 'Only this time!',
        }).json()

        self.assertEqual(True, detail['answers'][str(yes_no_id)]['yes_no'])
        self.assertEqual('Only this time!', detail['answers'][str(yes_no_id)]['vote_note'])

        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': yes_no_id,
            'yes_no': None
        }, assert_status_code=400).json()

        self.assertEqual({'yes_no': ['This field is required for yes/no question'],
                          'detail': WRONG_REQUEST}, error)

        # Can change opinion
        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': detail['questions'][0]['id'],
            'yes_no': False
        }).json()

        self.assertEqual(False, detail['answers'][str(yes_no_id)]['yes_no'])
        self.assertEqual(1, len(detail['answers']))

        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': faa_id,
        }, assert_status_code=400).json()

        self.assertEqual({'for_against_abstain': ['This field is required for for/against/abstain question'],
                          'detail': WRONG_REQUEST}, error)

        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': faa_id,
            'for_against_abstain': VoterAnswer.ANSWER_FOR,
        }).json()

        self.assertEqual(VoterAnswer.ANSWER_FOR, detail['answers'][str(faa_id)]['for_against_abstain'])

        # Can change opinion
        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': faa_id,
            'for_against_abstain': VoterAnswer.ANSWER_AGAINST,
        }).json()

        self.assertEqual(VoterAnswer.ANSWER_AGAINST, detail['answers'][str(faa_id)]['for_against_abstain'])
        self.assertEqual(2, len(detail['answers']))

        # Elect someone wrong
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': election['id'],
            'candidate': 42 * 42 * 42 * 42
        }, assert_status_code=400).json()
        self.assertEqual({'candidate': ['Invalid pk "3111696" - object does not exist.'],
                          'detail': WRONG_REQUEST}, error)

        # Just try not to elect anyone
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': election['id'],
        }, assert_status_code=400).json()
        self.assertEqual({'candidate': ['This field is required for election.'],
                          'detail': WRONG_REQUEST}, error)

        # Elect someone not so wrong but from other voting
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': election['id'],
            'candidate': wrong_election['candidates'][0]['id']
        }, assert_status_code=400).json()
        self.assertEqual({'candidate': ['Wrong candidate for this election.'],
                          'detail': WRONG_REQUEST}, error)

        # Elect someone
        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': election['id'],
            'candidate': election['candidates'][0]['id']
        }).json()
        self.assertEqual(election['candidates'][0]['id'], detail['answers'][str(election['id'])]['candidate'])

        # Elect someone: change your mind
        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': election['id'],
            'candidate': election['candidates'][1]['id']
        }).json()
        self.assertEqual(election['candidates'][1]['id'], detail['answers'][str(election['id'])]['candidate'])

        # Select some wrong fruit
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': single_select['id'],
            'answers': [wrong_single_select['answers'][0]['id']]
        }, assert_status_code=400).json()
        self.assertEqual({'answers': {'0': ['Wrong answer for this question.']},
                          'detail': WRONG_REQUEST}, error)

        # Select too many fruits (single select)
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': single_select['id'],
            'answers': [single_select['answers'][0]['id'], single_select['answers'][1]['id']]
        }, assert_status_code=400).json()
        self.assertEqual({'answers': ['Too many answers selected for single select'],
                          'detail': WRONG_REQUEST}, error)

        # Select too less fruits (single select)
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': single_select['id'],
            'answers': []
        }, assert_status_code=400).json()
        self.assertEqual({'answers': ['This field is required for single select.'],
                          'detail': WRONG_REQUEST}, error)

        # Select some good fruit
        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': single_select['id'],
            'answers': [single_select['answers'][0]['id']]
        }).json()
        self.assertEqual([single_select['answers'][0]['id']], detail['answers'][str(single_select['id'])]['answers'])

        # Select some good fruit: Change your mind
        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': single_select['id'],
            'answers': [single_select['answers'][1]['id']]
        }).json()
        self.assertEqual([single_select['answers'][1]['id']], detail['answers'][str(single_select['id'])]['answers'])

        # Select some wrong Framework (multiple)
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': multi_select['id'],
            'answers': [multi_select['answers'][0]['id'], wrong_multi_select['answers'][0]['id']]
        }, assert_status_code=400).json()
        self.assertEqual({'answers': {'1': ['Wrong answer for this question.']},
                          'detail': WRONG_REQUEST}, error)

        # Select some no frameworks (multiple)
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': multi_select['id'],
            'answers': [multi_select['answers'][0]['id'], wrong_multi_select['answers'][0]['id']]
        }, assert_status_code=400).json()
        self.assertEqual({'answers': {'1': ['Wrong answer for this question.']},
                          'detail': WRONG_REQUEST}, error)

        # Select some good frameworks
        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': multi_select['id'],
            'answers': [multi_select['answers'][1]['id'], multi_select['answers'][2]['id']]
        }).json()
        # Set comparison as order isn't important
        self.assertEqual({multi_select['answers'][1]['id'], multi_select['answers'][2]['id']}, set(detail['answers'][str(multi_select['id'])]['answers']))

        # change to other selection of frameworks
        detail = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': multi_select['id'],
            'answers': [multi_select['answers'][3]['id'], multi_select['answers'][2]['id']]
        }).json()

        self.assertEqual({multi_select['answers'][2]['id'], multi_select['answers'][3]['id']}, set(detail['answers'][str(multi_select['id'])]['answers']))

        # Let's break: put our candidate in other Voting (i.e. wrong voter_key)
        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': wrong_election['id'],
            'candidate': wrong_election['candidates'][0]['id'],
        }, assert_status_code=403).json()
        self.assertEqual({'non_field_errors': ["Question doesn't belong to this voting."]}, error)

        # Check ip is filled somehow
        for answer in VoterAnswer.objects.filter(voter__voter_key=voter_key):
            self.assertTrue(answer.voter_ip_address)

    def test_vote_voting_not_in_progress_should_fail(self):
        voting = self._create_voting(voters=[self.membership_admin.id])
        self.acc_put_json('api-voting-votings-detail', pk=voting['id'], json_data={
            'name': 'New voting',
            'start_time': (now() + timedelta(hours=2)).isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'is_anonymous': False
        })

        self._publish(voting)

        resp = self.acc_get('api-voting-available-votings-list')
        voting_result = resp.json()['results'][0]
        voter_key = voting_result['voter_key']
        self.assertTrue(voter_key)
        self.assertFalse(voting_result['is_in_progress'])

        error = self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': voting['questions'][0]['id'],
            'yes_no': False
        }, assert_status_code=403).json()
        self.assertEqual({'non_field_errors': ['Voting is not in progress now.']}, error)

    def test_voting_done(self):
        voting = self._create_voting(voters=[self.membership_admin.id, self.membership.id])
        self._publish(voting)

        resp = self.acc_get('api-voting-available-votings-list')
        voter_key = resp.json()['results'][0]['voter_key']
        self.assertTrue(voter_key)

        resp = self.acc_post_json('api-voting-vote-voting-mark-done', pk=voter_key, assert_status_code=400, json_data={})
        self.assertEqual({'non_field_errors': ["Voting can't be marked done until all questions are answered."]}, resp.json())

        voting = self.acc_get('api-voting-vote-voting-detail', pk=voter_key).json()
        self.assertFalse(voting['voting_done'])

        self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': voting['questions'][0]['id'],
            'yes_no': True
        })

        self.acc_post_json('api-voting-vote-voting-mark-done', pk=voter_key, assert_status_code=200, json_data={})
        voting = self.acc_get('api-voting-vote-voting-detail', pk=voter_key).json()
        self.assertTrue(voting['voting_done'])

    def test_results(self):
        # Prepare data:
        voting = self._create_voting(voters=[self.membership.id])
        self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'memberships': [self.membership_admin.id],
            'weight': 3,  # Make it of different weight
        })

        # Add third user
        user3 = UserFactory(accounts=[self.account])
        membership3 = user3.get_membership(self.account)
        self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'memberships': [membership3.id],
            'weight': 1,
        })

        # Add questions
        yes_no_id = voting['questions'][0]['id']

        faa_id = self._create_question(voting, {
            'question_type': VotingQuestion.TYPE_FOR_AGAINST_ABSTAIN,
            'question': 'To be or not to be or abstain?',
        })['id']

        election = self._create_question(voting, {
            'question_type': VotingQuestion.TYPE_ELECTION,
            'question': 'Guess who is admin here?',
            'candidates': [{'user': self.membership_admin.id},
                           {'user': self.membership.id}]
        })

        single_select = self._create_question(voting, {
            'question_type': VotingQuestion.TYPE_SINGLE_SELECT,
            'question': 'Which is fruit?',
            'answers': [{'answer': 'Apple'}, {'answer': 'Window'}]
        })

        multi_select = self._create_question(voting, {
            'question_type': VotingQuestion.TYPE_MULTIPLE_SELECT,
            'question': 'Vote for UI framework?',
            'answers': [{'answer': 'Angular 1.x'}, {'answer': 'Angular 2.x'}, {'answer': 'VueJS'}, {'answer': 'React'}]
        })
        self._publish(voting)
        voting = self.acc_get('api-voting-votings-detail', pk=voting['id']).json()

        # Check empty result
        self.assertEqual(0, voting['result']['done'])

        self.assertEqual(3, len(voting['voters']), msg="Wrong voters list (not 3 voters): {0}".format(voting['voters']))
        user_voter, admin_voter, user3_voter = [v['id'] for v in voting['voters']]

        # Voting process... directly to make it smaller and quicker
        def do_answer(voter_id, question_id, yes_no=None, answers_ids=None, candidate_id=None, for_against_abstain=None, vote_note=None):
            a = VoterAnswer.objects.create(
                voter_id=voter_id,
                question_id=question_id,
                voter_ip_address='192.168.0.1',
                yes_no=yes_no,
                for_against_abstain=for_against_abstain,
                vote_note=vote_note,
                candidate_id=candidate_id)
            for answer_id in (answers_ids or []):
                a.answers.add(VotingQuestionAnswer.objects.get(pk=answer_id))

        def done(voter_id):
            VotingVoter.objects.filter(id=voter_id).update(voting_done=True)

        do_answer(admin_voter, yes_no_id, yes_no=True, vote_note="Admin's voice.")
        do_answer(admin_voter, faa_id, for_against_abstain=VoterAnswer.ANSWER_FOR)
        do_answer(admin_voter, single_select['id'], answers_ids=[single_select['answers'][0]['id']])
        do_answer(admin_voter, multi_select['id'], answers_ids=[multi_select['answers'][0]['id'], multi_select['answers'][1]['id']])
        do_answer(admin_voter, election['id'], candidate_id=election['candidates'][0]['id'])
        done(admin_voter)

        do_answer(user_voter, yes_no_id, yes_no=False, vote_note="This is user's note.")
        do_answer(user_voter, faa_id, for_against_abstain=VoterAnswer.ANSWER_AGAINST)
        do_answer(user_voter, single_select['id'], answers_ids=[single_select['answers'][1]['id']])
        do_answer(user_voter, multi_select['id'], answers_ids=[multi_select['answers'][2]['id'], multi_select['answers'][1]['id']])
        do_answer(user_voter, election['id'], candidate_id=election['candidates'][1]['id'])
        done(user_voter)

        do_answer(user3_voter, yes_no_id, yes_no=False)
        do_answer(user3_voter, faa_id, for_against_abstain=VoterAnswer.ANSWER_ABSTAIN)
        do_answer(user3_voter, single_select['id'], answers_ids=[single_select['answers'][1]['id']])
        # User didn't finish, don't count him

        voting = self.acc_get('api-voting-votings-detail', pk=voting['id']).json()
        result = voting['result']
        self.assertEqual(True, voting['voters'][0]['voting_done'])
        self.assertEqual(False, voting['voters'][2]['voting_done'])  # See below - shouldn't be available for anonymous

        self.assertEqual(3, result['total'])
        self.assertEqual(2, result['done'])
        self.assertEqual(4, result['done_weight'])
        self.assertEqual(5, len(result['questions']))

        yes_no_result = result['questions'][str(yes_no_id)]
        self.assertEqual(False, yes_no_result['yes'])  # Results aren't available until all voters are done

        # Finish voting for user3
        do_answer(user3_voter, multi_select['id'], answers_ids=[multi_select['answers'][2]['id'], multi_select['answers'][1]['id']])
        do_answer(user3_voter, election['id'], candidate_id=election['candidates'][1]['id'])
        done(user3_voter)

        voting = self.acc_get('api-voting-votings-detail', pk=voting['id']).json()
        result = voting['result']

        self.assertTrue(result['has_answers'])

        yes_no_result = result['questions'][str(yes_no_id)]
        self.assertEqual(3, yes_no_result['yes']['weight'])
        self.assertEqual(2, yes_no_result['no']['weight'])
        self.assertEqual(60, yes_no_result['yes']['percent'])
        self.assertEqual(1, len(yes_no_result['yes']['voters']))
        self.assertEqual(admin_voter, yes_no_result['yes']['voters'][0]['voter_id'])
        self.assertEqual("Admin's voice.", yes_no_result['yes']['voters'][0]['vote_note'])
        self.assertEqual('192.168.0.1', yes_no_result['yes']['voters'][0]['ip'])

        faa_result = result['questions'][str(faa_id)]
        self.assertEqual(3, faa_result['for']['weight'])
        self.assertEqual(1, faa_result['against']['weight'])
        self.assertEqual(1, faa_result['abstain']['weight'])

        election_result = result['questions'][str(election['id'])]
        self.assertEqual(2, len(election_result))
        self.assertEqual(3, election_result[str(election['candidates'][0]['id'])]['weight'])
        self.assertEqual(2, election_result[str(election['candidates'][1]['id'])]['weight'])

        multi_result = result['questions'][str(multi_select['id'])]
        self.assertEqual(4, len(multi_result))
        self.assertEqual(3, multi_result[str(multi_select['answers'][0]['id'])]['weight'])
        self.assertEqual(5, multi_result[str(multi_select['answers'][1]['id'])]['weight'])
        self.assertEqual(2, multi_result[str(multi_select['answers'][2]['id'])]['weight'])
        self.assertEqual(0, multi_result[str(multi_select['answers'][3]['id'])]['weight'])  # Include answer even if no one selected it

        single_result = result['questions'][str(single_select['id'])]
        self.assertEqual(2, len(single_result))
        self.assertEqual(3, single_result[str(single_select['answers'][0]['id'])]['weight'])
        self.assertEqual(2, single_result[str(single_select['answers'][1]['id'])]['weight'])

        # Check anonymous output
        Voting.objects.filter(pk=voting['id']).update(is_anonymous=True)

        voting = self.acc_get('api-voting-votings-detail', pk=voting['id']).json()
        result = voting['result']
        yes_no_result = result['questions'][str(yes_no_id)]

        self.assertEqual(3, yes_no_result['yes']['weight'])
        self.assertEqual(2, yes_no_result['no']['weight'])
        self.assertEqual(60, yes_no_result['yes']['percent'])

        self.assertEqual(1, len(yes_no_result['yes']['voters']))
        self.assertEqual("Admin's voice.", yes_no_result['yes']['voters'][0]['vote_note'])  # Only vote_note is available
        self.assertEqual(None, yes_no_result['yes']['voters'][0]['voter_id'])
        self.assertEqual(None, yes_no_result['yes']['voters'][0]['ip'])
        self.assertEqual(None, yes_no_result['yes']['voters'][0]['first_name'])

        self.assertEqual(None, voting['voters'][0]['voting_done'])
        self.assertEqual(None, voting['voters'][2]['voting_done'])  # See below - shouldn't be available for anonymous

    def test_add_committee(self):
        committee1 = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        committee2 = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        _, user1 = self.create_membership()
        _, user2 = self.create_membership()
        _, user3 = self.create_membership()
        _, user4 = self.create_membership()

        committee1.memberships.add(user1, user2)
        committee2.memberships.add(user2, user3)

        voting = self._create_voting([])
        self.assertEqual(0, len(voting['voters']))

        self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'weight': 1,
            'committees': [committee1.id]
        }, assert_status_code=201)

        voting = self._get_voting(voting)
        self.assertEqual(2, len(voting['voters']))

        # Post once more time same committee
        self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'weight': 2,
            'committees': [committee1.id]
        }, assert_status_code=201)

        voting = self._get_voting(voting)
        self.assertEqual(2, len(voting['voters']))  # Change is ignored
        self.assertEqual(1, voting['voters'][0]['weight'])

        # Post other committee
        self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'weight': 2,
            'committees': [committee2.id]
        }, assert_status_code=201)

        voting = self._get_voting(voting)
        self.assertEqual(3, len(voting['voters']))  # One user is in intersection
        self.assertEqual(2, voting['voters'][2]['weight'])

        # Check access:
        account2 = AccountFactory()
        foreign_committee = CommitteeFactory(account=account2)
        error = self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'weight': 2,
            'committees': [foreign_committee.id]
        }, assert_status_code=400).json()
        self.assertEqual({'committees': [['Invalid pk "%d" - object does not exist.' % (foreign_committee.id,)]],
                          'detail': WRONG_REQUEST}, error)

    def test_add_voters_when_create_voting(self):
        committee1 = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        committee2 = CommitteeFactory(account=self.account, chairman=self.membership_admin)
        _, user1 = self.create_membership()
        _, user2 = self.create_membership()
        _, user3 = self.create_membership()
        _, user4 = self.create_membership()
        _, guest = self.create_membership(role=Membership.ROLES.guest)

        committee1.memberships.add(user1, user2)
        committee2.memberships.add(user2, user3)

        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'start_time': now().isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'add_voters': {
                'committees': [committee1.id],
                'memberships': [user4.id],
                'all_members': ['guests'],
                'weight': 1,
            },
            'is_anonymous': False
        })
        voting = resp.json()
        voters = {v['membership'] for v in voting['voters']}
        self.assertIn(user1.id, voters)  # committee
        self.assertIn(user2.id, voters)  # committee
        self.assertIn(user4.id, voters)  # direct
        self.assertIn(guest.id, voters)  # all_members: ['guests']

    def test_add_users(self):
        existing_members, existing_guests = partition(lambda m: m.is_guest, Membership.objects.filter(account=self.account, is_active=True))

        _, user1 = self.create_membership()
        _, user2 = self.create_membership(role=Membership.ROLES.guest)
        _, user3 = self.create_membership(role=Membership.ROLES.guest, accounts__is_active=False)
        _, user4 = self.create_membership(accounts__is_active=False)

        voting = self._create_voting([])
        self.assertEqual(0, len(voting['voters']))

        self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'weight': 1,
            'all_members': ['members']
        }, assert_status_code=201)

        voting = self._get_voting(voting)
        self.assertEqual(len(existing_members) + 1, len(voting['voters']))  # One member not is_active

        self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
            'weight': 1,
            'all_members': ['guests']
        }, assert_status_code=201)

        voting = self._get_voting(voting)
        self.assertEqual(len(existing_members) + len(existing_guests) + 2, len(voting['voters']))  # One member and one guest are not is_active

    def test_send_emails(self):
        voting = self._create_voting([self.membership_admin.id, self.membership.id])
        self._publish(voting)

        self.login_member()
        resp = self.acc_get('api-voting-available-votings-list')
        voter_key = resp.json()['results'][0]['voter_key']

        url = reverse('voting:voting-vote-by-key', kwargs={'voter_key': voter_key, 'url': self.account.url})

        self.assertEqual(2, len(mail.outbox))  # For now let's not exclude sender

        member_email = mail.outbox[1]
        self.assertEqual(self.account.name + ": Voting '" + voting['name'] + "' available", member_email.subject)
        self.assertEqual([self.user.email], member_email.to)
        self.assertTrue(url in member_email.body)

        mail.outbox = []

        # Check resend by user
        self.acc_post_json('api-voting-votings-resend-email', pk=voting['id'], json_data={}, assert_status_code=403)

        self.init_second_account()

        # Check other account
        self.login_admin2()
        self.acc_post_json('api-voting-votings-resend-email', pk=voting['id'], json_data={}, assert_status_code=403)

        # Check resend
        self.login_admin()
        self.acc_post_json('api-voting-votings-resend-email', pk=voting['id'], json_data={}, assert_status_code=200)

        self.assertEqual(2, len(mail.outbox))

    def test_publish_results(self):
        voting = self._create_voting([self.membership_admin.id, self.membership.id])
        self._publish(voting)
        yes_no_id = voting['questions'][0]['id']

        resp = self.acc_get('api-voting-available-votings-list')
        voter_key = next(v['voter_key'] for v in resp.json()['results'] if v['id'] == voting['id'])
        self.assertTrue(voter_key)

        self.acc_put_json('api-voting-vote-voting-detail', pk=voter_key, json_data={
            'question': yes_no_id,
            'yes_no': True,
            'vote_note': 'Only this time!',
        }).json()
        self.acc_post_json('api-voting-vote-voting-mark-done', pk=voter_key, assert_status_code=200, json_data={})

        voting = self.acc_get('api-voting-votings-detail', pk=voting['id']).json()
        self.assertEqual(False, voting['result']['questions'][str(yes_no_id)]['yes'])

        self.login_member()
        self.acc_post_json('api-voting-votings-publish-results', pk=voting['id'], json_data={}, assert_status_code=403)

        self.login_admin()
        self.acc_post_json('api-voting-votings-publish-results', pk=voting['id'], json_data={}, assert_status_code=200).json()
        voting = self.acc_get('api-voting-votings-detail', pk=voting['id']).json()

        self.assertTrue(voting['is_result_published'])
        self.assertEqual(100, voting['result']['questions'][str(yes_no_id)]['yes']['percent'])

    def test_delete_voting(self):
        self.login_admin()
        voting = self._create_voting([self.membership.id, self.membership_admin.id])
        self.acc_delete('api-voting-votings-detail', pk=voting['id'])

        self.assertFalse(Voting.objects.filter(pk=voting['id']).exists())

        voting = self._create_voting([self.membership.id, self.membership_admin.id])
        self._publish(voting)

        VoterAnswer.objects.create(question_id=voting['questions'][0]['id'],
                                   voter_id=voting['voters'][0]['id'],
                                   voter_ip_address='127.0.0.1',
                                   yes_no=True)

        delete = self.acc_delete('api-voting-votings-detail', pk=voting['id'], assert_status_code=403).json()
        self.assertEqual({'detail': "Can't delete voting with votes"}, delete)

        # Check that member can't delete
        voting = self._create_voting([self.membership.id, self.membership_admin.id])

        self.login_member()
        delete = self.acc_delete('api-voting-votings-detail', pk=voting['id'], assert_status_code=403).json()
        self.assertEqual({'detail': "You do not have permission to perform this action."}, delete)

    def _get_voting(self, voting, account_url=None):
        if isinstance(voting, dict):
            voting = voting['id']
        return self.acc_get('api-voting-votings-detail', pk=voting, account_url=account_url).json()

    def _create_voting(self, voters, account_url=None):
        resp = self.acc_post_json('api-voting-votings-list', {
            'name': 'New voting',
            'start_time': now().isoformat(),
            'end_time': (now() + timedelta(days=1)).isoformat(),
            'is_anonymous': False
        }, account_url=account_url)
        voting = resp.json()

        if voters:
            self.acc_post_json('api-voting-voters-add-members', voting=voting['id'], json_data={
                'memberships': voters,
                'weight': 1,
            }, account_url=account_url)

        self._create_question(voting, account_url=account_url, question={
            'question_type': VotingQuestion.TYPE_YES_NO,
            'question': 'To be or not to be?',
        })
        return self.acc_get('api-voting-votings-detail', pk=voting['id'], account_url=account_url).json()

    def _create_question(self, voting, question, account_url=None):
        return self.acc_post_json('api-voting-questions-list', voting=voting['id'], json_data=question, account_url=account_url).json()

    def _publish(self, voting):
        self.acc_post_json('api-voting-votings-publish', pk=voting['id'], json_data={}, assert_status_code=200)
