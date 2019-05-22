# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from billing.fields import BigIntegerSizeField


class Plan(models.Model):
    STARTER, STANDARD, PREMIER, STARTER_2016, STANDARD_2016, PREMIER_2016 = range(1, 7)
    PLAN_TYPES = (
        (STARTER, _('Starter (Introduction Offer)')),
        (STANDARD, _('Standard (Introduction Offer)')),
        (PREMIER, _('Premier (Introduction Offer)')),
        (STARTER_2016, _('Starter')),
        (STANDARD_2016, _('Standard')),
        (PREMIER_2016, _('Premier')),
    )
    DEFAULT_PLAN = PREMIER_2016

    name = models.PositiveIntegerField(_('name type'), choices=PLAN_TYPES, default=STANDARD, editable=False)
    pname = models.CharField(_('plan name'), max_length=255, default='', blank=True, null=True)
    max_members = models.PositiveIntegerField(_('max number of members'))
    max_storage = BigIntegerSizeField(_('max storage size'), help_text=_('In GB.'))
    month_price = models.PositiveIntegerField(_('price per month'))
    year_price = models.PositiveIntegerField(_('price per year'))
    stripe_month_plan_id = models.CharField(_('Stripe Monthly Plan ID'), max_length=70)
    stripe_year_plan_id = models.CharField(_('Stripe Yearly Plan ID'), max_length=70)
    available = models.BooleanField(_('Available'), default=False)

    # @property
    def name_str(self):
        if self.pname:
            return self.pname
        else:
            return unicode(dict(self.PLAN_TYPES).get(self.name, ""))

    name_str.short_description = "Plan name"

    @property
    def max_storage_size(self):
        if self.max_storage:
            return '{} GB'.format(self.max_storage / 1024 ** 3)
        else:
            return _('Unlimited')

    @property
    def max_members_str(self):
        if self.max_members:
            return str(self.max_members)
        else:
            return _('Unlimited')

    @property
    def is_unlimited(self):
        return not self.max_members and not self.max_storage

    @property
    def save_for_year(self):
        return 12 * self.month_price - self.year_price

    def __unicode__(self):
        # return self.get_name_display()
        return self.name_str()

    class Meta:
        ordering = ['month_price']

    @classmethod
    def list_available_plans(cls):
        return cls.objects.filter(available=True)


class BillingSettings(models.Model):
    MONTH, YEAR = range(1, 3)
    CYCLE_TYPES = (
        (MONTH, _('every month')),
        (YEAR, _('every year')),
    )
    CREDIT_CARD_TYPES = """
        American Express	34, 37
        China UnionPay	62, 88
        Diners ClubCarte Blanche	300-305
        Diners Club International	300-305, 309, 36, 38-39
        Diners Club US & Canada\t54, 55
        Discover Card	6011, 622126-622925, 644-649, 65
        JCB\t3528-3589
        Laser	6304, 6706, 6771, 6709
        Maestro\t5018, 5020, 5038, 5612, 5893, 6304, 6759, 6761, 6762, 6763, 0604, 6390
        Dankort\t5019
        MasterCard	50-55
        Visa Electron	4026, 417500, 4405, 4508, 4844, 4913, 4917
        Visa	4
        """

    account = models.OneToOneField('accounts.Account', verbose_name=_('account'), related_name='billing_settings')
    card_number = models.CharField(_('credit card number'), max_length=16, null=True, blank=True)
    expiration_month = models.PositiveSmallIntegerField(_('expiration month'), null=True)
    expiration_year = models.PositiveSmallIntegerField(_('expiration year'), null=True)
    cvv = models.CharField(_('cvv'), max_length=4, null=True, blank=True)
    cycle = models.PositiveIntegerField(_('billing cycle'), choices=CYCLE_TYPES, default=YEAR)
    address = models.CharField(_('billing address'), blank=False, max_length=250)
    city = models.CharField(_('city'), blank=True, max_length=100)
    state = models.CharField(_('province/state'), blank=False, max_length=100)
    zip = models.PositiveIntegerField(_('zip'), blank=False, null=True)
    country = models.CharField(_('country'), blank=True, max_length=100)
    mail = models.EmailField(_('billing mail'), blank=False)
    name = models.CharField(_('billing name'), blank=False, max_length=255)
    discount = models.CharField(_('discount code'), max_length=20, blank=True)
    unit_number = models.CharField(_('unit number'), blank=True, null=True, max_length=100)

    last4 = models.CharField(_('last4'), blank=True, null=True, max_length=4)
    card_type = models.CharField(_('card type'), blank=True, null=True, max_length=100)

    def get_full_address(self):
        address = self.address
        if self.city:
            address += '<br>%s' % self.city
        if self.state:
            address += ', %s' % self.state
        if self.zip:
            address += ' {}'.format(self.zip)
        if self.country:
            address += '<br>%s' % self.country
        return address

    @property
    def is_monthly(self):
        return self.cycle == self.MONTH

    @property
    def has_credentials(self):
        return self.expiration_month and self.expiration_year and self.card_number and self.cvv

    # def get_card_type(self):
    #     if self.card_type:
    #         return self.card_type
    #
    #     # Old way with storing credentials
    #     types = self.CREDIT_CARD_TYPES.split("\n")
    #     for type in types:
    #         if not type.strip():
    #             continue
    #         try:
    #             name, variants = type.split("\t")
    #         except ValueError:
    #             continue
    #
    #         for variant in variants.split(","):
    #             if self.card_number.startswith(variant):
    #                 return name.strip()
    #
    #     return "Unknown card"

    @property
    def card_last_nums(self):
        return self.last4  # or (self.card_number[-4:] if self.card_number else None)

    @property
    def expiration_str(self):
        if self.expiration_month is not None and self.expiration_year is not None:
            return "%02d/%02d" % (self.expiration_month, self.expiration_year - 2000 if self.expiration_year else 0)
        else:
            return _("-")

    class Meta:
        verbose_name_plural = _('Billing Settings objects')


class Invoice(models.Model):
    PAID, PENDING, FAILED = range(1, 4)
    STATUS_TYPES = (
        (PAID, _('paid')),
        (PENDING, _('pending')),
        (FAILED, _('failed')),
    )
    payment = models.PositiveIntegerField(_('payment'))
    created_at = models.DateTimeField(_('payment date'), default=timezone.now)
    status = models.PositiveIntegerField(_('status'), choices=STATUS_TYPES, default=PENDING)
    account = models.ForeignKey('accounts.Account', verbose_name=_('account'), related_name='invoices')
    payed_period_end = models.DateTimeField(_('payed period end'))

    class Meta:
        get_latest_by = 'created_at'

    def __unicode__(self):
        return self.account.name
