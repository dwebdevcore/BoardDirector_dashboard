# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import (BoardsListView, AccountCancelView, AccountReactivateView, AccountLogoView, AccountLogoRemoveView,
                    AccountNotifyView)

app_name = 'accounts'

urlpatterns = [
    url(r'^$', BoardsListView.as_view(), name='boards'),
    url(r'^cancel/$', AccountCancelView.as_view(), name='cancel'),
    url(r'^reactivate/$', AccountReactivateView.as_view(), name='reactivate'),
    url(r'^logo/$', AccountLogoView.as_view(), name='logo'),
    url(r'^notify/$', AccountNotifyView.as_view(), name='notify'),
    url(r'^logo/remove/$', AccountLogoRemoveView.as_view(), name='remove-logo'),
]
