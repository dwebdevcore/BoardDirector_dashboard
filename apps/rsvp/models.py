# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField


class RsvpRule(models.Model):
    REQUIRED_RESPONSES, REQUIRED_ACCEPTATIONS, MAX_RESPONSES_PER_USER, LATEST_RESPONSE_DATE, LATEST_RESPONSE_CHANGE_DATE = range(5)
    RULE_TYPE_CHOICES = (
        (REQUIRED_RESPONSES, _('Required responses')),
        (REQUIRED_ACCEPTATIONS, _('Required acceptations')),
        (MAX_RESPONSES_PER_USER, _('Max responses per invitee')),
        (LATEST_RESPONSE_DATE, _('Latest response date')),
        (LATEST_RESPONSE_CHANGE_DATE, _('Latest response change date'))
    )
    meeting = models.ForeignKey('meetings.Meeting', verbose_name=_('meeting'), null=False, related_name='rsvp_rules')
    rule_type = models.PositiveSmallIntegerField(_('rule type'), choices=RULE_TYPE_CHOICES, default=REQUIRED_RESPONSES)
    rule_parameters = JSONField(default='{}')


class RsvpResponse(models.Model):
    ACCEPT, DECLINE, TENTATIVE = range(3)
    RESPONSE_CHOICES = (
        (ACCEPT, _('Accept')),
        (DECLINE, _('Decline')),
        (TENTATIVE, _('Tentative'))
    )
    IN_PERSON, BY_PHONE, OTHER = range(3)
    ACCEPT_CHOICES = [
        (IN_PERSON, _('In Person')),
        (BY_PHONE, _('By Phone')),
        (OTHER, _('Other')),
    ]
    timestamp = models.DateTimeField(auto_now_add=True)
    meeting = models.ForeignKey('meetings.Meeting', verbose_name=_('meeting'), null=False, related_name='rsvp_responses')
    meeting_repetition = models.ForeignKey('meetings.MeetingRepetition', verbose_name=_('meeting repetition'), null=True, related_name='rsvp_responses')
    user = models.ForeignKey('profiles.User', verbose_name=_('user'), null=False, related_name='rsvp_responses')
    response = models.PositiveSmallIntegerField(_('response'), choices=RESPONSE_CHOICES, default=TENTATIVE)
    accept_type = models.PositiveSmallIntegerField(choices=ACCEPT_CHOICES, default=IN_PERSON)
    note = models.TextField(null=True, blank=True)

    def response_from_string(self, s):
        for (key, verbose) in self.RESPONSE_CHOICES:
            if verbose.lower() == s.lower():
                return key
        raise KeyError(s)

    def __unicode__(self):
        return 'RsvpResponse(meeting_id={meeting_id}, meeting_repetition_id={meeting_repetition_id}, user_id={user_id}, ' \
               'response={response}, timestamp={timestamp})'.format(**self.__dict__)
