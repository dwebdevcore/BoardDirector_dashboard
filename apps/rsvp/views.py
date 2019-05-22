# -*- coding: utf-8 -*-
from django.core.exceptions import PermissionDenied
from django.views.generic import UpdateView

from accounts.account_helper import get_current_account
from common.mixins import AjaxableResponseMixin, LoginRequiredMixin
from meetings.models import Meeting, MeetingRepetition
from rsvp.forms import RsvpResponseForm
from .models import RsvpResponse


class RsvpUpdateView(LoginRequiredMixin, AjaxableResponseMixin, UpdateView):
    model = RsvpResponse

    def post(self, request, *args, **kwargs):
        """
        Handles AJAX calls on RsvpResponse objects.

        :param request:
        - request.path: /<account>/rsvp/,
        - request.POST: <QueryDict: {u'meeting': [u'<meeting pk>'],
                                     u'response': [u'Accept|Decline|Tentative']}>,

        Security notes:
        - relies on django's CSRF middleware to prevent one user from poking into another user's session
        - relies on django's session middleware to cross-check the requested URL against the logged in user
        - implements check for meeting membership
        """
        try:
            # Check for manipulated request URLs (i.e. /<not this session user's account>/rsvp/)
            account = get_current_account(request)
            if account.url != self.kwargs['url']:
                raise PermissionDenied()

            # Check if the current user is on the meeting's membership
            repetition = MeetingRepetition.objects.get(pk=int(request.POST["repetition"]))
            meeting = repetition.meeting

            # if user is assistant, then updating RSVP for his boss -- find real user
            the_user = None
            membership = request.user.get_membership(account)
            if membership.role == membership.ROLES.assistant:
                for boss in membership.get_bosses():
                    if meeting.check_user_is_member(boss.user):
                        the_user = boss.user
                        break

            # user is not assistant -- check if he is invited to the meeting
            elif meeting.check_user_is_member(request.user):
                the_user = request.user

            if not the_user:
                raise PermissionDenied()

            form = RsvpResponseForm(request.POST)
            if form.is_valid():
                # Create or update the RSVP response (update == create newer one anyway, so that history is kept)
                if meeting.repeat_type and request.POST.get('for_repetition', 'false') == 'true':
                    rsvp = RsvpResponse.objects.create(meeting=meeting, meeting_repetition=repetition, user=the_user)
                else:
                    rsvp = RsvpResponse.objects.create(meeting=meeting, user=the_user)

                response = form.cleaned_data['response_text']
                rsvp.response = rsvp.response_from_string(response)
                rsvp.accept_type = form.cleaned_data['accept_type']
                rsvp.note = form.cleaned_data['note']
                rsvp.save()

                return self.render_to_json_response({'repetition': repetition.pk,
                                                     'account': account.pk,
                                                     'response': response})
            else:
                return self.render_to_json_response({'error': 'Form data is invalid',
                                                     'errors': form.errors.as_json()}, status=400)

        except PermissionDenied:
            return self.render_to_json_response({'error': 'Permission denied'}, status=403)
        except Meeting.DoesNotExist:
            return self.render_to_json_response({'error': 'Meeting not found'}, status=404)
        except (KeyError, ValueError):
            return self.render_to_json_response({'error': 'Unknown value'}, status=400)
