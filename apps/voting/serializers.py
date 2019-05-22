from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.mixins import FilterSerializerByAccountMixin
from voting import models

from committees.models import Committee
from common.utils import dict_by_key
from profiles.models import Membership
from voting.models import VotingQuestion, VoterAnswer


class VotingAddMembersSerializer(FilterSerializerByAccountMixin, serializers.Serializer):
    memberships = serializers.ListSerializer(child=serializers.PrimaryKeyRelatedField(queryset=Membership.objects.all()), required=False, default=[])
    committees = serializers.ListSerializer(child=serializers.PrimaryKeyRelatedField(queryset=Committee.objects.all()), required=False, default=[])
    all_members = serializers.ListSerializer(child=serializers.ChoiceField(choices=['members', 'guests']), default=[])
    weight = serializers.IntegerField(min_value=1)

    def __init__(self, instance=None, *args, **kwargs):
        super(VotingAddMembersSerializer, self).__init__(instance, *args, **kwargs)
        self.filter_account_in_child('memberships')
        self.filter_account_in_child('committees')

    def validate(self, attrs):
        attrs = super(VotingAddMembersSerializer, self).validate(attrs)

        if not (attrs['memberships'] or attrs['committees'] or attrs['all_members']):
            raise ValidationError({'non_field_errors': [_('Either all members or committee or members is required.')]})

        return attrs


class VotingSerializer(serializers.ModelSerializer):
    add_voters = VotingAddMembersSerializer(write_only=True, required=False)

    def validate(self, attrs):
        copy = dict(attrs)
        copy.pop('add_voters', None)
        voting = models.Voting(**copy)
        voting.clean()
        return attrs

    def create(self, validated_data):
        add_voters = validated_data.pop('add_voters', None)
        voting = models.Voting(**validated_data)
        voting.save()

        if add_voters:
            add_voters_for_voting(self.context['account'], voting, add_voters)

        return voting

    def update(self, instance, validated_data):
        add_voters = validated_data.pop('add_voters', None)
        voting = super(VotingSerializer, self).update(instance, validated_data)

        if add_voters:
            add_voters_for_voting(self.context['account'], voting, add_voters)

        return voting

    class Meta:
        model = models.Voting
        fields = ['id', 'name', 'description', 'state', 'is_anonymous', 'owner', 'start_time', 'end_time', 'can_edit', 'can_publish',
                  'is_active', 'created', 'updated', 'is_in_progress', 'is_done', 'add_voters', 'is_result_published', 'is_result_visible']
        read_only_fields = ['id', 'owner', 'state', 'is_active', 'created', 'updated', 'is_in_progress', 'is_result_published',
                            'is_result_visible']  # Maybe unlock is_active later


class VotingQuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VotingQuestionAnswer
        fields = ['id', 'answer']
        read_only_fields = ['created', 'question']


class VotingQuestionCandidateSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, candidate):
        return candidate.membership and candidate.membership.avatar_url()

    class Meta:
        model = models.VotingQuestionCandidate
        fields = ['id', 'membership', 'first_name', 'last_name', 'bio', 'notes', 'created', 'question', 'avatar_url']
        read_only_fields = ['created', 'question']


class VotingQuestionSerializer(serializers.ModelSerializer):
    answers = VotingQuestionAnswerSerializer(many=True, read_only=False, required=False)
    candidates = VotingQuestionCandidateSerializer(many=True, read_only=False, required=False)

    class Meta:
        model = models.VotingQuestion
        fields = ['id', 'question', 'description', 'question_type', 'voting', 'ordering', 'answers', 'candidates']
        read_only_fields = ['id', 'voting']

    def validate(self, attrs):
        attrs = super(VotingQuestionSerializer, self).validate(attrs)
        if attrs['question_type'] in (VotingQuestion.TYPE_SINGLE_SELECT, VotingQuestion.TYPE_MULTIPLE_SELECT):
            if not len(attrs.get('answers', [])):
                raise ValidationError(_('Single-select/Multiple-select questions must have at least one answer'))
        else:
            attrs['answers'] = []

        if attrs['question_type'] == VotingQuestion.TYPE_ELECTION:
            if not len(attrs.get('candidates', [])):
                raise ValidationError(_('Elections must have at least one candidate'))
        else:
            attrs['candidates'] = []

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        answers = validated_data.pop('answers', [])
        candidates = validated_data.pop('candidates', [])

        question = super(VotingQuestionSerializer, self).create(validated_data)

        self.save_collection(answers, question.answers.all(), VotingQuestionAnswerSerializer, {'question': question})
        self.save_collection(candidates, question.candidates.all(), VotingQuestionCandidateSerializer, {'question': question})

        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        answers = validated_data.pop('answers', [])
        candidates = validated_data.pop('candidates', [])

        question = super(VotingQuestionSerializer, self).update(instance, validated_data)

        self.save_collection(answers, question.answers.all(), VotingQuestionAnswerSerializer, {'question': question})
        self.save_collection(candidates, question.candidates.all(), VotingQuestionCandidateSerializer, {'question': question})

        return question

    @staticmethod
    def save_collection(new_items, existing_items, item_serializer, save_kwargs=None):
        existing_by_id = {i.id: i for i in existing_items}
        for data in new_items:
            item_id = data.pop('id', None)
            existing = existing_by_id.pop(item_id, None)

            serializer = item_serializer(existing, data)

            data = dict(data)
            data.update(save_kwargs or {})
            if existing:
                serializer.update(existing, data)
            else:
                serializer.create(data)

        for item in existing_by_id.values():
            item.delete()  # Remove old which aren't in new dict


class VotingVoterSerializer(serializers.ModelSerializer):
    voting_done = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    def get_voting_done(self, voter):
        if voter.voting.is_anonymous:
            return None
        else:
            return voter.voting_done

    def get_avatar_url(self, voter):
        return voter.membership and voter.membership.avatar_url()

    class Meta:
        model = models.VotingVoter
        fields = ['id', 'membership', 'weight', 'voting', 'voting_done', 'avatar_url', 'first_name', 'last_name', 'display_first_name', 'display_last_name']
        read_only_fields = ['id', 'membership', 'voting', 'voting_done', 'display_first_name', 'display_last_name']

    def validate(self, attrs):
        attrs = super(VotingVoterSerializer, self).validate(attrs)
        if attrs.get('weight', 1) <= 0:
            raise ValidationError({'weight': _('Must be greater then 0')})
        return attrs


class VotingDetailsSerializer(VotingSerializer):
    questions = VotingQuestionSerializer(many=True, read_only=True)
    voters = VotingVoterSerializer(many=True, read_only=True)

    class Meta(VotingSerializer.Meta):
        fields = VotingSerializer.Meta.fields + ['questions', 'voters']


class VotingDetailsWithResultSerializer(VotingDetailsSerializer):
    result = serializers.SerializerMethodField()

    class Meta(VotingDetailsSerializer.Meta):
        fields = VotingDetailsSerializer.Meta.fields + ['result']

    def get_result(self, voting):
        all_voters = list(voting.voters.all().prefetch_related('answers'))
        voters = [v for v in all_voters if v.voting_done]
        voter_by_id = {v.id: v for v in voters}
        question_by_id = {q.id: q for q in voting.questions.all()}

        full_weight = sum(v.weight for v in voters)

        show_answers = voting.is_result_visible()

        def collect_answer(voter_answers):
            voter_answers = list(voter_answers)  # materialize
            weight = sum(voter_by_id[a.voter_id].weight for a in voter_answers)
            return False if not show_answers else {
                'weight': weight,
                'percent': float(weight) * 100 / full_weight,
                'voters': [
                    {
                        'voter_id': None if voting.is_anonymous else a.voter_id,
                        'ip': None if voting.is_anonymous else a.voter_ip_address,
                        'vote_date': a.created,
                        'first_name': None if voting.is_anonymous else voter_by_id[a.voter_id].display_first_name,
                        'last_name': None if voting.is_anonymous else voter_by_id[a.voter_id].display_last_name,
                        'vote_note': a.vote_note,
                    } for a in voter_answers]
            }

        answers_per_question = dict_by_key((a for v in voters for a in v.answers.all()), lambda answer: answer.question_id)
        question_info = {}
        for question_id, voter_answers in answers_per_question.items():
            question = question_by_id[question_id]
            if question.question_type == VotingQuestion.TYPE_YES_NO:
                answers = {
                    'yes': collect_answer(a for a in voter_answers if a.yes_no),
                    'no': collect_answer(a for a in voter_answers if not a.yes_no),
                }
            elif question.question_type == VotingQuestion.TYPE_FOR_AGAINST_ABSTAIN:
                answers = {
                    'for': collect_answer(a for a in voter_answers if a.for_against_abstain == VoterAnswer.ANSWER_FOR),
                    'against': collect_answer(a for a in voter_answers if a.for_against_abstain == VoterAnswer.ANSWER_AGAINST),
                    'abstain': collect_answer(a for a in voter_answers if a.for_against_abstain == VoterAnswer.ANSWER_ABSTAIN),
                }
            elif question.question_type == VotingQuestion.TYPE_SINGLE_SELECT or question.question_type == VotingQuestion.TYPE_MULTIPLE_SELECT:
                # Quite hard code to read it... voter_answer (in voter_answers) has list of answers,
                # so we need to unpack it first, regroup by answer, then do math
                voter_answers_by_answer_id = dict_by_key(((answer.id, voter_answer) for voter_answer in voter_answers for answer in voter_answer.answers.all()),
                                                         lambda t: t[0])
                answers = {qa.id: collect_answer(t[1] for t in voter_answers_by_answer_id.get(qa.id, [])) for qa in question.answers.all()}
            elif question.question_type == VotingQuestion.TYPE_ELECTION:
                voter_answers_by_candidate = dict_by_key(voter_answers, lambda a: a.candidate_id)
                answers = {candidate.id: collect_answer(voter_answers_by_candidate.get(candidate.id, [])) for candidate in question.candidates.all()}
            else:
                raise NotImplementedError("Unknown type %d" % (question.question_type,))

            question_info[question_id] = answers

        return {
            'total': len(all_voters),
            'has_answers': any(bool(v.answers.all()) for v in all_voters),
            'done': len(voters),
            'done_weight': full_weight,
            'questions': question_info
        }


class AvailableVotingSerializer(VotingSerializer):
    voter_key = serializers.SerializerMethodField()
    voting_done = serializers.SerializerMethodField()

    def get_voter_key(self, voting):
        membership_id = self.context['membership'] and self.context['membership'].id
        # Collections will be prefetched so lookup correct voter in python
        return next((v.voter_key for v in voting.voters.all() if v.membership_id == membership_id), None)

    def get_voting_done(self, voting):
        membership_id = self.context['membership'] and self.context['membership'].id
        return next((v.voting_done for v in voting.voters.all() if v.membership_id == membership_id), None)

    class Meta(VotingSerializer.Meta):
        fields = VotingSerializer.Meta.fields + ['voter_key', 'voting_done']


class VotingVoteSerializer(VotingSerializer):
    questions = VotingQuestionSerializer(many=True, read_only=True)
    answers = serializers.SerializerMethodField()
    voting_done = serializers.SerializerMethodField()

    # noinspection PyUnusedLocal
    def get_answers(self, voting):
        answers = VoterAnswer.objects.filter(voter=self.context['voter'])
        return {answer.question_id: VoterAnswerSerializer(answer).data for answer in answers}

    def get_voting_done(self, voting):
        return self.context['voter'].voting_done

    class Meta(VotingSerializer.Meta):
        fields = VotingSerializer.Meta.fields + ['questions', 'answers', 'voting_done']


class VoterAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoterAnswer
        fields = ['question', 'yes_no', 'candidate', 'answers', 'for_against_abstain', 'vote_note']

    def validate(self, attrs):
        attrs = super(VoterAnswerSerializer, self).validate(attrs)
        question = attrs['question']
        assert isinstance(question, VotingQuestion)

        if question.question_type == question.TYPE_YES_NO:
            if attrs['yes_no'] is None:
                raise ValidationError({'yes_no': [_('This field is required for yes/no question')]})
        else:
            attrs['yes_no'] = None

        if question.question_type == question.TYPE_FOR_AGAINST_ABSTAIN:
            if attrs.get('for_against_abstain') is None:
                raise ValidationError({'for_against_abstain': [_('This field is required for for/against/abstain question')]})
            if attrs['for_against_abstain'] not in [k for k, v in VoterAnswer.FAA_CHOICES]:
                raise ValidationError({'for_against_abstain': [_('Incorrect value for for/against/abstain question')]})
        else:
            attrs['for_against_abstain'] = None

        candidate = attrs.get('candidate')
        if candidate and not question.candidates.filter(pk=candidate.id).exists():
            raise ValidationError({'candidate': [_('Wrong candidate for this election.')]})

        if question.question_type == question.TYPE_ELECTION:
            if not candidate:
                raise ValidationError({'candidate': [_('This field is required for election.')]})
        else:
            attrs['candidate'] = None

        answers = attrs.get('answers')
        if answers:
            valid_answers = {a.id for a in question.answers.all()}
            for (index, answer) in enumerate(answers):
                if answer.id not in valid_answers:
                    raise ValidationError({'answers': {index: [_('Wrong answer for this question.')]}})

        if question.question_type == question.TYPE_SINGLE_SELECT:
            if not answers or len(answers) == 0:
                raise ValidationError({'answers': [_('This field is required for single select.')]})
            if len(answers) > 1:
                raise ValidationError({'answers': [_('Too many answers selected for single select')]})
        elif question.question_type == question.TYPE_MULTIPLE_SELECT:
            if not answers or len(answers) == 0:
                raise ValidationError({'answers': [_('This field is required for multi select.')]})
        else:
            attrs['answers'] = []

        return attrs


class EmptySerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


def add_voters_for_voting(account, voting, add_members_data):
    memberships = set(add_members_data['memberships'])
    memberships.update({m for committee in add_members_data['committees'] for m in committee.memberships.all()})

    if 'guests' in add_members_data['all_members']:
        memberships.update({m for m in account.memberships.filter(is_active=True) if m.is_guest})
    if 'members' in add_members_data['all_members']:
        memberships.update({m for m in account.memberships.filter(is_active=True) if not m.is_guest})

    existing_voters = {v.membership.id for v in voting.voters.all() if v.membership}

    for member in memberships:
        if member.id not in existing_voters:
            voter = models.VotingVoter(voting=voting, membership=member, weight=add_members_data['weight'])
            voter.save()
