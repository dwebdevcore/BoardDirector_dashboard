# -*- coding: utf-8 -*-
from django import template

register = template.Library()


def avatar(membership, geometry):
    return membership.avatar_url(geometry)


def membership(user, account):
    return user.get_membership(account)

register.filter('avatar', avatar)
register.filter('membership', membership)
