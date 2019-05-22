from rest_framework import viewsets

from committees.models import Committee
from committees.serializers import CommitteeSerializer
from common.mixins import GetMembershipWithURLFallbackMixin


# Readonly as writing isn't needed now and one should control permissions better for writing
from permissions.mixins import RestPermissionMixin
from permissions.rest_permissions import IsMember, CheckAccountUrl


class CommitteeViewSet(GetMembershipWithURLFallbackMixin, RestPermissionMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CommitteeSerializer
    permission_classes = [IsMember, CheckAccountUrl]
    permission = (Committee, 'view')

    def get_queryset(self):
        return Committee.objects.for_membership(self.get_current_membership()).prefetch_related('memberships', 'chairman')
