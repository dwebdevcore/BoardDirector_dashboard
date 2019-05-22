# -*- coding: utf-8 -*-
# from django.conf.urls import patterns
from django.conf.urls import include
from django.conf.urls import url
from django.views.generic.base import TemplateView

from registration.backends.default.views import ActivationView
from registration.backends.default.views import RegistrationView, FrameRegistrationView


urlpatterns = [
    url(r'^activate/complete/$',
        TemplateView.as_view(template_name='registration/activation_complete.html'),
        name='registration_activation_complete'),
    # Activation keys get matched by \w+ instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
    # that way it can return a sensible "invalid key" message instead of a
    # confusing 404.
    url(r'^activate/(?P<activation_key>\w+)/$',
        ActivationView.as_view(),
        name='registration_activate'),
    url(r'^sign-up/$',
        RegistrationView.as_view(),
        name='registration_register'),
    # url(r'^sign-up/complete/$',
    #     TemplateView.as_view(template_name='registration/registration_complete.html'),
    #     name='registration_complete'),
    # url(r'^sign-up/closed/$',
    #     TemplateView.as_view(template_name='registration/registration_closed.html'),
    #     name='registration_disallowed'),

    url(r'', include('registration.auth_urls')),


    # alternates for frames
    url(r'^activate-frame/complete/$',
        TemplateView.as_view(template_name='registration/activation_complete_frame.html'),
        name='registration_activation_complete_frame'),
    url(r'^activate-frame/(?P<activation_key>\w+)/$',
        ActivationView.as_view(template_name='registration/activate_frame.html'),
        name='registration_activate_frame'),
    url(r'^register-frame/$',
        FrameRegistrationView.as_view(template_name='registration/registration_form_frame.html'),
        name='registration_register_frame'),
    url(r'^register-frame/complete/$',
        TemplateView.as_view(template_name='registration/registration_complete.html'),
        name='registration_complete'),
    url(r'^register-frame/error/$',
        TemplateView.as_view(template_name='registration/login_error.html'),
        name='registration_login_error'),
    url(r'^register-frame/closed/$',
        TemplateView.as_view(template_name='registration/registration_closed.html'),
        name='registration_disallowed'),
]
