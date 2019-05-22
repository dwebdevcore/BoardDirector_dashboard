# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from common.choices import Choices

PERMISSIONS = Choices(
    ('view', 'view', _('View')),
    ('add', 'add', _('Add')),
    ('edit', 'edit', _('Edit')),
    ('delete', 'delete', _('Delete')),
    ('share', 'share', _('Share')),
)
