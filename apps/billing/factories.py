# -*- coding: utf-8 -*-
import factory

from django.utils import lorem_ipsum
from django.utils import timezone

from .models import Invoice, BillingSettings
from accounts.models import Account
from common.utils import random_with_n_digits


class InvoiceFactory(factory.DjangoModelFactory):
    class Meta:
        model = Invoice

    @factory.lazy_attribute
    def created_at(self):
        return timezone.now()

    @factory.lazy_attribute
    def status(self):
        return Invoice.PAID

    @factory.lazy_attribute
    def account(self):
        return Account.objects.order_by('?')[0]

    @factory.lazy_attribute
    def payment(self):
        return 29

    @factory.lazy_attribute
    def payed_period_end(self):
        return timezone.now() + timezone.timedelta(days=30)


class BillingSettingsFactory(factory.DjangoModelFactory):
    class Meta:
        model = BillingSettings

    @factory.lazy_attribute
    def account(self):
        return Account.objects.order_by('?')[0]

    @factory.lazy_attribute
    def card_number(self):
        return str(random_with_n_digits(16))

    @factory.lazy_attribute
    def expiration_month(self):
        return timezone.now().month

    @factory.lazy_attribute
    def expiration_year(self):
        return timezone.now().year

    @factory.lazy_attribute
    def cvv(self):
        return unicode(random_with_n_digits(3))

    @factory.lazy_attribute
    def mail(self):
        return u'{}@example.com'.format(lorem_ipsum.words(1, False))

    @factory.lazy_attribute
    def name(self):
        return u'{}'.format(lorem_ipsum.words(1, False))

    @factory.lazy_attribute
    def cycle(self):
        return BillingSettings.MONTH
