from rest_framework import serializers

from accounts.models import Account


class AccountSerializer(serializers.ModelSerializer):
    max_storage = serializers.SerializerMethodField()

    def get_max_storage(self, account):
        return account.get_max_storage()

    class Meta:
        model = Account
        fields = ['id', 'name', 'url', 'send_notification', 'plan',
                  'total_storage_size', 'max_storage', 'date_created', 'is_active']
        read_only_fields = ['date_created', 'is_active']
