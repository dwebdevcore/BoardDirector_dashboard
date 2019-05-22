# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import CalendarView

app_name = 'boardcalendar'

urlpatterns = [
    url(r'^$', CalendarView.as_view(), name='list'),
]
