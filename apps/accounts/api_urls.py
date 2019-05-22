from rest_framework.routers import DefaultRouter

from accounts.api_views import AccountViewSet

account_router = DefaultRouter()
account_router.register('accounts/accounts', AccountViewSet, 'api-accounts-accounts')
