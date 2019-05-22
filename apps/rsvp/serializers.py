from rest_framework import serializers

from common.mixins import FilterSerializerByAccountMixin
from rsvp.models import RsvpResponse


class RsvpResponseSerializer(FilterSerializerByAccountMixin, serializers.ModelSerializer):
    def __init__(self, instance=None, **kwargs):
        super(RsvpResponseSerializer, self).__init__(instance, **kwargs)
        # Meeting and user are readonly so no filtering required
        self.filter_account('meeting_repetition', account_field='meeting__account')

    class Meta:
        model = RsvpResponse
        fields = '__all__'
        read_only_fields = ['timestamp', 'user', 'meeting']
