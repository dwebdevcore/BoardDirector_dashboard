# -*- coding: utf-8 -*-
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from documents.models import Folder


@receiver(post_save)
def update_bound_folder(sender, instance, **kwargs):
    # can't import on module level
    from committees.models import Committee
    from meetings.models import Meeting
    from profiles.models import Membership
    if sender == Committee:
        Folder.objects.update_committee_folder(instance)
    elif sender == Meeting:
        Folder.objects.update_meeting_folder_if_exists(instance)
    elif sender == Membership:
        Folder.objects.update_membership_folder(instance)


@receiver(pre_delete)
def delete_bound_folder(sender, instance, **kwargs):
    from committees.models import Committee
    from meetings.models import Meeting
    # Don't delete members private folder
    if sender in (Committee, Meeting):
        try:
            # TODO - delete RecentActivity & Audit trials?
            instance.folder.delete()
        except:
            pass


@receiver(post_save)
def create_initial_folders(sender, instance, created, **kwargs):
    from accounts.models import Account
    if sender == Account and created:
        Folder.objects.create_initial_folders(instance)
