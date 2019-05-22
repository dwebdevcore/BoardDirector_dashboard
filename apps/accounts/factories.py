# -*- coding: utf-8 -*-
import factory
from django.template.defaultfilters import slugify

from accounts.models import Account
from billing.models import Plan


class AccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = Account

    @factory.lazy_attribute_sequence
    def name(self, n):
        return 'test company {0}'.format(n)

    @factory.lazy_attribute
    def url(self):
        return slugify(self.name)[-25:]

    @factory.lazy_attribute
    def plan(self):
        return Plan.objects.get(name=Plan.DEFAULT_PLAN)
