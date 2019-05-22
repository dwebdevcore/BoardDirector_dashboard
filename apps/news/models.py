# -*- coding: utf-8 -*-
import urlparse
from django.conf import settings
from django.core.urlresolvers import reverse

from django.db import models
from django.utils.translation import ugettext as _
from sorl.thumbnail import get_thumbnail
from accounts.models import Account
from documents.models import file_storage

from profiles.models import Membership


class News(models.Model):
    title = models.CharField(_('title'), max_length=255, unique=True)
    text = models.TextField(_('text'))
    created_at = models.DateTimeField(_('date created'), auto_now=True)
    file = models.ImageField(_('image'), upload_to='uploads/news/%Y%m%d', storage=file_storage, null=True, blank=True)
    created_member = models.ForeignKey(Membership, verbose_name=_('member'))
    account = models.ForeignKey(Account, verbose_name=_('account'))
    is_publish = models.BooleanField(_('published'), default=True)

    class Meta:
        ordering = ('-created_at',)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:detail', kwargs={'pk': self.pk, 'url': self.account.url})

    def list_photo_url(self, geometry='180x120'):
        if self.file:
            return get_thumbnail(self.file, geometry, crop='center', quality=100).url
        return urlparse.urljoin(settings.STATIC_URL, 'images/news.png')
