from django.db.transaction import atomic
from rest_framework import viewsets, permissions
from rest_framework.decorators import list_route
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Account
from accounts.serializers import AccountSerializer
from accounts.shortcuts import init_account
from billing.models import Plan


class RequireAdminToUpdateDelete(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS \
               or request.method in ['POST'] \
               or request.user.is_authenticated and request.user.get_membership(get_object_or_404(Account.objects.all(), pk=view.kwargs.get('pk'))).is_admin


class AccountViewSet(viewsets.ModelViewSet):
    """
    Accounts viewset:

    - requires auth for most actions
    - returns list of available accounts for current user
    - user can `POST` to create new account (and become admin of it)
    - `is_admin` member can update/delete account
    - `/check-exists?url=something` route checks account for existence, possible responses:

        * `exists` - such url exists
        * `inactive` - user is inactive - pretty the same as `exists` for purpose of registration
        * `not-exists` - not exists

    """
    permission_classes = [IsAuthenticated, RequireAdminToUpdateDelete]
    serializer_class = AccountSerializer

    def get_queryset(self):
        return self.request.user.accounts.filter(is_active=True).order_by('name')

    @atomic
    def perform_create(self, serializer):
        if 'plan' not in serializer.validated_data:
            serializer.validated_data['plan'] = Plan.objects.get(pk=Plan.DEFAULT_PLAN)
        serializer.save()
        account = serializer.instance
        init_account(account, self.request.user)

    @list_route(permission_classes=[])
    def check_exists(self, request):
        url = self.request.query_params.get('url')
        if url:
            if Account.objects.filter(url=url, is_active=True).exists():
                return Response({'result': 'exists'})
            elif Account.objects.filter(url=url):
                return Response({'result': 'inactive'})

        return Response({'result': 'not-exists'})

