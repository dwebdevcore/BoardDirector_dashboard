# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.utils import timezone


class CommitteeManager(models.Manager):
    # TODO - convert to QuerySet as_manager after Django upgrade
    # add upcoming, past
    def for_membership(self, membership):
        queryset = self.filter(account=membership.account)
        # limit guest to see only his committee meetings
        if membership.role in (membership.ROLES.guest, membership.ROLES.vendor, membership.ROLES.consultant):
            committee_ids = membership.committees.all().values_list('id', flat=True)
            queryset = queryset.filter(id__in=committee_ids)
        return queryset


class Committee(models.Model):
    name = models.CharField(_('name'), max_length=250)
    chairman = models.ManyToManyField('profiles.Membership', verbose_name=_('chairman'))
    summary = models.CharField(_('short summary'), blank=True, max_length=250)
    description = models.TextField(_('description'), blank=True)
    account = models.ForeignKey('accounts.Account', verbose_name=_('account'), related_name='committees')

    objects = CommitteeManager()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('committees:detail', kwargs={'pk': self.pk, 'url': self.account.url})

    def members(self):
        all_members = self.memberships.all()
        chairman = self.chairman.all()
        [setattr(c, 'is_chair', True) for c in chairman]
        members = [m for m in all_members if m not in chairman and m.is_active]
        members.extend(chairman)
        return members

    def ordinary_members(self):
        all_members = self.memberships.all()
        chairman = self.chairman.all()
        members = [m for m in all_members if m not in chairman and m.is_active]
        return members

    def upcoming_meetings(self):
        return self.meetings.filter(start__gt=timezone.now()).reverse()

    def past_meetings(self):
        return self.meetings.filter(end__lt=timezone.now())
