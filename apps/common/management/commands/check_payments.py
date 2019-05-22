# -*- coding: utf-8 -*-
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

import stripe

from accounts.models import Account
from billing.models import Invoice, BillingSettings


class Command(BaseCommand):
    help = 'Check Stripe Payments'

    def handle(self, *args, **options):
        self.stdout.write('Start checking payments ...')

        accounts = Account.objects.filter(is_active=True).exclude(stripe_customer_id='')
        for account in accounts:
            try:
                last_invoice = account.invoices.all().latest()
                if last_invoice.payed_period_end < timezone.now():

                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    c = stripe.Customer.retrieve(account.stripe_customer_id)

                    timestamp_period_start = datetime.fromtimestamp(int(c.subscription.current_period_start))
                    period_start = timestamp_period_start.replace(tzinfo=timezone.utc)

                    timestamp_period_end = datetime.fromtimestamp(int(c.subscription.current_period_end))
                    period_end = timestamp_period_end.replace(tzinfo=timezone.utc)

                    plan_fee = account.plan.month_price
                    if account.billing_settings.cycle == BillingSettings.YEAR:
                        plan_fee = account.plan.year_price

                    Invoice.objects.create(payment=plan_fee, status=Invoice.PAID, account=account,
                                           created_at=period_start, payed_period_end=period_end)

            except Invoice.DoesNotExist:
                pass

        self.stdout.write('Complete checking payments ...')
