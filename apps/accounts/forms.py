# -*- coding: utf-8 -*-
from django import forms
from accounts.models import Account


class AccountReactivateForm(forms.Form):
    account_id = forms.IntegerField(min_value=1)


class AccountLogo(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('logo',)


class AccountNotify(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('send_notification', 'view_email', 'default_meetings_location')
