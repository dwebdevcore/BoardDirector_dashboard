from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication


class RestTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        from common.models import AuthToken

        try:
            token = AuthToken.objects.select_related('user').get(token=key)
        except AuthToken.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        if token.disabled:
            raise exceptions.AuthenticationFailed(_('Token is disabled (logout).'))

        if token.created <= timezone.now() - timedelta(days=settings.REST_TOKEN_MAX_AGE_DAYS):
            raise exceptions.AuthenticationFailed(_('Token is too old, authorize again.'))

        return token.user, token
