from rest_framework.routers import DefaultRouter

from profiles.api_views import MembershipViewSet, CheckEmailViewSet, ResetPasswordViewSet

profiles_router = DefaultRouter()
profiles_router.register('profiles/memberships', MembershipViewSet, 'api-profiles-memberships')
profiles_router.register('profiles/check-email', CheckEmailViewSet, 'api-profiles-check-email')
profiles_router.register('profiles/reset-password', ResetPasswordViewSet, 'api-profiles-reset-password')
