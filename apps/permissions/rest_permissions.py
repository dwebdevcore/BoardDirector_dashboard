from django.shortcuts import get_object_or_404
from rest_framework import permissions

from accounts.account_helper import get_current_account
from accounts.models import Account
from permissions import PERMISSIONS
from permissions.shortcuts import get_object_permissions


class IsAccountAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # To be able to use without Board selection in session, i.e. via basic auth
        account = get_current_account(request) or get_object_or_404(Account, url=view.kwargs['url'])

        return (
            request.user
            and request.user.is_authenticated
            and (
                request.method in permissions.SAFE_METHODS
                and not request.user.get_membership(account).is_guest

                or request.user.get_membership(account).is_admin
            ))


class IsAccountAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # To be able to use without Board selection in session, i.e. via basic auth
        account = get_current_account(request) or get_object_or_404(Account, url=view.kwargs['url'])

        return (
            request.user
            and request.user.is_authenticated
            and request.user.get_membership(account).is_admin
        )


class IsMember(permissions.BasePermission):
    def has_permission(self, request, view):
        # To be able to use without Board selection in session, i.e. via basic auth
        account = get_current_account(request) or get_object_or_404(Account, url=view.kwargs['url'])

        membership = request.user and request.user.is_authenticated and request.user.get_membership(account)
        return (
            membership
            and not membership.is_guest
        )


class CheckAccountUrl(permissions.BasePermission):
    def has_permission(self, request, view):
        account = get_current_account(request)
        return not account or account.url == view.kwargs['url']

    def has_object_permission(self, request, view, obj):
        return obj.account.url == view.kwargs['url']


class RequireObjectEdit(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated \
               and PERMISSIONS.edit in get_object_permissions(request.user.get_membership(get_current_account(request)), obj)


class CheckAccountUrlLambda(permissions.BasePermission):
    def __init__(self, check_lambda):
        self.check_lambda = check_lambda

    def has_object_permission(self, request, view, obj):
        return self.check_lambda(obj, view.kwargs['url'], kw=view.kwargs, view=view, request=request)
