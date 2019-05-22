from rest_framework import serializers

from common.models import AuthToken
from profiles.serializers import UserSerializer


class TokenSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta(object):
        model = AuthToken
        fields = ['token', 'created', 'user']
