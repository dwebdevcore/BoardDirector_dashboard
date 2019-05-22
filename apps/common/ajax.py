# -*- coding: utf-8 -*-
# from dajax.core import Dajax
# from dajaxice.decorators import dajaxice_register
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext as _

from committees.models import Committee
from meetings.models import Meeting


# @dajaxice_register
# def committees_filter(request, committee_id=None):
#     dajax = Dajax()
#     membership = request.user.get_membership(request.session['current_account'])
#     committees = Committee.objects.for_membership(membership)
#     if committee_id:
#         committees = committees.filter(id=committee_id)
#     if committees:
#         members_email = mailto_email(committees)
#         committees = render_to_string('committees/includes/committees.html', {'committees': committees})
#         dajax.add_data(data={'committees': committees, 'members_email': members_email}, function='update_committee_list')
#     return dajax.json()
#
#
# @dajaxice_register
# def meeting_filter(request, filter_by=None):
#     membership = request.user.get_membership(request.session['current_account'])
#     meetings = Meeting.objects.for_membership(membership).filter(start__gte=timezone.now())
#     return result_meeting_filter(meetings, filter_by)
#
#
# @dajaxice_register
# def past_meeting_filter(request, filter_by=None):
#     membership = request.user.get_membership(request.session['current_account'])
#     meetings = Meeting.objects.for_membership(membership).filter(start__lt=timezone.now())
#     return result_meeting_filter(meetings, filter_by)
#
#
# def result_meeting_filter(meetings, filter_by=None):
#     dajax = Dajax()
#     if filter_by:
#         if filter_by == 'desc':
#             meetings = meetings.order_by('-start')
#         elif filter_by == 'asc':
#             meetings = meetings.order_by('start')
#         else:
#             meetings = meetings.filter(committee_id=filter_by)
#     if meetings:
#         meetings = render_to_string('meetings/includes/meetings.html', {'meetings': meetings})
#         dajax.add_data(data={'meetings': meetings}, function='update_meetings_list')
#     else:
#         dajax.add_data(data={'empty_message': _('No Meetings Found')}, function='display_empty_message')
#
#     return dajax.json()


def mailto_email(committees):
    members_email = 'mailto:'
    for committee in committees:
        for member in committee.members():
            if member.user.email not in members_email:
                members_email += '{},'.format(member.user.email)
    return members_email[:-1]
