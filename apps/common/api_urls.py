from rest_framework.routers import DefaultRouter

from accounts.api_urls import account_router
from committees.api_urls import committee_router
from common.api_views import MeViewset
from common.restauth.views import TokenAuthViewset
from dashboard.api_urls import dashboard_router
from documents.api_urls import documents_router
from meetings.api_urls import meetings_router
from profiles.api_urls import profiles_router
from voting.urls import router as voting_router


class CombineRouter(DefaultRouter):
    def extend(self, router):
        self.registry.extend(router.registry)

    def sort(self):
        self.registry.sort(key=lambda t: t[0])


combined_router = CombineRouter()
combined_router.extend(profiles_router)
combined_router.extend(voting_router)
combined_router.extend(committee_router)
combined_router.extend(meetings_router)
combined_router.extend(dashboard_router)
combined_router.extend(documents_router)

combined_router.sort()

global_router = CombineRouter()
global_router.extend(account_router)
global_router.register('token-auth', TokenAuthViewset, 'token-auth')
global_router.register('me', MeViewset, 'me')
