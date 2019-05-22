from rest_framework.routers import DefaultRouter

from documents.api_views import DocumentViewset, FolderViewset, AnnotationsViewSet

documents_router = DefaultRouter()
documents_router.register('documents/documents', DocumentViewset, 'api-documents-documents')
documents_router.register('documents/folders', FolderViewset, 'api-documents-folders')
documents_router.register('documents/annotations', AnnotationsViewSet, 'api-documents-annotations')
