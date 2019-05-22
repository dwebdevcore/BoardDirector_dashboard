from rest_framework.routers import DefaultRouter

from dashboard.api_views import DashboardMeetingViewSet

dashboard_router = DefaultRouter()
dashboard_router.register('dashboard/meetings', DashboardMeetingViewSet, 'api-dashboard-meetings')
