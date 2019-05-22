# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic.base import TemplateView

from .views import EditProfileView, MemberView, MembershipDeleteView, InviteMemberView, AssistantView, EditAssistantView, \
    AssistantDeleteView, switch_user

app_name = 'profiles'

urlpatterns = [
    url(r'^edit/(?P<pk>\d+)/$', EditProfileView.as_view(), name='edit'),
    url(r'^delete/(?P<pk>\d+)/$', MembershipDeleteView.as_view(), name='delete'),
    url(r'^edit/(?P<member_pk>\d+)/(?P<pk>\d+)/$', EditAssistantView.as_view(), name='assistant_edit'),
    url(r'^delete/(?P<member_pk>\d+)/(?P<pk>\d+)/$', AssistantDeleteView.as_view(), name='assistant_delete'),
    url(r'^(?P<pk>\d+)/$', MemberView.as_view(), name='detail'),
    url(r'^(?P<member_pk>\d+)/(?P<pk>\d+)/assistant/$', AssistantView.as_view(), name='assistant_detail'),
    url(r'^invite/(?P<user_pk>\d+)/$', InviteMemberView.as_view(), name='invite'),
    url(r'^already-associated/$', TemplateView.as_view(template_name='profiles/already_associated.html'), name='already_associated'),
    url(r'^switch-user/$', switch_user, name='switch_user'),
    url(r'^$', MemberView.as_view(), name='detail'),
]
