# -*- coding: utf-8 -*-
from django.conf.urls import url
from .views import NewsListView, NewsDetailView, NewsCreateView, NewsUpdateView, NewsDeleteView

app_name = 'news'

urlpatterns = [
    url(r'^create/$', NewsCreateView.as_view(), name='create'),
    url(r'^update/(?P<pk>\d+)/$', NewsUpdateView.as_view(), name='edit'),
    url(r'^delete/(?P<pk>\d+)/$', NewsDeleteView.as_view(), name='delete'),
    url(r'^(?P<pk>\d+)/$', NewsDetailView.as_view(), name='detail'),
    url(r'^$', NewsListView.as_view(), name='list')
]
