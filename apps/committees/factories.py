# -*- coding: utf-8 -*-
import factory

from django.utils import lorem_ipsum

from .models import Committee
from accounts.models import Account


class CommitteeFactory(factory.DjangoModelFactory):
    class Meta:
        model = Committee

    @factory.lazy_attribute_sequence
    def name(self, n):
        return 'Committee test {0}'.format(n)

    summary = lorem_ipsum.words(5, True)
    description = lorem_ipsum.words(20, True)

    @factory.lazy_attribute
    def account(self):
        return Account.objects.order_by('?')[0]

    @factory.post_generation
    def chairman(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            self.chairman.add(extracted)
