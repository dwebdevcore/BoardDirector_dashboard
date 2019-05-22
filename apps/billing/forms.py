# -*- coding: utf-8 -*-
import stripe
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from accounts.models import Account
from billing.models import BillingSettings, Plan
from common.common_data import COUNTRIES


class PlanChangeForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['plan']
        widgets = {
            'plan': forms.RadioSelect()
        }


class BillingSettingsEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BillingSettingsEditForm, self).__init__(*args, **kwargs)

        self.fields['stripe_token'] = forms.CharField(widget=forms.HiddenInput, required=False)
        self.fields['city'].required = True

    class Meta:
        model = BillingSettings
        fields = ['address', 'city', 'state', 'zip', 'country', 'mail', 'name', 'discount', 'unit_number']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'zip': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'country': forms.Select(choices=zip(COUNTRIES, COUNTRIES), attrs={'class': 'form-control default', 'required': 'required'}),
            'mail': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'discount': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter your promocode here')}),
            'unit_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_discount(self):
        discount = self.cleaned_data.get('discount', '').strip()
        if discount:
            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe.Coupon.retrieve(discount)
            except stripe.StripeError as e:
                raise forms.ValidationError(e)
        return discount


class ChangePlanForm(forms.Form):
    cycle = forms.IntegerField(widget=forms.HiddenInput, required=True)
    plan = forms.ModelChoiceField(Plan.list_available_plans(), widget=forms.HiddenInput, required=True)


class BillingAddressEditForm(forms.ModelForm):
    class Meta:
        model = BillingSettings
        fields = ['address', 'city', 'state', 'zip', 'country', 'mail', 'name']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'txt'}),
            'city': forms.TextInput(attrs={'class': 'txt'}),
            'state': forms.TextInput(attrs={'class': 'txt'}),
            'zip': forms.TextInput(attrs={'class': 'txt'}),
            'country': forms.TextInput(attrs={'class': 'txt'}),
            'mail': forms.TextInput(attrs={'class': 'txt'}),
            'name': forms.TextInput(attrs={'class': 'txt'}),
        }
