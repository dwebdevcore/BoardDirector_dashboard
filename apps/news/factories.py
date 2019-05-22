# -*- coding: utf-8 -*-
import factory

from django.utils import lorem_ipsum

from accounts.models import Account
from news.models import News
from profiles.models import Membership


class NewsFactory(factory.DjangoModelFactory):
    class Meta:
        model = News

    @factory.lazy_attribute_sequence
    def title(self, n):
        return lorem_ipsum.words(5, False)

    @factory.lazy_attribute_sequence
    def text(self, n):
        return lorem_ipsum.words(105, False)

    @factory.lazy_attribute
    def account(self):
        return Account.objects.order_by('?')[0]

    @factory.lazy_attribute
    def created_member(self):
        return Membership.objects.filter(account=self.account).order_by('?')[0]
