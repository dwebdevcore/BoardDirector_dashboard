# -*- coding: utf-8 -*-
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _

from accounts.models import Account
from common.models import TemplateModel
from documents.models import Folder


class RecentActivityManager(models.Manager):
    def for_membership(self, membership):
        queryset = self.filter(account=membership.account)
        # TODO - WEB-129
        if membership.role not in (membership.ROLES.chair,):
            queryset = queryset.filter(init_user=membership.user)
        return queryset


class RecentActivity(models.Model):
    """
        This will showcase the latest activity that is associated with the user.
        If he is part of a committee, and a new document is added, then this will appear here.
        Title of the activity
        (New Meetings, Updated Meetings, New Documents, Updated Documents,
        New Committee added, New Member Added
        Date of the Meeting associated to the document,
        Title of the Meeting (if a meeting).
        Location (if a meeting)
        File icon (linkable and downloadable)
        Name of file (linkable and downloadable)
        Name of who created the document
        Date of when they added it (for an audit trail)
        The six most recent activities will show up and then a pagination appears.
    """
    ADDITION, CHANGE = 1, 2
    ACTION_FLAG_CHOICES = (
        (ADDITION, 'New'),
        (CHANGE, 'Updated'),
    )

    init_user = models.ForeignKey(
        'profiles.User', related_name='recent_activity')
    account = models.ForeignKey('accounts.Account', related_name='recent_activity')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    action_flag = models.PositiveSmallIntegerField(
        _('action flag'), choices=ACTION_FLAG_CHOICES)
    action_time = models.DateTimeField(auto_now_add=True)

    objects = RecentActivityManager()

    class Meta:
        ordering = ['-action_time']
        verbose_name = _('Recent Activity')
        verbose_name_plural = _('Recent Activities')

    def __unicode__(self):
        return u'Recent Activity item "{}"'.format(self.content_object)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.account = Account.objects.get(pk=self.account.pk)
        super(RecentActivity, self).save(force_insert, force_update, using, update_fields)
