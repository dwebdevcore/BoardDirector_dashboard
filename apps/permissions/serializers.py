from rest_framework import serializers

from permissions.models import ObjectPermission


class ObjectPermissionsBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectPermission
        fields = ['id', 'role', 'membership', 'permission']
