# -*- coding: utf-8 -*-
from django.conf.urls import url

from committees.views import (CommitteesView, CommitteeDetailView, CommitteeCreateView, CommitteeUpdateView,
                              CommitteeDeleteView)

app_name = 'committees'

urlpatterns = [
    url(r'^$', CommitteesView.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/$', CommitteeDetailView.as_view(), name='detail'),
    url(r'^create/$', CommitteeCreateView.as_view(), name='create'),
    url(r'^update/(?P<pk>\d+)/$', CommitteeUpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>\d+)/$', CommitteeDeleteView.as_view(), name='delete'),
]
