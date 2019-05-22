from rest_framework import serializers

from committees.models import Committee
from profiles.serializers import MembershipShortSerializer


class CommitteeSerializer(serializers.ModelSerializer):
    memberships = MembershipShortSerializer(many=True)
    chairman = MembershipShortSerializer(many=True)

    class Meta:
        model = Committee
        fields = ['id', 'name', 'chairman', 'description', 'account', 'memberships']
