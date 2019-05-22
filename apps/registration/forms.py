# -*- coding: utf-8 -*-
"""
Forms and validation code for user registration.

Note that all of these forms assume Django's bundle default ``User``
model; since it's not possible for a form to anticipate in advance the
needs of custom user models, you will need to write your own forms if
you're using a custom model.

"""

from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from accounts.models import Account
from common.models import TemplateModel
from profiles.models import User


class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    required_css_class = 'required'

    email = forms.EmailField(label=_('E-mail'))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'onkeyup': "passwordStrength(this.value)"}),
                                label=_('Password'))
    url = forms.SlugField(label=_('Board director url'), max_length=255,
                          widget=forms.DateInput(attrs={'placeholder': _('yourorganization')}),
                          error_messages={
                              'invalid': _('Company URL may only contain letters, numbers, underscores or hyphens.')})
    name = forms.CharField(label=_('Company or organization name'), max_length=255,
                           widget=forms.TextInput(attrs={'placeholder': 'Acme, Inc.'}))

    def clean_url(self):
        url = self.cleaned_data['url']
        if Account.objects.filter(url=url).exists():
            raise forms.ValidationError(_('This url is already in use. Please supply a different url.'))
        return url


class RegistrationFormTermsOfService(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which adds a required checkbox
    for agreeing to a site's Terms of Service.

    """
    tos = forms.BooleanField(widget=forms.CheckboxInput,
                             label=_(u'I have read and agree to the Terms of Service'),
                             error_messages={'required': _("You must agree to the terms to register")})


class RegistrationFormUniqueEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.

    """

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.

        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(
                _("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']


class RegistrationFormNoFreeEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which disallows registration with
    email addresses from popular free webmail services; moderately
    useful for preventing automated spam registrations.

    To change the list of banned domains, subclass this form and
    override the attribute ``bad_domains``.

    """
    bad_domains = ['aim.com', 'aol.com', 'email.com', 'gmail.com',
                   'googlemail.com', 'hotmail.com', 'hushmail.com',
                   'msn.com', 'mail.ru', 'mailinator.com', 'live.com',
                   'yahoo.com']

    def clean_email(self):
        """
        Check the supplied email address against a list of known free
        webmail domains.

        """
        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in self.bad_domains:
            raise forms.ValidationError(
                _("Registration using free email addresses is prohibited. Please supply a different email address."))
        return self.cleaned_data['email']


class ResetPasswordForm(PasswordResetForm):
    def save(self, domain_override=None, subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html', use_https=None, token_generator=default_token_generator,
             from_email=None, request=None, **kwargs):
        for user in self.get_users(self.cleaned_data['email']):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            if use_https is None:
                use_https = settings.SSL_ON
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(str(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            tmpl = TemplateModel.objects.get(name=TemplateModel.RESET)
            subject = tmpl.title
            email = tmpl.generate(c)
            user.email_user(subject, email, from_email)
