# -*- coding: utf-8 -*-
import logging
from django.db.models import Q
from permissions import PERMISSIONS
from permissions.utils import get_contenttype, get_cached_permissions
from permissions.models import RolePermission, ObjectPermission
from profiles.models import Membership

logger = logging.getLogger(__name__)


def _get_role_permissions(membership, ct, level=1):
    permissions = set()
    # If assistant, check bosses for permission, limit recursion depth
    if membership.role == membership.ROLES.assistant and level == 1:
        # don't transfer account permissions
        if ct == get_contenttype('accounts.account'):
            return set()
        for boss in membership.get_bosses():
            permissions = permissions.union(_get_role_permissions(boss, ct, level=2))
    else:
        # If committee chairman (pseudo role)
        if membership.committee_set.exists():
            if ct == get_contenttype('profiles.membership'):
                permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.add, PERMISSIONS.edit])
            elif ct == get_contenttype('meetings.meeting'):
                permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.add])
        qs = RolePermission.objects.filter(role=membership.role, content_type=ct)
        permissions = permissions.union(qs.values_list('permission', flat=True))
        logger.debug(u'"{0}" {1} {2}'.format(membership, ct, permissions))
    return permissions


def get_role_permissions(membership, ct):
    try:
        key = 'role_{0}'.format(ct.id)
        return get_cached_permissions(membership, key, _get_role_permissions, membership, ct)
    except Exception as e:
        logger.exception(e)
    return set()


def has_role_permission(membership, model, permission):
    return membership.is_admin or permission in get_role_permissions(membership, get_contenttype(model))


def _get_object_permissions(membership, obj, level=1):
    assert isinstance(membership, Membership)
    permissions = set()
    if membership.role == membership.ROLES.assistant and level == 1:
        for boss in membership.get_bosses():
            permissions = permissions.union(_get_object_permissions(boss, obj, level=2))
    else:
        ct = get_contenttype(obj)
        # Special case permissions
        if ct == get_contenttype('profiles.membership'):
            if membership == obj:
                permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.edit])
            if membership.assistant == obj:
                permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.edit, PERMISSIONS.delete])
        elif ct == get_contenttype('committees.committee'):
            if membership.is_committee_chairman(obj):
                permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.edit])
        elif ct == get_contenttype('meetings.meeting'):
            if membership.is_committee_chairman(obj.committee):
                permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.edit, PERMISSIONS.delete])
        elif ct == get_contenttype('news.news'):
            if membership == obj.created_member:
                permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.edit])
        # Folders
        elif ct == get_contenttype('documents.folder'):
            permissions = permissions.union(_get_folder_permissions(membership, obj))
        # Documents
        elif ct == get_contenttype('documents.document'):
            # check on parent folder
            if obj.folder is not None and obj.folder.can_add_files:
                permissions = permissions.union(_get_folder_permissions(membership, obj.folder, for_content=True))

        if len(permissions) != len(PERMISSIONS):
            qs = ObjectPermission.objects\
                .filter(Q(role=membership.role) | Q(membership=membership))\
                .filter(content_type=ct, object_id=obj.id)
            permissions = permissions.union(qs.values_list('permission', flat=True))
        logger.debug(u'"{0}" {1} "{2}" {3}'.format(membership, ct, obj, permissions))
    return permissions


def _get_folder_permissions(membership, obj, for_content=False):
    permissions = set()

    # View permission is handeled differently for folder/document
    # Usually RolePermission view means can view all, but for folders user can only see explicitly allowed ones
    if membership.is_admin or membership.role in (membership.ROLES.chair,):
        permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.add, PERMISSIONS.edit,
                                         PERMISSIONS.delete, PERMISSIONS.share])
    else:
        if obj.name in (obj.MEETINGS_NAME, obj.COMMITTEES_NAME):
            permissions = permissions.union([PERMISSIONS.view])

        # Check committee
        committee = obj.committee or obj.meeting and obj.meeting.committee
        if committee:
            # committee & meeting folder
            if membership.is_committee_chairman(committee):
                permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.add, PERMISSIONS.edit,
                                                 PERMISSIONS.delete, PERMISSIONS.share])
            elif membership.committees.filter(id=committee.id).exists():
                # committee folder
                if obj.committee:
                    permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.add, PERMISSIONS.edit, PERMISSIONS.delete])
                # meeting folder
                if obj.meeting and obj.meeting.is_published:
                    permissions = permissions.union([PERMISSIONS.view])

        # Check meeting
        # Meeting must be either published or we're checking permissions for content actually
        if obj.meeting and (obj.meeting.is_published or for_content) and PERMISSIONS.view not in permissions:
            # Check "All Board Members Meeting" that has committee as None
            if obj.meeting.committee is None and not membership.is_guest:
                permissions = permissions.union([PERMISSIONS.view])

            # Check meeting Extra members (outside committee)
            if obj.meeting.extra_members.filter(id=membership.id).exists():
                permissions = permissions.union([PERMISSIONS.view])

        # Check if members private folder
        if obj.membership_id == membership.id:
            permissions = permissions.union([PERMISSIONS.view, PERMISSIONS.add, PERMISSIONS.edit,
                                             PERMISSIONS.delete, PERMISSIONS.share])

    # check on parent folder (stop before committee & meeting root folder)
    if len(permissions) != len(PERMISSIONS) and obj.parent is not None and obj.parent.can_add_files:
        permissions = permissions.union(_get_object_permissions(membership, obj.parent))

    return permissions


def get_object_permissions(membership, obj):
    try:
        ct = get_contenttype(obj)
        key = 'object_{0}_{1}'.format(ct.id, obj.id)
        return get_cached_permissions(membership, key, _get_object_permissions, membership, obj)
    except Exception as e:
        logger.exception(e)
    return set()


def has_object_permission(membership, obj, permission):
    return obj is not None and permission in get_object_permissions(membership, obj)


def filter_by_permission(objects, membership, permission, use_queryset=False):
    allowed = [obj for obj in objects if has_object_permission(membership, obj, permission)]
    if use_queryset:
        return objects.filter(id__in=[obj.id for obj in allowed])
    else:
        return allowed
