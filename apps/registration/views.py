# -*- coding: utf-8 -*-
"""
Views which allow users to create and activate accounts.

"""
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _

from accounts.models import Account
from accounts.shortcuts import init_account
from registration.social import cleanup_social_auth_from_session_by_request
from .forms import RegistrationFormUniqueEmail
from accounts.mixins import MembershipQuerysetMixin
from billing.models import Plan
from profiles.models import User, Membership
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin


class _RequestPassingFormView(FormView):
    """
    A version of FormView which passes extra arguments to certain
    methods, notably passing the HTTP request nearly everywhere, to
    enable finer-grained processing.

    """
    def get(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class(request)
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class(request)
        form = self.get_form(form_class)
        if form.is_valid():
            # Pass request to form_valid.
            return self.form_valid(form, request)
        else:
            return self.form_invalid(form)

    def get_form_class(self, request=None):
        return super(_RequestPassingFormView, self).get_form_class()

    def get_form_kwargs(self, request=None, form_class=None):
        return super(_RequestPassingFormView, self).get_form_kwargs()

    def get_initial(self, request=None):
        return super(_RequestPassingFormView, self).get_initial()

    def get_success_url(self, request=None, user=None):
        # We need to be able to use the request and the new user when
        # constructing success_url.
        return super(_RequestPassingFormView, self).get_success_url()

    def form_valid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_valid(form)

    def form_invalid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_invalid(form)


class RegistrationView(_RequestPassingFormView):
    """
    Base class for user registration views.

    """
    disallowed_url = 'registration_disallowed'
    form_class = RegistrationFormUniqueEmail
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    success_url = None
    template_name = 'registration/registration_form.html'
    email_dup_error = _('This email address is already in use. Please supply a different email address.')
    pass_wrong_error = _('Please enter a correct email address and password. Note that both fields may be case-sensitive.')

    def dispatch(self, request, *args, **kwargs):
        """
        Check that user signup is allowed before even bothering to
        dispatch or do other processing.

        """
        if not self.registration_allowed(request):
            return redirect(self.disallowed_url)
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)

    def form_invalid(self, form, request=None):
        if 'email' in form.errors and self.email_dup_error in form.errors['email']:
            if len(form.errors) == 1:
                email = self.request.POST.get('email').strip()
                user = User.objects.get(email__iexact=email)
                if not user.check_password(form.cleaned_data['password1']):
                    form.errors['email'].insert(0, self.pass_wrong_error)
                    return super(RegistrationView, self).form_invalid(form)

                try:
                    plan = Plan.objects.get(name=self.request.GET.get('plan', Plan.DEFAULT_PLAN))
                except Plan.DoesNotExist:
                    plan = Plan.objects.get(name=Plan.DEFAULT_PLAN)

                url = form.cleaned_data['url']
                name = form.cleaned_data['name']

                account = Account.objects.create(name=name, url=url, plan=plan)
                init_account(account, user)

                # Otherwise it won't reset pipeline and will cycle back and forth here.
                cleanup_social_auth_from_session_by_request(self.request)
                return HttpResponseRedirect(reverse('registration_activation_complete_frame'))
            else:
                index = next((i for i in range(len(form.errors['email'])) if form.errors['email'][i] == self.email_dup_error), None)
                if index is not None:
                    form.errors['email'].pop(index)

        return super(RegistrationView, self).form_invalid(form)

    def form_valid(self, form, request=None):
        new_user = self.register(request, **form.cleaned_data)
        success_url = self.get_success_url(request, new_user)

        # success_url may be a simple string, or a tuple providing the
        # full argument set for redirect(). Attempting to unpack it
        # tells us which one it is.
        try:
            to, args, kwargs = success_url
            return redirect(to, *args, **kwargs)
        except ValueError:
            return redirect(success_url)

    def registration_allowed(self, request):
        """
        Override this to enable/disable user registration, either
        globally or on a per-request basis.

        """
        return True

    def register(self, request, **cleaned_data):
        """
        Implement user-registration logic here. Access to both the
        request and the full cleaned_data of the registration form is
        available here.

        """
        raise NotImplementedError


class ActivationView(TemplateView):
    """
    Base class for user activation views.

    """
    http_method_names = ['get']
    template_name = 'registration/activate.html'

    def get(self, request, *args, **kwargs):
        activated_user = self.activate(request, *args, **kwargs)
        if activated_user:
            success_url = self.get_success_url(request, activated_user)
            try:
                to, args, kwargs = success_url
                return redirect(to, *args, **kwargs)
            except ValueError:
                return redirect(success_url)
        return super(ActivationView, self).get(request, *args, **kwargs)

    def activate(self, request, *args, **kwargs):
        """
        Implement account-activation logic here.

        """
        raise NotImplementedError

    def get_success_url(self, request, user):
        raise NotImplementedError


class ChangeMembersPassword(MembershipQuerysetMixin, PermissionMixin, FormView):
    permission = (Membership, PERMISSIONS.edit)
    template_name = 'registration/password_member_change_form.html'
    form_class = SetPasswordForm

    def get_success_url(self, **kwargs):
        return reverse('profiles:detail', kwargs={'pk': self.kwargs['pk']})

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk']).user

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.get_object(), **self.get_form_kwargs())

    def form_valid(self, form):
        form.save()
        self.get_success_message()
        return super(ChangeMembersPassword, self).form_valid(form)

    def get_success_message(self):
        messages.success(self.request, _('Password was changed successfully.'))


class SwitchGuestView(MembershipQuerysetMixin, PermissionMixin, SingleObjectMixin, RedirectView):
    permission = (Membership, PERMISSIONS.edit)

    def get_redirect_url(self, *args, **kwargs):
        membership = self.get_object()
        if membership.is_guest:
            membership.role = Membership.ROLES.member
        else:
            membership.role = Membership.ROLES.guest

        membership.custom_role_name = ''
        membership.save()

        return reverse('profiles:edit', kwargs={'pk': kwargs['pk']})


