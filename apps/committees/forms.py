# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from common.shortcuts import reorder_form_fields
from .models import Committee
from profiles.models import Membership


class CommitteeFilter(forms.Form):
    def __init__(self, membership, *args, **kwargs):
        super(CommitteeFilter, self).__init__(*args, **kwargs)
        committee_options = ([('', _('All Committees'))]
                             + [(c.id, c.name) for c in Committee.objects.for_membership(membership)])
        self.fields['committee'] = forms.ChoiceField(committee_options, required=False,
                                                     widget=forms.Select(attrs={'class': 'submit-form committee-select'}))


class CommitteeAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CommitteeAddForm, self).__init__(*args, **kwargs)
        account_users = Membership.objects.filter(account=kwargs['initial']['account'], is_active=True).exclude(role=Membership.ROLES.assistant)
        self.fields['summary'].label = _('Add Summary')
        if self.instance.pk:
            initial = Membership.objects.filter(committees=self.instance)
        else:
            initial = []
        self.fields['chairman'] = forms.ModelMultipleChoiceField(queryset=account_users,
                                                                 widget=forms.SelectMultiple(attrs={'class': 'multiple selectize-300px'}),
                                                                 initial=initial,
                                                                 required=True,
                                                                 label=_('Add Chairman'))
        self.fields['members'] = forms.ModelMultipleChoiceField(queryset=account_users,
                                                                widget=forms.SelectMultiple(attrs={'class': 'multiple selectize-300px'}),
                                                                initial=initial,
                                                                required=True,
                                                                label=_('Add Members'))
        self.fields['uploaded'] = forms.IntegerField(widget=forms.HiddenInput(), required=False)
        self.fields = reorder_form_fields(self.fields, ['name', 'chairman', 'members', 'summary', 'description'])

    class Meta:
        model = Committee
        exclude = ['account']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'txt title', 'placeholder': _('Untitled Committee')}),
            'description': forms.Textarea(attrs={'class': 'kendo_editor'}),
            'summary': forms.Textarea(attrs={'class': 'k-textbox'})
        }
