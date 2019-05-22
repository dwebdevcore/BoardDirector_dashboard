# -*- coding: utf-8 -*-
from django.conf import settings

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Account
from billing.models import Invoice
from profiles.models import Membership


class Command(BaseCommand):
    help = 'Check Accounts with Trial Plans'

    def handle(self, *args, **options):
        self.stdout.write('Start checking ...')

        date_x = timezone.now() - timezone.timedelta(days=settings.TRIAL_PERIOD)
        # send trial expiry notification to admins
        trial_date = date_x + timezone.timedelta(days=3)
        accounts = Account.objects.filter(date_created__year=trial_date.year, date_created__month=trial_date.month,
                                          date_created__day=trial_date.day, is_active=True, stripe_customer_id='').exclude(unlimited_trial=True)
        for account in accounts:
            members = Membership.objects.filter(account=account, is_admin=True).select_related('User')
            for member in members:
                member.user.admin_notification(account=account, msg_type='trial_reminder')
        # deactivate accounts with expired trial
        accounts = Account.objects.filter(is_active=True, stripe_customer_id='', date_created__lt=date_x).exclude(unlimited_trial=True)
        non_active_accounts = []
        for account in accounts:
            payed_period_end = None
            try:
                last_invoice = account.invoices.all().latest()
                payed_period_end = last_invoice.payed_period_end
            except Invoice.DoesNotExist:
                pass
            # check if account's paid period is finished or is trial
            if not payed_period_end or payed_period_end < timezone.now():
                billing = account.billing_settings

                # Old method, with storing credentials. Will work for old billing information.
                if billing.has_credentials:
                    resp = account._create_subscription()
                    if resp['status'] == 'error':
                        non_active_accounts.append(account.id)
                else:
                    non_active_accounts.append(account.id)
                upd_account = Account.objects.get(id=account.id)
                memberships = Membership.objects.filter(account=upd_account, is_admin=True)
                for membership in memberships:
                    if payed_period_end:
                        # paid period has finished and there are some troubles with credit card (no stripe user exists)
                        membership.user.admin_notification(account=upd_account, msg_type='paid_is_over')
                    else:
                        membership.user.admin_notification(account=upd_account, msg_type='trial_is_over')
        Account.objects.filter(id__in=non_active_accounts).update(is_active=False)
        self.stdout.write('Complete checking ...')
