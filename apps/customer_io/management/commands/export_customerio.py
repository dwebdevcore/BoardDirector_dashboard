# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from profiles.models import Membership
from customer_io.api import CIOApi


class Command(BaseCommand):
    help = 'Export user memberships to CustomerIO'

    def handle(self, *args, **options):
        self.stdout.write('Start export to CustomerIO ...')

        api = CIOApi()
        for membership in Membership.objects.all():
            api.create_or_update(membership=membership)

        self.stdout.write('Complete export to CustomerIO ...')
