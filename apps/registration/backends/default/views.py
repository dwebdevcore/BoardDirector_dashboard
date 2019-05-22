# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from registration import signals

from accounts.models import Account
from billing.models import BillingSettings, Plan
from committees.models import Committee
from profiles.models import Membership
from registration.models import RegistrationProfile
from registration.views import ActivationView as BaseActivationView
from registration.views import RegistrationView as BaseRegistrationView


class RegistrationView(BaseRegistrationView):
    """
    A registration backend which follows a simple workflow:

    1. User signs up, inactive account is created.

    2. Email is sent to user with activation link.

    3. User clicks activation link, account is now active.

    Using this backend requires that

    * ``registration`` be listed in the ``INSTALLED_APPS`` setting
      (since this backend makes use of models defined in this
      application).

    * The setting ``ACCOUNT_ACTIVATION_DAYS`` be supplied, specifying
      (as an integer) the number of days from registration during
      which a user may activate their account (after that period
      expires, activation will be disallowed).

    * The creation of the templates
      ``registration/activation_email_subject.txt`` and
      ``registration/activation_email.txt``, which will be used for
      the activation email. See the notes for this backends
      ``register`` method for details regarding these templates.

    Additionally, registration can be temporarily closed by adding the
    setting ``REGISTRATION_OPEN`` and setting it to
    ``False``. Omitting this setting, or setting it to ``True``, will
    be interpreted as meaning that registration is currently open and
    permitted.

    Internally, this is accomplished via storing an activation key in
    an instance of ``registration.models.RegistrationProfile``. See
    that model and its custom manager for full documentation of its
    fields and supported operations.

    """

    def get_context_data(self, **kwargs):
        data = super(RegistrationView, self).get_context_data(**kwargs)
        is_social = self.is_social()

        data['is_social'] = is_social
        data['social_mapping'] = settings.SOCIAL_MAPPING
        if is_social:
            details = self.request.session.get('social_details')
            data['backend'] = self.request.session.get('social_last_backend')
            data['email'] = details and details.get('email')
            data['social_info'] = settings.SOCIAL_MAPPING.get(data['backend'])

        return data

    def is_social(self):
        return self.request.session.get('social_details')

    def get_form(self, form_class=None):
        form = super(RegistrationView, self).get_form(form_class)
        if self.is_social():
            form.fields['password1'].required = False

        return form

    def register(self, request, **cleaned_data):
        """
        Given a username, email address and password, register a new
        user account, which will initially be inactive.

        Along with the new ``User`` object, a new
        ``registration.models.RegistrationProfile`` will be created,
        tied to that ``User``, containing the activation key which
        will be used for this account.

        An email will be sent to the supplied email address; this
        email should contain an activation link. The email will be
        rendered using two templates. See the documentation for
        ``RegistrationProfile.send_activation_email()`` for
        information about these templates and the contexts provided to
        them.

        After the ``User`` and ``RegistrationProfile`` are created and
        the activation email is sent, the signal
        ``registration.signals.user_registered`` will be sent, with
        the new ``User`` as the keyword argument ``user`` and the
        class of this backend as the sender.

        """
        email, password = cleaned_data['email'], cleaned_data['password1']
        site = get_current_site(request)

        try:
            plan = Plan.objects.get(name=request.GET.get('plan', Plan.DEFAULT_PLAN))
        except Plan.DoesNotExist:
            plan = Plan.objects.get(name=Plan.DEFAULT_PLAN)

        # NOTE: accounts.shortcuts also has this functionality, it can be refactored (& tested) someday to remove duplication
        account = Account.objects.create(name=cleaned_data['name'], url=cleaned_data['url'], plan=plan)
        BillingSettings.objects.create(name=cleaned_data['name'], mail=cleaned_data['email'], account=account)

        if self.is_social():
            details = self.request.session.get('social_details') or {}  # {} just in case
            # User is created active and without
            new_user = get_user_model().objects.create_user(email, password)
            membership = Membership.objects.create(user=new_user, account=account, is_admin=True,
                                                   first_name=details.get('first_name'), last_name=details.get('last_name'))
        else:
            new_user = RegistrationProfile.objects.create_inactive_user(email, password, site, account)
            membership = Membership.objects.create(user=new_user, account=account, is_admin=True)

        board_of_directors = Committee.objects.create(name=_('Full Board'), account=account)
        board_of_directors.chairman.add(membership)
        membership.committees.add(board_of_directors)
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user

    def registration_allowed(self, request):
        """
        Indicate whether account registration is currently permitted,
        based on the value of the setting ``REGISTRATION_OPEN``. This
        is determined as follows:

        * If ``REGISTRATION_OPEN`` is not specified in settings, or is
          set to ``True``, registration is permitted.

        * If ``REGISTRATION_OPEN`` is both specified and set to
          ``False``, registration is not permitted.

        """
        return getattr(settings, 'REGISTRATION_OPEN', True)

    # noinspection PyMethodOverriding
    def get_success_url(self, request, user):
        """
        Return the name of the URL to redirect to after successful
        user registration.

        """
        if self.is_social():
            # Hacky but let it be, good way would be to inject it into pipeline somehow
            request.session['registered_user_id'] = user.id
            return 'social:complete', (), {'backend': self.request.session.get('social_last_backend')}
        else:
            return 'registration_complete', (), {}


class FrameRegistrationView(RegistrationView):
    template_name = 'registration/registration_form_frame.html'

    def get(self, *args, **kwargs):
        resp = super(FrameRegistrationView, self).get(*args, **kwargs)
        return resp

    def post(self, *args, **kwargs):
        resp = super(RegistrationView, self).post(*args, **kwargs)
        if self.request.is_ajax():
            if type(resp) is not HttpResponseRedirect:
                data = json.dumps({
                    'signed_in': False,
                    'html': resp.rendered_content,
                })
            else:
                data = json.dumps({
                    'signed_in': True,
                    'redirect': resp._headers['location'][1],
                })

            return HttpResponse(data, content_type='application/json')

        return resp


class ActivationView(BaseActivationView):
    # noinspection PyMethodOverriding
    def activate(self, request, activation_key):
        """
        Given an an activation key, look up and activate the user
        account corresponding to that key (if possible).

        After successful activation, the signal
        ``registration.signals.user_activated`` will be sent, with the
        newly activated ``User`` as the keyword argument ``user`` and
        the class of this backend as the sender.

        """
        activated_user = RegistrationProfile.objects.activate_user(activation_key)
        if activated_user:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated_user,
                                        request=request)
        return activated_user

    def get_success_url(self, request, user):
        return ('registration_activation_complete', (), {})
