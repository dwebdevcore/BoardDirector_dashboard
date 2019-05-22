# -*- coding: utf-8 -*-
from django.conf.urls import url

from meetings.views import MeetingDetailView, MeetingCreateView, MeetingsView, MeetingUpdateView, MeetingDeleteView, \
                            PastMeetingsView, MeetingMailView,MeetingPublishView, MeetingDownloadCardView


def make_meeting_urls(kwargs):
    return [
        url(r'^$', MeetingsView.as_view(), name='list', kwargs=kwargs),
        url(r'^(?P<pk>\d+)/$', MeetingDetailView.as_view(), name='detail', kwargs=kwargs),
        url(r'^(?P<pk>\d+)/mail-details/$', MeetingMailView.as_view(), name='mail-details', kwargs=kwargs),
        url(r'^create/$', MeetingCreateView.as_view(), name='create', kwargs=kwargs),
        url(r'^past/$', PastMeetingsView.as_view(), name='past', kwargs=kwargs),
        url(r'^update/(?P<pk>\d+)/$', MeetingUpdateView.as_view(), name='update', kwargs=kwargs),
        url(r'^delete/(?P<pk>\d+)/$', MeetingDeleteView.as_view(), name='delete', kwargs=kwargs),
        url(r'^publish/(?P<pk>\d+)/$', MeetingPublishView.as_view(), name='publish', kwargs=kwargs),
        url(r'^download-card/(?P<pk>\d+)/$', MeetingDownloadCardView.as_view(), name='download-card', kwargs=kwargs),
        url(r'^download-card/(?P<pk>\d+)/$', MeetingDownloadCardView.as_view(), name='download-card', kwargs=kwargs),
    ]

app_name = 'meetings'

urlpatterns = make_meeting_urls({})
