from django.contrib.auth.tokens import default_token_generator
from rest_framework import viewsets
from rest_framework.response import Response

from common.mixins import LoginRequiredMixin, GetMembershipMixin, ApiInitAccountByUrlMixin
from common.utils import AlmostNoPagination
from permissions.rest_permissions import IsAccountAdminOrReadOnly, CheckAccountUrl
from permissions.mixins import RestPermissionByMethodMixin, RestPermissionMixin
from profiles.models import Membership
from profiles.serializers import MembershipShortSerializer, RestorePasswordSerializer
from registration.forms import ResetPasswordForm


class MembershipViewSet(RestPermissionMixin, RestPermissionByMethodMixin,
                        ApiInitAccountByUrlMixin, GetMembershipMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = MembershipShortSerializer
    permission_classes = [IsAccountAdminOrReadOnly, CheckAccountUrl]
    pagination_class = AlmostNoPagination

    def get_queryset(self):
        return Membership.objects.filter(account=self.get_current_account(), is_active=True)


class CheckEmailViewSet(viewsets.GenericViewSet):
    """
    Pass `?email=some@email.com` to test if user with such email is registered. User is not tested to be within this board.
    So basically any board name like `__generic__` can be used.

    Possible results:

    * `exists` - such email exists and has active users/memberships
    * `inactive` - user is inactive - next registration will make it active again
    * `not-exists` - not exists
    """

    def list(self, request, url):
        email = self.request.query_params.get('email')
        if email:
            if Membership.objects.filter(user__email=email, user__is_active=True, is_active=True).exists():
                return Response({'result': 'exists'})
            elif Membership.objects.filter(user__email=email):
                return Response({'result': 'inactive'})

        return Response({'result': 'not-exists'})


class ResetPasswordViewSet(viewsets.GenericViewSet):
    serializer_class = RestorePasswordSerializer

    def create(self, request, url):
        serializer = RestorePasswordSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        form = ResetPasswordForm(serializer.validated_data)
        if form.is_valid():
            # Copy-paste from django/contrib/auth/views.py:252 - form is csrf-protected and we need to call it inside API
            opts = {
                'use_https': request.is_secure(),
                'token_generator': default_token_generator,
                'from_email': None,
                'email_template_name': 'registration/password_reset_email.html',
                'subject_template_name': 'registration/password_reset_subject.txt',
                'request': request,
                'html_email_template_name': None,
                'extra_email_context': None,
            }
            form.save(**opts)

            return Response({'result': 'ok'})
        else:
            return Response({'result': 'error', 'details': str(form.errors)})
