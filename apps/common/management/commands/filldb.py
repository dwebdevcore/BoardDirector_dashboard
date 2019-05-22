# -*- coding: utf-8 -*-
import random

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _

from accounts.models import Account
from accounts.factories import AccountFactory
from billing.factories import BillingSettingsFactory
from committees.models import Committee
from committees.factories import CommitteeFactory
from documents.factories import DocumentFactory
from meetings.factories import MeetingFactory
from profiles.models import User, Membership
from profiles.factories import UserFactory, AdminFactory


class Command(BaseCommand):
    help = 'Fill the database with test fixtures'

    def handle(self, *args, **options):
        self.stdout.write('Starting fill db')

        site = Site.objects.get(pk=1)
        site.domain = site.name = settings.DOMAIN
        site.save()

        user = User.objects.create_superuser(email='admin@example.com', password='')
        user.set_password('admin')
        user.save()

        accounts = AccountFactory.create_batch(2)
        for account in Account.objects.all():
            admin = AdminFactory(accounts=[account])
            membership = admin.get_membership(account)
            BillingSettingsFactory(account=account)
            board_of_directors = CommitteeFactory(name=_('Board of Directors'), account=account)
            membership.committees.add(board_of_directors)
        UserFactory.create_batch(5, accounts=accounts)
        for account in Account.objects.all():
            CommitteeFactory.create_batch(10, account=account)
        for membership in Membership.objects.filter(user__in=User.objects.select_related().exclude(is_superuser=True)):
            membership.committees.add(*random.sample(set(Committee.objects.filter(account_id=membership.account_id)), 2))
        MeetingFactory.create_batch(10)
        DocumentFactory.create_batch(5)

        self.stdout.write('Completed fill db')
