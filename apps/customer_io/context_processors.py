# -*- coding: utf-8 -*-
from django.conf import settings


def access_keys(request):
    return {
        'customerio_site_id': settings.CUSTOMERIO_SITE_ID,
        'customerio_enabled': settings.CUSTOMERIO_ENABLED,
    }
