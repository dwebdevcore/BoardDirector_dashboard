# -*- coding: utf-8 -*-
from .document import (DocumentAjaxCreateView, DocumentAjaxDeleteView,
                       DocumentDownloadView, DocumentRevisionDownloadView, DocumentSendView)
from .folder import (RootFolderRedirectView, RootFolderDetailView, FolderDetailView, SharedFolderView,
                     DocumentAddView, FolderAddView, FolderEditView, FolderDeleteView, FolderMoveView,
                     FolderOrderingAjaxView)
from .folder_lookup import FolderLookupView
from .permission import PermissionDetailView, PermissionAddView, PermissionDeleteView
