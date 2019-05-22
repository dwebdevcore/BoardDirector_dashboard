from rest_framework import serializers

from accounts.serializers import AccountSerializer
from profiles.models import Membership, User
from django.conf import settings


class MembershipShortSerializer(serializers.ModelSerializer):

    avatar_url = serializers.SerializerMethodField()
    avatar_path = serializers.StringRelatedField(source='avatar_url', read_only=True)
    role_name = serializers.StringRelatedField(source='get_role_name', read_only=True)

    def get_avatar_url(self, obj):
        avurl = obj.avatar_url(geometry='200x200')
        if self.context and 'request' in self.context:
            return self.context['request'].build_absolute_uri(avurl)
        elif 'MEDIA_HOST' in settings.__dict__:
            return "%s%s" % (settings.MEDIA_HOST, avurl)
        else:
            return avurl

    class Meta:
        model = Membership
        fields = ['id', 'first_name', 'last_name', 'bio', 'is_guest', 'avatar_path', 'avatar_url', 'role_name', 'account']


class UserSerializer(serializers.ModelSerializer):
    accounts = AccountSerializer(many=True)
    memberships = MembershipShortSerializer(many=True, source='membership_set')

    class Meta:
        model = User
        fields = ['id', 'email', 'accounts', 'memberships']


class RestorePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
