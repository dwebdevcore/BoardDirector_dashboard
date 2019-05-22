# -*- coding: utf-8 -*-
from django.db import models
from mptt.managers import TreeManager


class FolderManager(TreeManager, models.Manager):
    def get_account_root(self, account):
        """Get account root folder (and create if necessary)."""
        account_root, created = self.get_or_create(
            name=account.url,
            parent=None,
            account=account,
            defaults={
                'user': None,
                'protected': True,
            }
        )
        return account_root

    def create_meeting_folder(self, meeting):
        """Create meeting folder."""
        account = meeting.account
        account_root = self.get_account_root(account)
        meeting_root, created = self.get_or_create(
            name=self.model.MEETINGS_NAME,
            parent=account_root,
            account=account,
            defaults={
                'user': None,
                'protected': True,
            }
        )
        name = self.model.generate_name_from_meeting(meeting)
        meeting_folder, created = self.get_or_create(
            name=name,
            parent=meeting_root,
            account=account,
            meeting=meeting,
            defaults={
                'user': None,
                'protected': True,
            }
        )
        meeting_folder.created = meeting.start
        meeting_folder.save(update_fields=['created'])
        return meeting_folder

    def update_or_create_meeting_folder(self, meeting):
        if not self.update_meeting_folder_if_exists(meeting):
            self.create_meeting_folder(meeting)

    def update_meeting_folder_if_exists(self, meeting):
        try:
            folder = meeting.folder
        except self.model.DoesNotExist:
            return False

        name = self.model.generate_name_from_meeting(meeting)
        if folder.name != name:
            folder.name = name
            folder.save(update_fields=['name'])
        return True

    def create_committee_folder(self, committee):
        """Create committee folder."""
        account = committee.account
        account_root = self.get_account_root(account)
        committee_root, created = self.get_or_create(
            name=self.model.COMMITTEES_NAME,
            parent=account_root,
            account=account,
            defaults={
                'user': None,
                'protected': True,
            }
        )
        name = self.model.generate_name_from_committee(committee)
        committee_folder, created = self.get_or_create(
            name=name,
            parent=committee_root,
            account=account,
            defaults={
                'user': None,
                'committee': committee,
                'protected': True,
            }
        )
        return committee_folder

    def update_committee_folder(self, committee):
        try:
            folder = committee.folder
        except self.model.DoesNotExist:
            folder = self.create_committee_folder(committee)
        name = self.model.generate_name_from_committee(committee)
        if folder.name != name:
            folder.name = name
            folder.save(update_fields=['name'])

    def create_membership_folder(self, membership):
        """Create membership folder."""
        account = membership.account
        account_root = self.get_account_root(account)
        membership_root, created = self.get_or_create(
            name=self.model.MEMBERSHIPS_NAME,
            parent=account_root,
            account=account,
            defaults={
                'user': None,
                'protected': True,
            }
        )
        name = self.model.generate_name_from_membership(membership)
        membership_folder, created = self.get_or_create(
            name=name,
            parent=membership_root,
            account=account,
            defaults={
                'user': None,
                'membership': membership,
                'protected': True,

            }
        )
        return membership_folder

    def update_membership_folder(self, membership):
        try:
            folder = membership.private_folder
        except self.model.DoesNotExist:
            folder = self.create_membership_folder(membership)

        name = self.model.generate_name_from_membership(membership)
        if folder.name != name:
            folder.name = name
            folder.save(update_fields=['name'])

        if folder.protected != membership.is_active:
            folder.protected = membership.is_active
            folder.save(update_fields=['protected'])

    def _share_folder(self, folder):
        from permissions import PERMISSIONS
        from permissions.models import ObjectPermission
        from permissions.utils import get_contenttype
        from profiles.models import Membership
        return ObjectPermission.objects.get_or_create(
            role=Membership.ROLES.member,
            content_type=get_contenttype(folder),
            object_id=folder.id,
            permission=PERMISSIONS.view,
        )

    def create_initial_folders(self, account):
        folders = (
            ('Governance', ('Articles of Incorporation', 'EIN and/or Tax Registration Information', 'By-Laws', 'Mission Statement')),
            ('Board Policies', ('Whistleblower Policy', 'Conflict of Interest Policy')),
            ('Financials', ('Annual Reports', 'Audit Reports')),
        )
        account_root = self.get_account_root(account)
        for parent, subfolders in folders:
            for subfolder in subfolders:
                # mptt - always fetch fresh parent instance from db
                parent_folder, created = self.get_or_create(
                    name=parent,
                    parent=account_root,
                    account=account,
                    user=None,
                    protected=False,
                )
                if created:
                    self._share_folder(parent_folder)
                folder, created = self.get_or_create(
                    name=subfolder,
                    parent=parent_folder,
                    account=account,
                    user=None,
                    protected=False,
                )
                if created:
                    self._share_folder(folder)
