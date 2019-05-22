# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages.views import flatpage
from django.views.generic import TemplateView

# from dajaxice.core import dajaxice_autodiscover, dajaxice_config
from django.views.i18n import javascript_catalog
from rest_framework.authtoken.views import obtain_auth_token

from common.api_urls import combined_router, global_router
from common.swagger_views import get_boarddirector_swagger_view
from .views import MainView, ContactView, PricingView, DomainView, \
    get_office_token, get_google_token, \
    CalendarConnectionView, CalendarDisconnectView, CalendarSettingView, \
    save_event_to_file_login, save_event_to_file_code, add_event_to_calendar, MarkUpdateNotificationsAsRead
from accounts.views import (AccountSettingsView, MembersView, GuestsView, MemberCreateView, GuestCreateView,
                            ExportMembersPdfView, ExportMembersXlsView, AssistantCreateView)
from documents.views import RootFolderRedirectView

admin.autodiscover()
# dajaxice_autodiscover()


js_info_dict = {'packages': ('common',)}

urlpatterns = [
    url(r'^privacy/$', flatpage, {'url': '/privacy/'}, name='privacy'),
    url(r'^terms/$', flatpage, {'url': '/terms/'}, name='terms'),

    # calendar integration
    url(r'^get_office_token/$', get_office_token, name='office_token'),
    url(r'^get_google_token/$', get_google_token, name='google_token'),
    url(r'^calendar-connection/$', CalendarConnectionView.as_view(), name='calendar-connection'),
    url(r'^calendar-disconnect/(?P<connect_type>\w+)/$', CalendarDisconnectView.as_view(), name='calendar-disconnect'),
    url(r'^calendar-setting/(?P<connect_type>\w+)/$', CalendarSettingView.as_view(), name='calendar-setting'),
    url(r'^add-to-calendar/$', add_event_to_calendar, name='add-to-calendar'),
    url(r'^save-to-file/(?P<meeting_id>[0-9]+)/?$', save_event_to_file_login, name='save-to-file'),
    url(r'^save-to-file/(?P<meeting_id>[0-9]+)/(?P<code>[0-9a-zA-Z]+)/?$', save_event_to_file_code, name='save-to-file-code'),
    url(r'^mark-update-notifications-read/$', MarkUpdateNotificationsAsRead.as_view(), name='mark-update-notifications-read'),
]

urlpatterns += [
    url(r'^', include('registration.backends.default.urls')),
    # url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict),
    url(r'^mEOu0wA.html$', DomainView.as_view()),

    url(r'^$', MainView.as_view(), name='main'),
    url(r'^app-admin/', admin.site.urls),
    url(r'^api/v1/auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/', include(global_router.urls)),
    url(r'^(?P<url>[^/]+)/api/v1/swagger', get_boarddirector_swagger_view(title='BoardDirector API')),
    url(r'^(?P<url>[^/]+)/api/v1/', include(combined_router.urls)),
    url('', include('social_django.urls', namespace='social')),

    url(r'^accounts/', include('accounts.urls')),
    url(r'^accounts/email/', include('change_email.urls')),
    url(r'^billing/', include('billing.urls', 'billing')),
    url(r'^profile/', include('profiles.urls', 'profiles')),
    url(r'^contact/thankyou/', TemplateView.as_view(template_name='thankyou.html'), name='thankyou'),
    url(r'^contact/', ContactView.as_view(), name='contactus'),
    url(r'^documents/', include('documents.urls.document', 'documents')),
    url(r'^pricing/', PricingView.as_view(), name='pricing'),
    url(r'^pricing-frame/', PricingView.as_view(template_name="pricing_frame.html"), name='pricing-frame'),

    url(r'^(?P<url>[^/]+)/$', AccountSettingsView.as_view(), name='board_detail'),
    url(r'^(?P<url>[^/]+)/archives/', RootFolderRedirectView.as_view()),
    url(r'^(?P<url>[^/]+)/folders/', include('documents.urls.folder', 'folders')),
    url(r'^(?P<url>[^/]+)/committees/', include('committees.urls', 'committees')),
    url(r'^(?P<url>[^/]+)/news/', include('news.urls', 'news')),
    url(r'^(?P<url>[^/]+)/calendar/', include('boardcalendar.urls', 'calendar')),
    url(r'^(?P<url>[^/]+)/dashboard/', include('dashboard.urls', 'dashboard')),
    url(r'^(?P<url>[^/]+)/rsvp/', include('rsvp.urls', 'rsvp')),
    url(r'^(?P<url>[^/]+)/meetings/', include('meetings.urls', 'meetings')),
    url(r'^(?P<url>[^/]+)/events/', include('meetings.events_urls', 'events')),
    url(r'^(?P<url>[^/]+)/members/$', MembersView.as_view(), name='board_members'),
    url(r'^(?P<url>[^/]+)/guests/$', GuestsView.as_view(), name='board_guests'),
    url(r'^(?P<url>[^/]+)/members/create/$', MemberCreateView.as_view(), name='member_create'),
    url(r'^(?P<url>[^/]+)/guests/create/$', GuestCreateView.as_view(), name='guest_create'),
    url(r'^(?P<url>[^/]+)/assistant/(?P<pk>\d+)/create/$', AssistantCreateView.as_view(), name='assistant_create'),
    url(r'^(?P<url>[^/]+)/export/pdf/(?P<role>\w+)/$', ExportMembersPdfView.as_view(), name='export-pdf'),
    url(r'^(?P<url>[^/]+)/export/xls/(?P<role>\w+)/$', ExportMembersXlsView.as_view(), name='export-xls'),
    url(r'^(?P<url>[^/]+)/voting/', include('voting.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
