# -*- coding: utf-8 -*-
from django.conf.urls import url

from documents.views import (DocumentAjaxCreateView, DocumentAjaxDeleteView,
                             DocumentDownloadView, DocumentRevisionDownloadView, DocumentSendView)
from documents.views.document import (DocumentMoveView, DocumentPdfPreviewView,
                                      DocumentApproveView, DocumentRenameView)

app_name = 'documents'

urlpatterns = [
    url(r'^create/$', DocumentAjaxCreateView.as_view(), name='create'),
    url(r'^delete/$', DocumentAjaxDeleteView.as_view(), name='delete'),
    url(r'^download/(?P<document_id>\d+)/$', DocumentDownloadView.as_view(), name='download'),
    url(r'^download/(?P<document_id>\d+)/v(?P<revision>\d+)$',
        DocumentRevisionDownloadView.as_view(), name='download-revision'),
    url(r'^send/(?P<document_id>\d+)/$', DocumentSendView.as_view(), name='send'),
    url(r'^move/(?P<document_id>\d+)/$', DocumentMoveView.as_view(), name='move'),
    url(r'^pdf_preview/(?P<pk>\d+)/$', DocumentPdfPreviewView.as_view(), name='pdf_preview'),
    url(r'^approve/(?P<document_id>\d+)/$', DocumentApproveView.as_view(), name='approve'),
    url(r'^rename/$', DocumentRenameView.as_view(), name='rename'),
]
