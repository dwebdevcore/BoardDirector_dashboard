# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from six import text_type
from social_core.exceptions import AuthAlreadyAssociated, AuthException
import requests
import pytz

from accounts.account_helper import get_current_account
from common.utils import get_ip_address_from_request
from meetings.models import CalendarConnection


class TimezoneMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user_time_zone = request.session.get('user_time_zone', None)
        try:
            if user_time_zone is None:
                account = get_current_account(request)
                if request.user.is_authenticated and account:
                    membership = request.user.get_membership(account)
                    user_time_zone = self.timezone_for_membership(request, membership)

            if user_time_zone:
                request.session['user_time_zone'] = user_time_zone
                timezone.activate(pytz.timezone(user_time_zone))

        except Exception as e:
            request.session['user_time_zone'] = timezone.get_current_timezone().zone

    @staticmethod
    def timezone_for_membership(request, membership):
        if membership.timezone:
            user_time_zone = membership.timezone.zone
        else:
            user_ip = get_ip_address_from_request(request)
            freegeoip_resp = requests.get('http://freegeoip.net/json/{0}'.format(user_ip))
            freegeoip_resp_json = freegeoip_resp.json()
            user_time_zone = freegeoip_resp_json['time_zone']
        return user_time_zone

    @staticmethod
    def reset_timezone(request, membership):
        user_time_zone = TimezoneMiddleware.timezone_for_membership(request, membership)
        request.session['user_time_zone'] = user_time_zone
        timezone.activate(pytz.timezone(user_time_zone))


class CurrentAccountMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Just ensure it's called and thus request.current_account is initialized
        get_current_account(request)


class ForceSSLMiddleware(MiddlewareMixin):
    """
    Redirects all (non-DEBUG) requests to go through SSL.

    Picks up the `HTTP_X_FORWARDED_PROTO` proxy header set by Heroku.

    Also sets the "Strict-Transport-Security" header for 600 seconds so that
    compliant browsers force all requests to this domain to use SSL.
    Can be disabled in settings:

        SSL_USE_STS_HEADER = False
    """

    SSL_HEADER = getattr(settings, "SECURE_PROXY_SSL_HEADER", ('', ''))
    HTTP_X_FORWARDED_PROTO, HTTPS = SSL_HEADER

    def process_request(self, request):
        if not any([
            settings.DEBUG,
            request.is_secure(),
                    request.META.get(self.HTTP_X_FORWARDED_PROTO, '') == self.HTTPS
        ]):
            return self._redirect(request)

    def process_response(self, request, response):
        return self._response_sts(response)

    def _redirect(self, request):
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError('Django can\'t perform a SSL redirect while maintaining POST data. '
                               'Please structure your views so that redirects only occur during GETs.')

        url = request.build_absolute_uri(request.get_full_path())
        secure_url = url.replace("http://", "https://")
        return self._response_sts(HttpResponsePermanentRedirect(secure_url))

    def _response_sts(self, response):
        if not getattr(settings, "SSL_USE_STS_HEADER", True):
            return response

        response['Strict-Transport-Security'] = "max-age=600"
        return response


class CatchSocialException(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, AuthAlreadyAssociated) and not request.user.is_anonymous:
            # Redirect to disable refresh, which causes AuthCancelled
            return redirect('profiles:already_associated')
        elif isinstance(exception, AuthException):
            messages.error(request, text_type(exception))
            return redirect('registration_login_error')


class DebugRequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to temporary enable to log more information about requests
    """

    def process_response(self, request, response):
        message = "account: {account}\tuser: {user}\t{method}\t{path}\t-->\t{status}".format(
            method=request.method.ljust(5),
            path=request.path,
            user=request.user,
            account=get_current_account(request),
            status=response.status_code)

        print(message)

        return response
