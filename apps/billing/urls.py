# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import ChangeBillingCycleView, ChangePlanView, BillingSettingsUpdateView, BillingAddressUpdateView

app_name = 'billing'

urlpatterns = [
    url(r'^change_cycle/$', ChangeBillingCycleView.as_view(), name='change_cycle'),
    url(r'^change_plan/$', ChangePlanView.as_view(), name='change_plan'),
    url(r'^update_settings/$', BillingSettingsUpdateView.as_view(), name='update_settings'),
    url(r'^update_address/$', BillingAddressUpdateView.as_view(), name='update_address'),
]
