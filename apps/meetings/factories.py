# -*- coding: utf-8 -*-
import factory

from django.utils import timezone
from django.utils import lorem_ipsum
from django.utils.timezone import timedelta

from .models import Meeting
from accounts.models import Account
from committees.models import Committee


class MeetingFactory(factory.DjangoModelFactory):
    class Meta:
        model = Meeting

    name = lorem_ipsum.words(4, True)
    description = lorem_ipsum.words(8, True)

    @factory.sequence
    def start(n):
        return timezone.now() + timedelta(days=n)

    @factory.lazy_attribute_sequence
    def end(self, n):
        return self.start + timedelta(hours=n)

    location = lorem_ipsum.words(5, True)

    status = 1

    @factory.lazy_attribute
    def account(self):
        return Account.objects.order_by('?')[0]

    @factory.lazy_attribute
    def committee(self):
        return Committee.objects.filter(account_id=self.account.id).order_by('?')[0]
