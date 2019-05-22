# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType


class ContentTypeCache(object):
    """
    Cache fetching of Content Types.
    Needs a class because of ImportError when CONTENT_TYPES dict is on module level.
    """
    @classmethod
    def init(cls):
        cls.CONTENT_TYPES = {
            'accounts.account': ContentType.objects.get(app_label='accounts', model='account'),
            'committees.committee': ContentType.objects.get(app_label='committees', model='committee'),
            'documents.folder': ContentType.objects.get(app_label='documents', model='folder'),
            'documents.document': ContentType.objects.get(app_label='documents', model='document'),
            'meetings.meeting': ContentType.objects.get(app_label='meetings', model='meeting'),
            'profiles.membership': ContentType.objects.get(app_label='profiles', model='membership'),
            'news.news': ContentType.objects.get(app_label='news', model='news'),
            'voting.voting': ContentType.objects.get(app_label='voting', model='voting'),
        }

    @classmethod
    def get(cls, model_name):
        if not hasattr(cls, 'CONTENT_TYPES'):
            cls.init()
        return cls.CONTENT_TYPES.get(model_name)


def get_contenttype(model):
    if hasattr(model, '_meta'):
        return ContentType.objects.get_for_model(model)
    else:
        return ContentTypeCache.get(str(model))


def get_cached_permissions(membership, key, func, *args):
    # Cache results on membership object
    if not hasattr(membership, '_cached_permissions'):
        membership._cached_permissions = {}
    cached = membership._cached_permissions
    permissions = cached.get(key)
    if permissions is None:
        permissions = func(*args)
        cached[key] = permissions
    return permissions
