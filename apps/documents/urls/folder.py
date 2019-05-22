# -*- coding: utf-8 -*-
"""Folder urls are in a seperate file because they are included with account url."""
from django.conf.urls import url

from documents.views import (RootFolderDetailView, FolderDetailView, SharedFolderView, DocumentAddView,
                             FolderAddView, FolderEditView, FolderDeleteView, FolderLookupView, FolderMoveView,
                             FolderOrderingAjaxView, PermissionDetailView, PermissionAddView, PermissionDeleteView)

app_name = 'folders'

urlpatterns = [
    url(r'^$', RootFolderDetailView.as_view(), name='rootfolder_detail'),
    url(r'^lookup-folder/$', FolderLookupView.as_view(), name='folder_lookup'),
    url(r'^shared/$', SharedFolderView.as_view(), name='shared_folder'),
    url(r'^(?P<slug>[-\w]+)/$', FolderDetailView.as_view(), name='folder_detail'),
    url(r'^(?P<slug>[-\w]+)/add/$', DocumentAddView.as_view(), name='document_add'),
    url(r'^(?P<slug>[-\w]+)/add-folder/$', FolderAddView.as_view(), name='folder_add'),
    url(r'^(?P<slug>[-\w]+)/edit/$', FolderEditView.as_view(), name='folder_edit'),
    url(r'^(?P<slug>[-\w]+)/delete/$', FolderDeleteView.as_view(), name='folder_delete'),
    url(r'^(?P<slug>[-\w]+)/move/$', FolderMoveView.as_view(), name='folder_move'),
    url(r'^(?P<slug>[-\w]+)/share/$', PermissionDetailView.as_view(), name='share_detail'),
    url(r'^(?P<slug>[-\w]+)/share/add/$', PermissionAddView.as_view(), name='share_add'),
    url(r'^(?P<slug>[-\w]+)/share/delete/$', PermissionDeleteView.as_view(), name='share_delete'),
    url(r'^(?P<slug>[-\w]+)/ordering/$', FolderOrderingAjaxView.as_view(), name='folder_ordering'),
]
