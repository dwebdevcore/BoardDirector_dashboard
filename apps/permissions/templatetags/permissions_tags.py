# -*- coding: utf-8 -*-
from django import template
from permissions import shortcuts

register = template.Library()


@register.filter
def has_role_permission(membership, permission_string):
    """
    :param permission_string: 'app_label.model:permission'.
    """
    model, permission = permission_string.split(':')
    return shortcuts.has_role_permission(membership, model, permission)


@register.simple_tag(takes_context=True)
def has_permission(context, model, permission, obj=None):
    """
    :param model: 'app_label.model'
    """
    membership = context['current_membership']
    return (shortcuts.has_role_permission(membership, model, permission) or
            shortcuts.has_object_permission(membership, obj, permission))
