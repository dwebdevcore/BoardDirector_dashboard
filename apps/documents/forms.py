# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from common.shortcuts import reorder_form_fields
from .models import Document, AuditTrail, Folder
from profiles.models import Membership
from permissions import PERMISSIONS
from permissions.models import ObjectPermission


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file', ]


class DocumentDeleteForm(forms.Form):
    document_id = forms.IntegerField(min_value=1)
    action = forms.CharField(required=False)
    change_type = forms.IntegerField(required=False)

    def clean(self):
        data = self.cleaned_data
        data['change_type'] = AuditTrail.DELETED
        if data['action'] == 'update':
            data['change_type'] = AuditTrail.UPDATED
        return data


class DocumentAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DocumentAddForm, self).__init__(*args, **kwargs)
        self.fields['file'] = forms.FileField(label='', required=False)
        self.fields['uploaded_file'] = forms.CharField(widget=forms.HiddenInput(), required=False)
        self.fields['notify_group'] = forms.CharField(widget=forms.HiddenInput(), required=False)
        self.fields['notify_me'] = forms.CharField(widget=forms.HiddenInput(), required=False)
        self.fields = reorder_form_fields(self.fields, ['file', 'uploaded_file', 'notify_group', 'notify_me'])

    class Meta:
        model = Document
        fields = []

    def clean_uploaded_file(self):
        data = self.cleaned_data['uploaded_file']
        if not data:
            raise forms.ValidationError(_('You have not added any documents.'))
        return data


class DocumentRenameForm(forms.Form):
    document_id = forms.IntegerField(min_value=1)
    filename = forms.CharField(required=True, max_length=255)

    def clean(self):
        data = self.cleaned_data
        if not data.get('filename'):
            raise forms.ValidationError(_('Invalid filename.'))
        return data


class MessageForm(forms.Form):
    subject = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'txt', 'placeholder': _('Subject')}), max_length=255)
    body = forms.CharField(widget=forms.Textarea(attrs={'class': 'txt kendo_editor'}))


class FolderAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = 'add'
        super(FolderAddForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Folder
        fields = ['name']


class FolderEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = 'edit'
        super(FolderEditForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Folder
        fields = ['name']


class FolderMoveForm(forms.Form):
    target_slug = forms.SlugField()


class ShareAddForm(forms.Form):
    role = forms.ChoiceField(choices=[(0, _('Select ... ')),
                                      (Membership.ROLES.member, _('All Board Members')),
                                      (Membership.ROLES.guest, _('All Board Guests'))])
    memberships = forms.ModelMultipleChoiceField(required=False, queryset=Membership.objects.none(),
                                                 widget=forms.SelectMultiple(attrs={'placeholder': _('Type in names')}))
    permission = forms.ChoiceField(choices=[(PERMISSIONS.view, _('Can View')), (PERMISSIONS.edit, _('Can Edit'))])

    def __init__(self, account, *args, **kwargs):
        kwargs['prefix'] = 'share'
        super(ShareAddForm, self).__init__(*args, **kwargs)
        self.fields['memberships'].queryset = Membership.objects.filter(account=account, user__is_active=True, is_active=True).select_related('user')


class ShareDeleteForm(forms.Form):
    object_permission_id = forms.IntegerField(min_value=1)
