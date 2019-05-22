# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import string

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls.base import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class CommonStrMixin(object):
    def __unicode__(self):
        return u"%s #%d" % (self.__class__.__name__, self.pk)


class Voting(models.Model, CommonStrMixin):
    STATE_DRAFT, STATE_PUBLISHED = range(0, 2)
    STATE_CHOICES = [(STATE_DRAFT, _('Draft')), (STATE_PUBLISHED, _('Published'))]

    account = models.ForeignKey('accounts.Account', verbose_name=_('account'), related_name='votings', on_delete=models.CASCADE)
    owner = models.ForeignKey('profiles.Membership', related_name='votings', on_delete=models.CASCADE)

    name = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField()
    start_time = models.DateTimeField()  # Not used in UI anymore
    end_time = models.DateTimeField()
    state = models.IntegerField(choices=STATE_CHOICES, default=STATE_DRAFT)
    is_active = models.BooleanField(default=True)  # Soft-delete, not implemented
    is_result_published = models.BooleanField(default=False)  # For preliminary result publishing

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super(Voting, self).__init__(*args, **kwargs)

    def clean(self):
        if self.start_time > self.end_time:
            raise ValidationError({'start_time': _('Start time must be before end time')})

    @property
    def is_published(self):
        return self.state == self.STATE_PUBLISHED

    def is_in_progress(self, date_time=None):
        date_time = date_time or timezone.now()
        return self.is_published and self.start_time <= date_time < self.end_time and not self.all_voters_done()

    def is_done(self, date_time=None):
        date_time = date_time or timezone.now()
        return self.is_published and date_time >= self.start_time and self.all_voters_done()

    def is_result_visible(self):
        return self.all_voters_done() or self.is_result_published

    def all_voters_done(self):
        return next((False for v in self.voters.all() if not v.voting_done), True)

    @property
    def can_edit(self):
        return not self.is_published

    @property
    def can_publish(self):
        return bool(self.voters.all() and self.questions.all())


class VotingVoter(models.Model, CommonStrMixin):
    KEY_LENGTH = 16

    voting = models.ForeignKey(Voting, on_delete=models.CASCADE, related_name='voters')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    voter_key = models.CharField(max_length=KEY_LENGTH, unique=True, db_index=True)

    membership = models.ForeignKey('profiles.Membership', null=True, blank=True, on_delete=models.CASCADE)
    weight = models.IntegerField(default=1, validators=[MinValueValidator(1)])  # Not used in UI

    first_name = models.CharField(max_length=1024, null=True, blank=True)
    last_name = models.CharField(max_length=1024, null=True, blank=True)
    email = models.EmailField(max_length=1024, null=True, blank=True)

    voting_done = models.BooleanField(default=False)  # Filled automatically after all questions are answered

    class Meta:
        ordering = ['id']

    def __init__(self, *args, **kwargs):
        super(VotingVoter, self).__init__(*args, **kwargs)

    def generate_key(self):
        self.voter_key = ''.join(random.choice(string.digits + string.ascii_letters) for i in range(self.KEY_LENGTH))

    def clean(self):
        if not self.membership and not (self.first_name and self.last_name and self.email):
            raise ValidationError(_('Either user or first_name and last_name and email must be set'))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.voter_key:
            self.generate_key()

        super(VotingVoter, self).save(force_insert, force_update, using, update_fields)

    @property
    def display_first_name(self):
        return self.first_name or self.membership.first_name

    @property
    def display_last_name(self):
        return self.first_name or self.membership.last_name

    def get_voting_url(self):
        return reverse('voting:voting-vote-by-key', kwargs={'url': self.voting.account.url, 'voter_key': self.voter_key})


class VotingQuestion(models.Model, CommonStrMixin):
    TYPE_YES_NO, TYPE_SINGLE_SELECT, TYPE_MULTIPLE_SELECT, TYPE_ELECTION, TYPE_FOR_AGAINST_ABSTAIN = range(1, 6)
    TYPE_CHOICES = [
        (TYPE_YES_NO, _("Yes/no")),
        (TYPE_SINGLE_SELECT, _('Single Select')),
        (TYPE_MULTIPLE_SELECT, _('Multiple Select')),
        (TYPE_ELECTION, _('Election')),
        (TYPE_FOR_AGAINST_ABSTAIN, _('For/Against/Abstain'))]

    voting = models.ForeignKey(Voting, on_delete=models.CASCADE, related_name='questions')
    question_type = models.IntegerField(choices=TYPE_CHOICES)
    ordering = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    question = models.TextField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['ordering', 'created']


class VotingQuestionAnswer(models.Model, CommonStrMixin):
    question = models.ForeignKey(VotingQuestion, on_delete=models.CASCADE, related_name='answers')
    created = models.DateTimeField(auto_now_add=True)
    answer = models.TextField()

    class Meta:
        ordering = ['id']


class VotingQuestionCandidate(models.Model, CommonStrMixin):
    question = models.ForeignKey(VotingQuestion, on_delete=models.CASCADE, related_name='candidates')
    created = models.DateTimeField(auto_now_add=True)

    membership = models.ForeignKey('profiles.Membership', null=True, blank=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=1024, null=True, blank=True)
    last_name = models.CharField(max_length=1024, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def avatar_url(self):
        return self.membership and self.membership.avatar_url()

    class Meta:
        ordering = ['id']


class VoterAnswer(models.Model, CommonStrMixin):
    ANSWER_FOR, ANSWER_AGAINST, ANSWER_ABSTAIN = range(1, 4)
    FAA_CHOICES = [
        (ANSWER_FOR, _("For")),
        (ANSWER_AGAINST, _("Against")),
        (ANSWER_ABSTAIN, _("Abstain")),
    ]

    question = models.ForeignKey(VotingQuestion, on_delete=models.CASCADE, related_name='voter_answers')
    voter = models.ForeignKey(VotingVoter, on_delete=models.CASCADE, related_name='answers')
    created = models.DateTimeField(auto_now_add=True)
    voter_ip_address = models.GenericIPAddressField()

    yes_no = models.NullBooleanField()
    for_against_abstain = models.SmallIntegerField(null=True, blank=True, choices=FAA_CHOICES)
    candidate = models.ForeignKey(VotingQuestionCandidate, null=True, blank=True, on_delete=models.SET_NULL)
    answers = models.ManyToManyField(VotingQuestionAnswer, blank=True)  # To support multiple selection

    vote_note = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = [('voter', 'question')]
        ordering = ['id']
