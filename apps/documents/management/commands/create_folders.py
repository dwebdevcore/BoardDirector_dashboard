# -*- coding: utf-8 -*-
from optparse import make_option
from django.core.management.base import BaseCommand
from accounts.models import Account
from documents.models import Folder


class Command(BaseCommand):
    help = 'Create Folders for Meetings, Committees and/or Memberships'

    option_list = BaseCommand.option_list + (
        make_option(
            '--for',
            dest='for',
            default='meetings,committees,memberships',
            help='Only create folders for given models, default "meetings,committees,memberships"',
        ),
    )

    def handle(self, *args, **options):
        self.stdout.write('Start creating Folders ...')
        for account in Account.objects.all():
            self.stdout.write(u'Creating Folders for account: {0}'.format(account.name))
            if 'meetings' in options['for']:
                self.stdout.write(u'Meetings ...')
                for meeting in account.meetings.all():
                    Folder.objects.update_or_create_meeting_folder(meeting)
            if 'committees' in options['for']:
                self.stdout.write(u'Committees ...')
                for committee in account.committees.all():
                    Folder.objects.update_committee_folder(committee)
            if 'memberships' in options['for']:
                self.stdout.write(u'Memberships ...')
                for membership in account.memberships.all():
                    Folder.objects.update_membership_folder(membership)
            Folder.objects.rebuild()
        self.stdout.write('Complete creating Folders ...')
