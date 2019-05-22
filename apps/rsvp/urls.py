# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import RsvpUpdateView

app_name = 'rsvp'

urlpatterns = [
    url(r'^$', RsvpUpdateView.as_view(), name='update'),
]
