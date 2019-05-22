# -*- coding: utf-8 -*-
from django.conf.urls import url

from meetings.urls import make_meeting_urls
from meetings.views import MeetingDetailView, MeetingCreateView, MeetingsView, MeetingUpdateView, MeetingDeleteView, PastMeetingsView, MeetingMailView

app_name = 'meetings'
urlpatterns = make_meeting_urls(kwargs={'type': 'event'})