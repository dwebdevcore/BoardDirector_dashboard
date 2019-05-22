# -*- coding: utf-8 -*-
from __future__ import print_function
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, FormView, RedirectView, TemplateView
from django.views.generic.edit import View

from accounts.account_helper import get_current_account
from committees.models import Committee
from common.mixins import (ActiveTabMixin, AjaxableResponseMixin, RecentActivityMixin, SelectBoardRequiredMixin,
                           CurrentAccountMixin, LoginRequiredMixin)
from dashboard.models import RecentActivity
from documents.forms import DocumentAddForm, FolderAddForm, FolderEditForm, FolderMoveForm
from documents.models import Folder, Document, AuditTrail
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin
from permissions.models import ObjectPermission
from permissions.shortcuts import has_object_permission, filter_by_permission
from permissions.utils import get_contenttype

ALL_COMMITTEES = -1


class FolderQuerysetMixin(object):
    def get_queryset(self):
        account = get_current_account(self.request)
        queryset = Folder.objects.filter(account=account)
        return queryset


class DocumentAddView(ActiveTabMixin, AjaxableResponseMixin, CurrentAccountMixin, RecentActivityMixin,
                      SelectBoardRequiredMixin, FolderQuerysetMixin, PermissionMixin, FormView):
    permission = (Folder, PERMISSIONS.add)
    form_class = DocumentAddForm
    template_name = 'documents/document_add.html'
    active_tab = 'folders'

    def and_permission(self, account, membership):
        folder = self.get_permission_object()
        self.folder = folder
        return folder.can_add_files

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])

    def form_valid(self, form):
        self.object = get_current_account(self.request)
        if form.cleaned_data.get('notify_group'):
            notify_group = int(form.cleaned_data.get('notify_group'))
        else:
            notify_group = None
        notify_me = True if form.cleaned_data.get('notify_me') == 'true' else False
        documents = []
        if form.cleaned_data['uploaded_file']:
            docs = form.cleaned_data['uploaded_file'].split(',')
            for d in docs:
                try:
                    doc = Document.objects.get(id=d)
                    doc.account = self.object
                    doc.folder = self.folder
                    doc.created_at = timezone.now()
                    doc.save()
                    documents.append(doc)
                except (Document.DoesNotExist, Folder.DoesNotExist):
                    pass
        if self.request.POST.get('new_document'):
            self.save_recent_activity(action_flag=RecentActivity.ADDITION)
            self.get_success_add_message()
        else:
            self.save_recent_activity(action_flag=RecentActivity.CHANGE)
            self.get_success_change_message()
            if get_current_account(self.request).send_notification:
                user_membership = self.request.user.get_membership(self.object)
                if notify_group:
                    if notify_group != ALL_COMMITTEES:
                        members = list(Committee.objects.get(id=notify_group).memberships.all().
                                       exclude(Q(user=user_membership.user) | Q(user__is_active=False)).
                                       select_related('User'))
                    else:
                        members = list(self.object.memberships.all().
                                       exclude(Q(user=user_membership.user) | Q(user__is_active=False)).
                                       select_related('User'))
                    if notify_me:
                        members.append(user_membership)
                    for doc in documents:
                        doc.send_notification_email(members)

        return super(DocumentAddView, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(DocumentAddView, self).get_context_data(*args, **kwargs)
        context['folder'] = self.folder
        return context

    def get_success_add_message(self):
        messages.success(self.request, _('Documents were added successfully.'))

    def get_success_change_message(self):
        messages.success(self.request, _('Documents were edit successfully.'))

    def get_success_url(self):
        if 'back' in self.request.POST:
            return self.request.POST['back']
        else:
            return reverse('folders:folder_detail', kwargs={'url': get_current_account(self.request).url,
                                                            'slug': self.kwargs['slug']})


class FolderContextMixin(object):
    def get_folder(self):
        return self.get_object()

    def get_context_data(self, *args, **kwargs):
        context = super(FolderContextMixin, self).get_context_data(*args, **kwargs)
        folder = self.get_folder()
        if not folder:
            return context  # Exit in case of usage outside of Folders section, like committees, etc.

        account = get_current_account(self.request)
        membership = self.request.user.get_membership(account)
        # Folder forms
        context['folder_add_form'] = FolderAddForm()
        context['folder_edit_form'] = FolderEditForm()
        context['folder_move_form'] = FolderMoveForm()
        # Ordered items (files & folders)
        search = self.request.GET.get('search', None)
        if search:
            descendants = folder.get_descendants()
            sub_folders = descendants.filter(name__icontains=search)
            documents = Document.objects.filter(account=folder.account, folder__in=descendants, name__icontains=search)
        else:
            sub_folders = folder.children.all()
            documents = folder.documents.all()

        documents = documents.select_related('user')

        items = filter_by_permission(sub_folders, membership, PERMISSIONS.view)
        filtered_documents = filter_by_permission(documents, membership, PERMISSIONS.view)
        Document.prefetch_revisions(filtered_documents)
        items += filtered_documents

        # Order items
        default_ordering = 'date' if folder.name == 'Meeting Documents' else 'default'
        ordering = self.request.GET.get('o', default_ordering).lower()
        items = FolderContextMixin.sort_items(items, ordering)

        # append members private folder
        if folder.is_account_root and not search:
            try:
                private_folder = membership.private_folder
            except Folder.DoesNotExist:
                private_folder = Folder.objects.create_membership_folder(membership)
            items.append(private_folder)
            context['show_shared_folder'] = True
        # Set helper attributes
        FolderContextMixin.set_help_attrs(items)
        context['items'] = items
        context['ordering'] = ordering
        context['search'] = search
        qs = folder.get_ancestors(include_self=True).filter(membership_id=membership.id)
        membership_ancestor = qs[0] if len(qs) > 0 else None
        context['membership_ancestor'] = membership_ancestor
        return context

    @staticmethod
    def sort_items(items, ordering):
        reverse = ordering.startswith('-')
        if 'name' in ordering:
            items = sorted(items, key=lambda i: i.name, reverse=reverse)
        elif 'date' in ordering:
            items = sorted(items, key=lambda i: i.sort_date, reverse=reverse)
        elif 'default' in ordering:
            items = sorted(items, key=lambda i: i.ordering)
        return items

    @staticmethod
    def set_help_attrs(items):
        for item in items:
            item.is_file = 'Document' in item.__class__.__name__
            item.is_folder = 'Folder' in item.__class__.__name__


class FolderDetailView(ActiveTabMixin, SelectBoardRequiredMixin,
                       FolderContextMixin, FolderQuerysetMixin, PermissionMixin, DetailView):
    permission = (Folder, PERMISSIONS.view)
    active_tab = 'folders'
    template_name = 'documents/folder_detail.html'

    def and_permission(self, account, membership):
        # View only explicitly allowed folders (usually RolePermission view means can view all)
        return has_object_permission(membership, self.get_object(), PERMISSIONS.view)

    def dispatch(self, request, *args, **kwargs):
        # Redirect account root folder to RootFolder view (hides slug)
        account = get_current_account(request)
        if account:
            # call get object only if user has selected board
            folder = super(FolderDetailView, self).get_object()
            if folder.is_account_root:
                return redirect('folders:rootfolder_detail', url=account.url)
        return super(FolderDetailView, self).dispatch(request, *args, **kwargs)


class RootFolderDetailView(ActiveTabMixin, SelectBoardRequiredMixin,
                           FolderContextMixin, PermissionMixin, DetailView):
    permission = (Folder, PERMISSIONS.view)
    active_tab = 'folders'
    template_name = 'documents/folder_detail.html'

    def get_object(self, queryset=None):
        return Folder.objects.get_account_root(account=get_current_account(self.request))


class RootFolderRedirectView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, **kwargs):
        return reverse_lazy('folders:rootfolder_detail', kwargs={'url': get_current_account(self.request).url})


class SharedFolderView(ActiveTabMixin, SelectBoardRequiredMixin, PermissionMixin, TemplateView):
    permission = (Folder, PERMISSIONS.view)
    active_tab = 'folders'
    template_name = 'documents/shared_folder.html'

    def get_context_data(self, *args, **kwargs):
        context = super(SharedFolderView, self).get_context_data(*args, **kwargs)
        account = get_current_account(self.request)
        membership = self.request.user.get_membership(account)
        # Shared folders
        ct = get_contenttype(Folder)
        shared_folders = []
        for folder in account.folders.filter(protected=False).exclude(level=1):
            if ObjectPermission.objects.filter(Q(role=membership.role) | Q(membership=membership)).filter(content_type=ct, object_id=folder.id).exists():
                shared_folders.append(folder)
        items = shared_folders
        # Shared documents
        ct = get_contenttype(Document)
        shared_documents = []
        for document in account.documents.all():
            if ObjectPermission.objects.filter(Q(role=membership.role) | Q(membership=membership)).filter(content_type=ct, object_id=document.id).exists():
                shared_documents.append(document)
        items += shared_documents
        # Sort
        ordering = self.request.GET.get('o', 'name').lower()
        items = FolderContextMixin.sort_items(items, ordering)
        FolderContextMixin.set_help_attrs(items)
        context['items'] = items
        context['ordering'] = ordering
        context['folder_edit_form'] = FolderEditForm()
        return context


class FolderAddView(AjaxableResponseMixin, SelectBoardRequiredMixin,
                    FolderQuerysetMixin, PermissionMixin, FormView):
    permission = (Folder, PERMISSIONS.add)
    form_class = FolderAddForm
    template_name = 'documents/folder_detail.html'

    def and_permission(self, account, membership):
        parent = self.get_permission_object()
        self.parent = parent
        return parent.can_add_folders

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])

    def form_valid(self, form):
        folder = form.save(commit=False)
        if Folder.objects.filter(parent=self.parent, name__iexact=folder.name).exists():
            # Old json relies on simple array of errors, this is why safe=False
            return JsonResponse([_('Folder with this name already exists, please try other name')], safe=False, status=400)

        folder.parent = self.parent
        folder.account = get_current_account(self.request)
        folder.user = self.request.user
        folder.save()
        self.object = folder  # needed for AjaxableResponseMixin
        return super(FolderAddView, self).form_valid(form)

    def get_success_url(self):
        # not used in folders.js
        return self.object.get_absolute_url()


class FolderEditView(AjaxableResponseMixin, SelectBoardRequiredMixin,
                     FolderQuerysetMixin, PermissionMixin, FormView):
    permission = (Folder, PERMISSIONS.edit)
    form_class = FolderEditForm
    template_name = 'documents/folder_detail.html'

    def and_permission(self, account, membership):
        folder = self.get_permission_object()
        self.object = folder
        return not folder.protected

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])

    def get_form_kwargs(self):
        kwargs = super(FolderEditView, self).get_form_kwargs()
        kwargs['instance'] = self.object
        return kwargs

    def form_valid(self, form):
        folder = form.save(commit=False)
        if Folder.objects.filter(parent=folder.parent, name__iexact=folder.name).exclude(pk=folder.pk).exists():
            # Old json relies on simple array of errors, this is why safe=False
            return JsonResponse([_('Folder with this name already exists, please try other name')], safe=False, status=400)

        folder.user = self.request.user
        folder.save()
        self.object = folder  # needed for AjaxableResponseMixin
        return super(FolderEditView, self).form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class FolderDeleteView(AjaxableResponseMixin, SelectBoardRequiredMixin,
                       FolderQuerysetMixin, PermissionMixin, View):
    permission = (Folder, PERMISSIONS.delete)

    def and_permission(self, account, membership):
        folder = self.get_permission_object()
        self.object = folder
        return not folder.protected

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])

    def delete_folder(self, folder):
        if folder.protected:
            raise PermissionDenied()
        # Recursion for subfolders
        for subfolder in folder.children.all():
            self.delete_folder(subfolder)
        # Delete documents
        for document in folder.documents.all():
            # create AuditTrail from deleted document
            AuditTrail.objects.create(
                name=document.name,
                file=document.file,
                type=document.type,
                user_id=self.request.user.id,
                change_type=AuditTrail.DELETED,
                latest_version=document.id,
                created_at=document.created_at,
            )
            RecentActivity.objects.filter(
                object_id=document.id,
                content_type_id=ContentType.objects.get_for_model(document)
            ).delete()
            document.delete()
        # Delete folder
        folder.delete()

    def post(self, request, *args, **kwargs):
        self.delete_folder(self.object)
        return self.render_to_json_response({})


class FolderMoveView(AjaxableResponseMixin, FolderContextMixin, FolderQuerysetMixin,
                     SelectBoardRequiredMixin, PermissionMixin, View):
    permission = (Folder, PERMISSIONS.edit)

    def and_permission(self, account, membership):
        folder = self.get_permission_object()
        self.object = folder
        target = get_object_or_404(self.get_queryset(), slug=self.request.POST.get('target_slug'))
        return not folder.protected and target.can_add_folders and has_object_permission(membership, target, PERMISSIONS.add)

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])

    def post(self, request, *args, **kwargs):
        folder = self.object
        form = FolderMoveForm(request.POST)
        if form.is_valid():
            target = get_object_or_404(self.get_queryset(), slug=form.cleaned_data['target_slug'])
            folder.parent = target
            folder.save()
            return self.render_to_json_response({'result': 'ok'})
        else:
            # QUESTION: Is there already converter ErrorDict -> Dict[String, String]?
            return self.render_to_json_response({'result': 'failed', 'errors': 'TODO'})


class FolderOrderingAjaxView(AjaxableResponseMixin, ActiveTabMixin, SelectBoardRequiredMixin,
                             FolderContextMixin, FolderQuerysetMixin, PermissionMixin, View):

    permission = (Document, PERMISSIONS.add)

    def and_permission(self, account, membership):
        folder = self.get_permission_object()
        self.object = folder
        self.membership = membership
        return membership.is_admin

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])

    def post(self, request, *args, **kwargs):

        # read posted data -- re-ordered list of folders and files
        ordering = {'file': {}, 'folder': {}}
        for pk in request.POST.keys():
            if not pk or pk.find('ordering') < 0:
                continue
            pv = request.POST.getlist(pk)
            if pv and len(pv) == 3 \
                    and pv[1] in ['folder', 'file'] and pv[0].isdigit() and pv[2].isdigit():
                ordering[pv[1]][int(pv[2])] = int(pv[0]) + 1

        folder = self.object

        if len(ordering['file']) > 0:
            items = folder.documents.all()
            for item in items:
                if item.id in ordering['file']:
                    item.ordering = ordering['file'][item.id]
                    item.save(update_fields=['ordering'])

        if len(ordering['folder']) > 0:
            items = folder.children.all()
            for item in items:
                if item.id in ordering['folder']:
                    item.ordering = ordering['folder'][item.id]
                    item.save(update_fields=['ordering'])

        return self.render_to_json_response({'result': 'ok'})
