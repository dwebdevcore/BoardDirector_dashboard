# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import Http404, HttpResponseNotFound
from django.template import loader

from accounts.account_helper import get_current_account


def membership(request):
    membership = None
    account = get_current_account(request)
    if account and request.user and request.user.is_authenticated:
        membership = request.user.get_membership(account)
    return {'current_membership': membership}


def trial_period(request):
    return {'trial_period': settings.TRIAL_PERIOD}


def chameleon(request):
    return {'chameleon_enabled': settings.CHAMELEON_ENABLED}

def tidio(request):
    return {'tidio_enabled': settings.TIDIO_ENABLED}
