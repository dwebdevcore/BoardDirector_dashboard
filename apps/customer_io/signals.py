# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from accounts.account_helper import get_current_account
from .api import CIOApi
from billing.models import Invoice
from committees.views import CommitteeCreateView
from common.signals import view_create
from documents.views import DocumentAjaxCreateView
from meetings.views import MeetingCreateView
from profiles.models import Membership
from registration.signals import user_activated

api = CIOApi()
logger = logging.getLogger(__name__)


@receiver(user_activated)
def event_user_activated(sender, user, request, **kwargs):
    try:
        # User doesn't have session['current_account'] at this point
        membership = user.membership_set.all()[0]
        api.track_event(membership=membership, name='User Activated')
    except Exception as e:
        logger.exception(e)


@receiver(user_logged_in)
def update_membership(sender, user, request, **kwargs):
    try:
        for membership in user.membership_set.all():
            api.create_or_update(membership)
    except Exception as e:
        logger.exception(e)


def _get_membership(request):
    try:
        return request.user.get_membership(account=get_current_account(request))
    except Exception as e:
        logger.exception(e)


@receiver(view_create, sender=DocumentAjaxCreateView)
def event_document_created(sender, instance, request, **kwargs):
    api.track_event(membership=_get_membership(request), name='Document Created')


@receiver(view_create, sender=MeetingCreateView)
def event_meeting_created(sender, instance, request, **kwargs):
    api.track_event(membership=_get_membership(request), name='Meeting Created')


@receiver(view_create, sender=CommitteeCreateView)
def event_committee_created(sender, instance, request, **kwargs):
    api.track_event(membership=_get_membership(request), name='Committee Created')


@receiver(post_save, sender=Invoice)
def event_invocie_update(sender, instance, **kwargs):
    # Send as account admin user event
    qs = instance.account.memberships.filter(is_admin=True)[:1]
    if len(qs):
        membership = qs[0]
        api.track_event(membership=membership, name='Invoce Updated',
                        status=instance.get_status_display(), payment=instance.payment)


@receiver(post_delete, sender=Membership)
def delete_membership(sender, instance, **kwargs):
    api.delete(membership=instance)
