# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response

from common.mixins import GetMembershipWithURLFallbackMixin, PerActionSerializerModelViewSetMixin, AccountSerializerContextMixin, ApiInitAccountByUrlMixin
from common.utils import get_ip_address_from_request
from permissions.rest_permissions import IsAccountAdminOrReadOnly, CheckAccountUrl, IsMember, IsAccountAdmin
from voting.models import Voting, VotingQuestion, VotingVoter, VoterAnswer
from voting.serializers import VotingDetailsSerializer, VotingQuestionSerializer, VotingVoterSerializer, EmptySerializer, VotingSerializer, \
    VoterAnswerSerializer, AvailableVotingSerializer, VotingVoteSerializer, VotingDetailsWithResultSerializer, VotingAddMembersSerializer, add_voters_for_voting
from voting.voting_utils import send_voting_email


class EditIfVotingNotPublished(BasePermission):
    message = "Can't edit if Voting is already published"

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or not obj.voting.is_published


class CheckAccountForVotingItems(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.voting.account.url == view.kwargs['url'] and obj.voting_id == int(view.kwargs['voting'])


class VotingViewSet(ApiInitAccountByUrlMixin, PerActionSerializerModelViewSetMixin, LoginRequiredMixin, GetMembershipWithURLFallbackMixin,
                    AccountSerializerContextMixin, viewsets.ModelViewSet):
    """
    Voting viewset - returns all available votings. Currently available only for Board Admin.
    
    * Use `/{board}/api/v1/voting/available-votings` to get list of votings, available for user. 
      This list also contains `voter_key` which is specific for user and is used in all requests to vote. 
    * Use [`/{pk}/questions`](./questions) to access questions information (and primarily POST new questions, PUT for update and DELETE)
    * Use [`/{pk}/voters`](./voters) to list voters for voting
        * [`/{pk}/voters/add_members`](./add_members) to add voters, it's combiner method: 
          POST `{ memberships: [1, 2, 3], committees: [1, 2], all_members: ['members', 'guests'], weight: 1 }`
          use [`/{board}/api/v1/profiles/committees/`](`/{board}/api/v1/profiles/committees/`) to list committees 
    * Use [`POST /{pk}/publish`](./publish) to publish Voting. There is currently no way to unpublish. So think twice.
     
    """
    serializer_class = VotingDetailsSerializer
    serializer_class_list = VotingSerializer
    serializer_class_retrieve = VotingDetailsWithResultSerializer
    permission_classes = [IsAccountAdminOrReadOnly, CheckAccountUrl]

    def get_queryset(self):
        query_set = Voting.objects.filter(account=self.get_current_account()).order_by('-pk')
        if self.action == 'retrieve':
            query_set = query_set.prefetch_related('questions', 'questions__answers',
                                                   'questions__candidates', 'questions__candidates__membership',
                                                   'voters', 'voters__membership', 'voters__answers', 'voters__answers__answers')
        return query_set

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(account=self.get_current_account(), owner=self.get_current_membership())

    @detail_route(methods=['post'], serializer_class=EmptySerializer, permission_classes=permission_classes)
    @transaction.atomic
    def publish(self, request, pk, url):
        voting = Voting.objects.filter(account__url=url).get(pk=pk)
        if not len(voting.voters.all()):
            raise ValidationError({'voters': [_('Voting can\'t be published without voters')]})
        if not len(voting.questions.all()):
            raise ValidationError({'questions': [_("Voting can't be published without questions")]})

        voting.state = Voting.STATE_PUBLISHED
        voting.save()

        send_voting_email(request, voting)

        serializer = VotingSerializer(voting, context=self.get_serializer_context())
        return Response(serializer.data)

    @detail_route(methods=['post'], serializer_class=EmptySerializer, permission_classes=[IsAccountAdmin])
    @transaction.atomic
    def publish_results(self, request, pk, url):
        voting = Voting.objects.filter(account__url=url).get(pk=pk)
        if not voting.is_published:
            raise ValidationError({'non_field_errors': [_('Voting must be published to publish it\'s results.')]})

        voting.is_result_published = True
        voting.save()

        return Response({'result': 'ok'})

    @detail_route(methods=['post'], permission_classes=permission_classes)
    def resend_email(self, request, pk, url):
        voting = Voting.objects.filter(account__url=url).get(pk=pk)
        send_voting_email(request, voting)

        return Response({'result': 'ok'})

    def perform_destroy(self, instance):
        if VoterAnswer.objects.filter(question__voting=instance).exists():
            raise PermissionDenied(_("Can't delete voting with votes"))

        super(VotingViewSet, self).perform_destroy(instance)


class AvailableVotingsViewSet(ApiInitAccountByUrlMixin, GetMembershipWithURLFallbackMixin, AccountSerializerContextMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AvailableVotingSerializer
    permission_classes = [IsMember, CheckAccountUrl]

    def get_queryset(self):
        return Voting.objects.filter(
            account=self.get_current_account(),
            state=Voting.STATE_PUBLISHED,
            voters__membership=self.get_current_membership()
        ).prefetch_related('voters').order_by('-pk')

    def get_serializer_context(self):
        context = super(AvailableVotingsViewSet, self).get_serializer_context()
        context['membership'] = self.get_current_membership()
        return context


class QuestionViewSet(ApiInitAccountByUrlMixin, PerActionSerializerModelViewSetMixin, LoginRequiredMixin, GetMembershipWithURLFallbackMixin,
                      viewsets.ModelViewSet):
    serializer_class = VotingQuestionSerializer
    permission_classes = [IsAccountAdminOrReadOnly, EditIfVotingNotPublished, CheckAccountForVotingItems]

    def get_queryset(self):
        return VotingQuestion.objects.filter(voting__account=self.get_current_account())

    def perform_create(self, serializer):
        serializer.save(voting_id=self.kwargs['voting'])


class VoterViewSet(ApiInitAccountByUrlMixin, PerActionSerializerModelViewSetMixin, LoginRequiredMixin, GetMembershipWithURLFallbackMixin,
                   viewsets.ModelViewSet):
    serializer_class = VotingVoterSerializer
    permission_classes = [IsAccountAdminOrReadOnly, EditIfVotingNotPublished, CheckAccountForVotingItems]

    def get_queryset(self):
        return VotingVoter.objects.filter(voting__account=self.get_current_account())

    def perform_create(self, serializer):
        serializer.save(voting_id=self.kwargs['voting'])

    @list_route(methods=['POST'], permission_classes=permission_classes)
    def add_members(self, request, voting, **kwargs):
        voting = get_object_or_404(Voting.objects.all(), account=self.get_current_account(), pk=voting)

        serializer = VotingAddMembersSerializer(data=request.data, context={'account': self.get_current_account()})
        serializer.is_valid(raise_exception=True)

        # TODO: Decide whether to move this into serializer?
        add_voters_for_voting(account=self.get_current_account(),
                              voting=voting,
                              add_members_data=serializer.validated_data)

        return Response({'result': 'ok'}, status=201)


class VoteVotingViewSet(AccountSerializerContextMixin, GetMembershipWithURLFallbackMixin, viewsets.ViewSet):
    """
    This is API to retrieve Voting information to perform actual voting.
     
    Use `GET /<url>/api/v1/voting/available-votings/` to obtain `voter_key`.
    
    It has specific format:
    
    * `GET /` - list is empty, just placeholder,
    * `GET /<voter_key>/` - will return data for voting: Voting + current recorded answers,
    * `POST /<voter_key>/` - has structure similar to single answer, and returns updated voting in response.
    * `POST /<voter_key>/mark_done/` - will mark this voter as done.
    """

    def list(self, request, **kwargs):
        return Response([])

    def get_serializer(self, instance=None):
        # For auto documentation purposes, ignore instance as it takes data.serializer from response.
        return VoterAnswerSerializer(instance=None)

    def retrieve(self, request, pk, **kwargs):
        voter = self._find_voter(pk)
        voting = voter.voting
        context = self.get_serializer_context()
        context['voter'] = voter
        return Response(VotingVoteSerializer(voting, context=context).data)

    def update(self, request, pk, **kwargs):
        serializer = VoterAnswerSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)

        voter = self._find_voter(pk)
        voting = voter.voting

        if not voting.is_in_progress():
            return Response({'non_field_errors': [_('Voting is not in progress now.')]}, status=403)

        data = dict(serializer.validated_data)
        data['voter'] = voter
        data['voter_ip_address'] = get_ip_address_from_request(request)
        if data['question'].voting != voting:
            return Response({'non_field_errors': [_('Question doesn\'t belong to this voting.')]}, status=403)
        try:
            instance = VoterAnswer.objects.get(voter=voter, question=serializer.validated_data['question'])
            serializer.update(instance, data)
        except VoterAnswer.DoesNotExist:
            serializer.create(data)

        context = self.get_serializer_context()
        context['voter'] = voter
        return Response(VotingVoteSerializer(voting, context=context).data)

    @detail_route(methods={'POST'})
    def mark_done(self, request, pk, **kwargs):
        voter = self._find_voter(pk)
        voting = voter.voting
        answered_questions = {a.question_id for a in voter.answers.all()}
        for q in voting.questions.all():
            if q.id not in answered_questions:
                return Response({'non_field_errors': [_("Voting can't be marked done until all questions are answered.")]}, status=400)

        voter.voting_done = True
        voter.save()

        context = self.get_serializer_context()
        context['voter'] = voter
        return Response(VotingVoteSerializer(voting, context=context).data)

    def _find_voter(self, voter_key):
        voter = get_object_or_404(VotingVoter.objects.filter(voting__account__url=self.kwargs['url']), voter_key=voter_key)
        assert isinstance(voter, VotingVoter)
        return voter
