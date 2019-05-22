# -*- coding: utf-8 -*-
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from . import PERMISSIONS
from profiles.models import Membership


class RolePermission(models.Model):
    """Global permissions."""
    role = models.PositiveSmallIntegerField(_('role'), choices=Membership.ROLES)
    content_type = models.ForeignKey(ContentType, verbose_name=_('content type'), related_name='+')
    permission = models.CharField(_('permission'), choices=PERMISSIONS, max_length=50)

    class Meta:
        ordering = ('role', 'content_type', 'permission')

    def __unicode__(self):
        return '{0} {1} {2}'.format(self.get_role_display(), self.content_type, self.get_permission_display())


class ObjectPermission(models.Model):
    """Account specific permissions."""
    role = models.PositiveSmallIntegerField(_('role'), choices=Membership.ROLES, null=True, blank=True)
    membership = models.ForeignKey('profiles.Membership', verbose_name=_('member'), related_name='object_permissions',
                                   null=True, blank=True, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, verbose_name=_('content type'), related_name='+')
    object_id = models.PositiveIntegerField(_('object id'))
    content_object = GenericForeignKey('content_type', 'object_id')
    permission = models.CharField(_('permission'), choices=PERMISSIONS, max_length=50)

    class Meta:
        ordering = ('content_type', 'object_id', 'role', 'membership', 'permission')

    def __unicode__(self):
        return '{0} {1} {2}'.format(self.membership or self.get_role_display(), self.content_object, self.get_permission_display())

    def clean(self, *args, **kwargs):
        if not self.role and not self.membership:
            raise ValidationError(_('Role or member has to be selected.'))
        if self.role and self.membership:
            raise ValidationError(_('Role cannot be selected together with member.'))
        if self.content_type and self.object_id and self.content_object is None:
            raise ValidationError(_('Invalid object id.'))
        return super(ObjectPermission, self).clean(*args, **kwargs)

    ROLE_STRINGS = {
        None: _('No Role'),
        Membership.ROLES.guest: _('All Guests'),
        Membership.ROLES.member: _('All Board Members'),
    }

    def get_role_string(self):
        return self.ROLE_STRINGS.get(self.role, self.get_role_display())

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(ObjectPermission, self).save(*args, **kwargs)
