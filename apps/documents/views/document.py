# -*- coding: utf-8 -*-
import mimetypes
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from os.path import splitext, basename
from subprocess import PIPE
from wsgiref.util import FileWrapper

import os
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.db.models import F
from django.db.transaction import atomic
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.http.response import BadHeaderError, Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, BaseFormView, View
from rest_framework.authentication import get_authorization_header

from accounts.account_helper import get_current_account
from accounts.models import Account
from common import signals
from common.mixins import AjaxableResponseMixin, RecentActivityMixin, SelectBoardRequiredMixin, MemberNotificationMixin
from dashboard.models import RecentActivity
from documents.forms import DocumentForm, DocumentDeleteForm, DocumentRenameForm, MessageForm, FolderMoveForm
from documents.models import Document, AuditTrail, Folder, Approval
from meetings.models import Meeting
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin
from permissions.shortcuts import has_object_permission

ALL_COMMITTEES = -1


class DocumentQuerysetMixin(object):
    def get_queryset(self):
        account = get_current_account(self.request)
        queryset = Document.objects.filter(account=account)
        return queryset


class DocumentCreateMixin(object):
    """
    Mixin to extract common processing for both plain views and rest views
    """

    def _check_and_update_storage(self, account, size):
        if account.plan.max_storage and account.total_storage + size > account.plan.max_storage:
            return {
                'status': 'error',
                'message': ugettext('Limit of data storage for your billing plan is exceeded,'
                                    ' you can upgrade it in your profile!')
            }

        Account.objects.filter(id=account.id).update(total_storage=F('total_storage') + size)
        return True

    def post_save_actions(self, document, old_doc, meeting):
        if old_doc:
            revisions = AuditTrail.objects.filter(latest_version=old_doc.id)
            revisions.update(latest_version=document.id)

        action_flag = RecentActivity.ADDITION

        if meeting:
            Folder.objects.update_or_create_meeting_folder(meeting)
            document.folder = meeting.folder
            document.save()

        if old_doc:
            action_flag = RecentActivity.CHANGE

            # copy folder & permissions from old document
            # folder
            document.previous_version = old_doc.id
            document.folder = old_doc.folder
            document.save(update_fields=['folder', 'previous_version'])
            # permissions
            for perm in old_doc.permissions.all():
                perm.id = None
                perm.object_id = document.id
                perm.save()

        self.save_recent_activity(action_flag=action_flag)


class DocumentAjaxCreateView(AjaxableResponseMixin, RecentActivityMixin, DocumentCreateMixin,
                             SelectBoardRequiredMixin, CreateView):
    """Has no PermissionMixin because permissions checking is done on folder view."""
    form_class = DocumentForm

    @atomic
    def post(self, request, *args, **kwargs):
        self.object = None
        if 'type' in request.POST:
            file = request.FILES.get(request.POST.get('type'))
            request.FILES['file'] = file
        size = request.FILES['file'].size
        account = get_current_account(request)
        check = self._check_and_update_storage(account, size)
        if check is not True:
            return self.render_to_json_response(check, status=403)

        return super(DocumentAjaxCreateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        document = self.object = form.save(commit=False)
        assert isinstance(document, Document)
        document.account = current_account = get_current_account(self.request)
        if 'type' in self.request.POST:
            for i, t in Document.DOCS_TYPES:
                if t == self.request.POST.get('type'):
                    document.type = i
                    break
        document.user = self.request.user

        old_doc_id = form.data.get('old_document')
        if old_doc_id:
            old_doc_id = int(old_doc_id)
            document.previous_version = old_doc_id

        document.save()

        # Prepare & check data
        action = self.request.POST.get('action')
        meeting_id = self.request.POST.get('meeting')

        if not meeting_id:
            meeting = None
        else:
            meeting = Meeting.objects.get(pk=meeting_id)
            if meeting.account != current_account:
                raise PermissionDenied("Wrong meeting field for current account.")

        if not old_doc_id:
            old_doc = None
        else:
            old_doc = Document.objects.get(pk=old_doc_id)
            if old_doc.account != current_account:
                raise PermissionDenied("Wrong old_doc field for current account.")

        self.post_save_actions(document, old_doc, meeting)

        signals.view_create.send(sender=self.__class__, instance=document, request=self.request)

        data = {'status': 'success', 'pk': document.pk}
        if action == 'update':
            data['html'] = render_to_string('documents/document_item.html',
                                            {'doc': document, 'user': self.request.user})
            data['type'] = document.get_type_display()

        return self.render_to_json_response(data)


class DocumentAjaxDeleteView(AjaxableResponseMixin, SelectBoardRequiredMixin,
                             DocumentQuerysetMixin, PermissionMixin, BaseFormView):
    permission = (Document, PERMISSIONS.delete)
    form_class = DocumentDeleteForm

    def get_permission_object(self):
        document_id = self.request.POST.get('document_id')
        return get_object_or_404(self.get_queryset(), id=document_id)

    def form_invalid(self, form):
        return HttpResponseBadRequest()

    def form_valid(self, form):
        document_id = form.cleaned_data['document_id']
        change_type = form.cleaned_data['change_type']
        document = get_object_or_404(self.get_queryset(), id=document_id)

        # create AuditTrail from deleted/updated document
        self.process_delete(change_type, document, self.request.user.id)

        data = {'doc_id': document.id, 'doc_type': document.type}
        return self.render_to_json_response(data)

    @staticmethod
    def process_delete(change_type, document, user_id):
        AuditTrail.objects.create(
            name=document.name,
            file=document.file,
            type=document.type,
            user_id=user_id,
            change_type=change_type,
            latest_version=document.id,
            created_at=document.created_at,
        )

        RecentActivity.objects.filter(
            object_id=document.id,
            content_type_id=ContentType.objects.get_for_model(document),
        ).delete()

        document_id = document.id
        document.delete()

        new_version = Document.objects.filter(previous_version=document_id)
        if new_version:
            ats = AuditTrail.objects.filter(latest_version=document_id)
            ats.update(latest_version=new_version[0].id)


# class AllowTokenAuthMixin(object):
#     def dispatch(self, request, *args, **kwargs):
#         auth = get_authorization_header(request)
#         if auth and auth.startswith('Token'):
#             pass


class DocumentDownloadView(SelectBoardRequiredMixin, DocumentQuerysetMixin, PermissionMixin, View):
    permission = (Document, PERMISSIONS.view)

    def and_permission(self, account, membership):
        document = get_object_or_404(self.get_queryset(), id=self.kwargs['document_id'])
        self.document = document
        return has_object_permission(membership, document, PERMISSIONS.view)

    def get(self, request, document_id):
        return self.do_download(self.document, view=bool(request.GET.get('view', False)))

    # Static so that it can be reused in DocumentDirectDownloadView below
    @staticmethod
    def do_download(document, view=False):
        return DocumentDownloadView.do_download_file(document.file, document.name, view)

    # Static so that it can be reused in DocumentPdfPreviewView below
    @staticmethod
    def do_download_file(f, document_name, view=False):
        if settings.USE_S3:
            content_type = mimetypes.guess_type(f.name)[0]
            filename = f.file.key.name.split('/')[-1]
            wrapper = FileWrapper(f.file)
            size = f.size
        else:
            content_type = mimetypes.guess_type(f.path)[0]
            filename = os.path.basename(f.name)
            wrapper = FileWrapper(open(f.path, 'rb'))
            size = os.path.getsize(f.path)

        # Create the HttpResponse object with the appropriate headers.
        response = HttpResponse(wrapper, content_type=content_type)
        response['Content-Length'] = size
        # TODO: Test with some docs if it doesn't hurt, this header replaces wrong text/html type,
        # and at least heals debug-panel.
        # response['Content-Type'] = 'application/x-octet-stream'
        if not view:
            try:
                response['Content-Disposition'] = u'attachment; filename="{}"'.format(document_name or filename)
            except BadHeaderError:
                _, file_extension = os.path.splitext(document_name or filename)
                response['Content-Disposition'] = u'attachment; filename="{}"'.format("file" + file_extension)
                pass

        return response


class DocumentRevisionDownloadView(SelectBoardRequiredMixin, DocumentQuerysetMixin, PermissionMixin, View):
    permission = (Document, PERMISSIONS.view)

    def and_permission(self, account, membership):
        document = get_object_or_404(self.get_queryset(), id=self.kwargs['document_id'])
        return has_object_permission(membership, document, PERMISSIONS.view)

    @staticmethod
    def get(request, document_id, revision):
        audit = get_object_or_404(AuditTrail, latest_version=document_id, revision=revision)

        if settings.USE_S3:
            content_type = mimetypes.guess_type(audit.file.name)[0]
            filename = audit.file.file.key.name.split('/')[-1]
            wrapper = FileWrapper(audit.file.file)
            size = audit.file.size
        else:
            content_type = mimetypes.guess_type(audit.file.path)[0]
            filename = os.path.basename(audit.file.name)
            wrapper = FileWrapper(file(audit.file.path, 'rb'))
            size = os.path.getsize(audit.file.path)

        # Create the HttpResponse object with the appropriate headers.
        response = HttpResponse(wrapper, content_type=content_type)
        response['Content-Length'] = size
        response['Content-Disposition'] = u'attachment; filename="{}"'.format(audit.name or filename)
        return response


class DocumentSendView(AjaxableResponseMixin, SelectBoardRequiredMixin, MemberNotificationMixin,
                       DocumentQuerysetMixin, PermissionMixin, FormView):
    permission = (Document, PERMISSIONS.view)
    form_class = MessageForm
    template_name = 'documents/message.html'

    def and_permission(self, account, membership):
        document = get_object_or_404(self.get_queryset(), id=self.kwargs['document_id'])
        self.object = document
        return has_object_permission(membership, document, PERMISSIONS.view)

    def get(self, request, *args, **kwargs):
        super(DocumentSendView, self).get(request, *args, **kwargs)
        data = {
            'html': render_to_string(self.template_name,
                                     self.get_context_data(form=self.get_form(self.form_class),
                                                           document_id=self.kwargs['document_id']),
                                     context_instance=RequestContext(self.request))
        }
        return self.render_to_json_response(data)

    def form_valid(self, form):
        ctx_dict = {
            'title': form.cleaned_data['subject'],
            'msg': form.cleaned_data['body'],
            'account': get_current_account(self.request)
        }
        self.send(ctx_dict, attachments=((self.object.name, self.object.file.read(), None),))
        return redirect(self.get_success_url())

    def get_success_message(self):
        messages.success(self.request, _('Documents were shared'))

    def get_success_url(self):
        account_url = get_current_account(self.request).url
        if self.object.folder is not None:
            self.object.folder.get_absolute_url()
        else:
            return reverse('folders:rootfolder_detail', kwargs={'url': account_url})


class DocumentMoveView(AjaxableResponseMixin, DocumentQuerysetMixin,
                       PermissionMixin, SelectBoardRequiredMixin, View):
    permission = (Document, PERMISSIONS.edit)

    def and_permission(self, account, membership):
        target = get_object_or_404(Folder, account=account, slug=self.request.POST.get('target_slug'))
        self.target = target
        return target.can_add_files and has_object_permission(membership, target, PERMISSIONS.add)

    def get_permission_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['document_id'])

    def post(self, request, *args, **kwargs):
        document = self.get_permission_object()

        form = FolderMoveForm(request.POST)
        if form.is_valid():
            document.folder = self.target
            document.save()
            return self.render_to_json_response({'result': 'ok'})
        else:
            # QUESTION: Is there already converter ErrorDict -> Dict[String, String]?
            return self.render_to_json_response({'result': 'failed', 'errors': 'TODO'})


class DocumentPdfPreviewView(DocumentQuerysetMixin, PermissionMixin, SelectBoardRequiredMixin, View):
    permission = (Document, PERMISSIONS.view)

    def get(self, request, *args, **kwargs):
        document = get_object_or_404(self.get_queryset(), pk=kwargs['pk'])
        preview = document.generate_preview()
        if not document.pdf_preview:
            return DocumentDownloadView.do_download_file(preview, document.name)

        return DocumentDownloadView.do_download_file(document.pdf_preview, document.name + '.pdf')


class DocumentApproveView(SelectBoardRequiredMixin, DocumentQuerysetMixin, PermissionMixin, View):
    permission = (Document, PERMISSIONS.view)

    def and_permission(self, account, membership):
        document = get_object_or_404(self.get_queryset(), id=self.kwargs['document_id'])
        self.document = document
        return has_object_permission(membership, document, PERMISSIONS.view)

    def get(self, request, document_id):

        user_id = request.user.id

        # aprv, rc = Approval.objects.get_or_create(user_id=user_id, document_id=document_id)
        aprv = Approval.objects.filter(user_id=user_id, document_id=document_id).first()
        if not aprv:
            aprv = Approval.objects.create(user_id=user_id, document_id=document_id)

        if 'ajax' not in request.GET:
            return redirect(self.document.folder.get_absolute_url())
        else:
            return JsonResponse({'approval_id': aprv.id,
                                 'document_id': document_id,
                                 'message': 'Approved!'})


class DocumentRenameView(AjaxableResponseMixin, SelectBoardRequiredMixin,
                         DocumentQuerysetMixin, PermissionMixin, BaseFormView):
    permission = (Document, PERMISSIONS.edit)
    form_class = DocumentRenameForm

    def get_permission_object(self):
        document_id = self.request.POST.get('document_id')
        return get_object_or_404(self.get_queryset(), id=document_id)

    def form_invalid(self, form):
        return HttpResponseBadRequest()

    def form_valid(self, form):
        document_id = form.cleaned_data['document_id']
        filename = form.cleaned_data['filename']
        document = get_object_or_404(self.get_queryset(), id=document_id)

        # create AuditTrail from updated document
        self.process_update(document, filename)

        data = {'doc_id': document.id, 'doc_type': document.type}
        return self.render_to_json_response(data)

    @staticmethod
    def process_update(document, filename):
        extension = ''
        if '.' in document.name:
            extension = '.' + document.name.split('.')[-1]
        document.name = filename + extension
        document.save()
