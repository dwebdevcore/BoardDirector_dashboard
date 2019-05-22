# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import DashboardView, GettingStartedView, ActivitiesView

app_name = 'dashboard'

urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='dashboard'),
    url(r'^getting-started/$', GettingStartedView.as_view(), name='getting_started'),
    url(r'^activity/$', ActivitiesView.as_view(), name='activity'),
]
