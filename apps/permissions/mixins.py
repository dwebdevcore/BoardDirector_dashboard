# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from accounts.account_helper import get_current_account, get_current_account_for_url
from permissions.shortcuts import has_role_permission, has_object_permission


# noinspection PyUnresolvedReferences
class PermissionMixin(object):
    def and_permission(self, account, membership):
        return True

    def or_permission(self, account, membership):
        return False

    def get_permission_object(self):
        try:
            return self.get_object()
        except:
            return None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        account = get_current_account(request)
        membership = request.user.get_membership(account)
        model, permission = self.permission
        obj = self.get_permission_object()
        if (self.and_permission(account, membership) and
                ((has_role_permission(membership, model, permission) or has_object_permission(membership, obj, permission)) or
                     self.or_permission(account, membership))):
            return super(PermissionMixin, self).dispatch(request, *args, **kwargs)
        # Soft land folder urls to root folder instead of 403
        if 'folders/' in request.path:
            return redirect('folders:rootfolder_detail', url=account.url)
        raise PermissionDenied()


# noinspection PyUnresolvedReferences
class RestPermissionMixin(object):
    def and_permission(self, account, membership):
        return True

    def or_permission(self, account, membership):
        return False

    def get_permission_object(self):
        try:
            return self.get_object()
        except:
            return None

    def check_permissions(self, request):
        super(RestPermissionMixin, self).check_permissions(request)

        # Manual handling of @login_required to return proper response for API usage (not a redirect)
        if not request.user.is_authenticated:
            self.permission_denied(request)

        account = get_current_account_for_url(request, self.kwargs['url'])
        membership = request.user.get_membership(account)

        if hasattr(self, 'get_model_permission'):  # Support dynamic permissions
            model, permission = self.get_model_permission(request)
        else:
            model, permission = self.permission

        obj = self.get_permission_object()
        if (self.and_permission(account, membership)
            and ((has_role_permission(membership, model, permission) or has_object_permission(membership, obj, permission))
                 or self.or_permission(account, membership))):
            return

        # Soft land folder urls to root folder instead of 403
        if 'folders/' in request.path:
            self.permission_denied(request, "No access to this folder")


class RestPermissionByMethodMixin(object):
    def get_model_permission(self, request):
        if hasattr(self, 'permission_model'):
            model = self.permission_model
        elif hasattr(self, 'get_queryset'):
            model = self.get_queryset().model
        else:
            raise RestPermissionByMethodMixin.Error("Please set permission_model class or implement get_queryset")

        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            permission = 'view'
        elif request.method in ['POST']:
            permission = 'create'
        elif request.method in ['PUT', 'PATCH']:
            permission = 'edit'
        elif request.method in ['DELETE']:
            permission = 'delete'
        else:
            raise RestPermissionByMethodMixin.Error("Unknown method " + request.method)

        return model, permission

    class Error(Exception):
        pass
