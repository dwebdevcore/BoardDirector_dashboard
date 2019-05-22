# -*- coding: utf-8 -*-
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic.edit import BaseFormView, FormView
from django.views.generic import TemplateView

from documents.forms import ShareAddForm, ShareDeleteForm
from documents.models import Folder
from common.mixins import AjaxableResponseMixin, SelectBoardRequiredMixin, GetMembershipMixin
from permissions import PERMISSIONS
from permissions.models import ObjectPermission
from permissions.mixins import PermissionMixin
from permissions.utils import get_contenttype
from .folder import FolderQuerysetMixin


class GetFolderDocumentMixin(object):
    def get_objects(self):
        if not hasattr(self, '_objects'):
            # Get folder and document based on GET param
            folder = get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])
            document_id = self.request.GET.get('document_id')
            document = get_object_or_404(folder.documents.all(), id=document_id) if document_id else None
            self._objects = (folder, document)
        return self._objects

    def get_permission_object(self):
        folder, document = self.get_objects()
        return document if document else folder

    def get_object_permissions(self):
        return self.get_permission_object().permissions.all()

    def get_context_data(self, *args, **kwargs):
        context = super(GetFolderDocumentMixin, self).get_context_data(*args, **kwargs)
        folder, document = self.get_objects()
        context['folder'] = folder
        context['document'] = document
        context['object'] = document or folder
        return context


class PermissionDetailView(SelectBoardRequiredMixin, GetMembershipMixin,
                           FolderQuerysetMixin, GetFolderDocumentMixin, PermissionMixin, TemplateView):
    permission = (Folder, PERMISSIONS.share)
    form_class = ShareAddForm
    template_name = 'documents/includes/folder_share.html'

    def get_context_data(self, *args, **kwargs):
        context = super(PermissionDetailView, self).get_context_data(*args, **kwargs)
        permissions = self.get_object_permissions()
        view_permissions = {}
        edit_permissions = {}
        # list only 'view' and 'edit' permissions
        for obj_perm in permissions:
            assert isinstance(obj_perm, ObjectPermission)
            key = (0, obj_perm.membership_id) if obj_perm.membership_id else (1, obj_perm.role)
            if obj_perm.permission == PERMISSIONS.view:
                view_permissions[key] = obj_perm
            elif obj_perm.permission == PERMISSIONS.edit:
                edit_permissions[key] = obj_perm

        for key in edit_permissions.keys():
            del view_permissions[key]

        context['view_permissions'] = sorted(view_permissions.values(), key=lambda p: (1, p.membership.get_full_name()) if p.membership else (0, p.role))
        context['edit_permissions'] = sorted(edit_permissions.values(), key=lambda p: (1, p.membership.get_full_name()) if p.membership else (0, p.role))
        context['form'] = ShareAddForm(account=self.get_current_account())
        return context


class PermissionAddView(AjaxableResponseMixin, SelectBoardRequiredMixin, GetMembershipMixin,
                        FolderQuerysetMixin, GetFolderDocumentMixin, PermissionMixin, FormView):
    permission = (Folder, PERMISSIONS.share)
    form_class = ShareAddForm
    template_name = 'documents/includes/folder_share_form.html'

    def get_form_kwargs(self):
        kwargs = super(PermissionAddView, self).get_form_kwargs()
        kwargs['account'] = self.get_current_account()
        return kwargs

    def form_invalid(self, form):
        return HttpResponseBadRequest()

    def form_valid(self, form):
        memberships = form.cleaned_data['memberships']
        role = None if memberships else form.cleaned_data['role']
        permission = form.cleaned_data['permission']
        perm_obj = self.get_permission_object()
        self.do_add_permissions(memberships, permission, role, perm_obj)

        return self.render_to_json_response({})

    @staticmethod
    def do_add_permissions(memberships, permission, role, perm_obj):
        permissions = tuple()
        if permission == PERMISSIONS.view:
            permissions = (PERMISSIONS.view,)
        elif permission == PERMISSIONS.edit:
            # 'edit' implicitly includes view, add, edit, delete
            permissions = (PERMISSIONS.view, PERMISSIONS.add, PERMISSIONS.edit, PERMISSIONS.delete)
        memberships_list = memberships if memberships else [None]
        if memberships or role:
            for perm in permissions:
                for membership in memberships_list:
                    ObjectPermission.objects.get_or_create(
                        role=role,
                        membership=membership,
                        content_type=get_contenttype(perm_obj),
                        object_id=perm_obj.id,
                        permission=perm,
                    )


class PermissionDeleteView(AjaxableResponseMixin, SelectBoardRequiredMixin, GetMembershipMixin,
                           FolderQuerysetMixin, GetFolderDocumentMixin, PermissionMixin, BaseFormView):
    permission = (Folder, PERMISSIONS.share)
    form_class = ShareDeleteForm

    def form_invalid(self, form):
        return HttpResponseBadRequest()

    def form_valid(self, form):
        permissions = self.get_object_permissions()
        obj_perm = get_object_or_404(permissions, id=form.cleaned_data['object_permission_id'])
        # delete all permissions for given Role or Membership
        permissions.filter(
            role=obj_perm.role,
            membership=obj_perm.membership,
        ).delete()
        return self.render_to_json_response({})
