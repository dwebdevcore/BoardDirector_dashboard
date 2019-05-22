from rest_framework.routers import DefaultRouter

from meetings.api_views import MeetingViewSet

meetings_router = DefaultRouter()
meetings_router.register('meetings/meetings', MeetingViewSet, 'api-meetings-meetings')
