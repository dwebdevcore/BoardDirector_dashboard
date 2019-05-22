# -*- coding: utf-8 -*-
import re
from collections import OrderedDict
from django import forms
from django.contrib.auth.forms import (ReadOnlyPasswordHashField,
                                       UserChangeForm as BaseUserChangeForm)
from django.utils import timezone
from django.utils.translation import ugettext as _

from committees.models import Committee
from common.shortcuts import reorder_form_fields
from .models import User, Membership


class UserChangeForm(BaseUserChangeForm):
    email = forms.EmailField(label=_('Email'), max_length=75)
    password = ReadOnlyPasswordHashField(label=_('Password'),
                                         help_text=_('Raw passwords are not stored, so there is no way to see '
                                                     "this user's password, but you can change the password "
                                                     'using <a href="password/">this form</a>.'))


class UserCreationForm(forms.ModelForm):
    email = forms.EmailField(label=_('Email'), max_length=75)
    password1 = forms.CharField(label=_('Password'),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'),
                                widget=forms.PasswordInput,
                                help_text=_('Enter the same password as above, for verification.'))

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ListTextWidget(forms.TextInput):
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<select id="select-role-box">'
        for item in self._list:
            data_list += '<option value="%s">%s</option>' % (item, item)
        data_list += '</select>'

        return '<div id="wrapper-for-role">' + text_html + data_list + '</div>'


class MembershipBaseForm(forms.ModelForm):
    x1 = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    y1 = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    x2 = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    y2 = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    first_name = forms.CharField(label=_('First Name'), max_length=30,
                                 widget=forms.TextInput(attrs={'class': 'txt'}), required=True)
    last_name = forms.CharField(label=_('Last Name'), max_length=30,
                                widget=forms.TextInput(attrs={'class': 'txt'}), required=True)
    email = forms.EmailField(label=_('Email'), max_length=75,
                             widget=forms.TextInput(attrs={'class': 'txt'}), required=True)
    phone_number = forms.CharField(label=_('Phone Number'), max_length=13,
                                   widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    employer = forms.CharField(label=_('Employer'), max_length=50,
                               widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    job_title = forms.CharField(label=_('Job Title'), max_length=50,
                                widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    work_email = forms.EmailField(label=_('Work Email'), max_length=75,
                                  widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    work_number = forms.CharField(label=_('Work Number'), max_length=13,
                                  widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    intro = forms.CharField(label=_('Intro'), max_length=100,
                            widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    bio = forms.CharField(label=_('Short Bio'), widget=forms.Textarea(attrs={'class': 'txt'}), required=False)

    title = forms.CharField(label=_('Title'), max_length=150,
                            widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    description = forms.CharField(label=_('Description'), widget=forms.Textarea(attrs={'class': 'txt'}), required=False)

    address = forms.CharField(label=_('Address'), max_length=150,
                              widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    secondary_address = forms.CharField(label=_('Address (opt)'), max_length=150,
                                        widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    city = forms.CharField(label=_('City'), max_length=100,
                           widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    state = forms.CharField(label=_('State'), max_length=100,
                            widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    zip = forms.CharField(label=_('Zip'), max_length=50,
                          widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    country = forms.CharField(label=_('Country'), max_length=100,
                              widget=forms.TextInput(attrs={'class': 'txt'}), required=False)

    work_address = forms.CharField(label=_('Work Address'), max_length=150,
                                   widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    work_secondary_address = forms.CharField(label=_('Work Address (opt)'), max_length=150,
                                             widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    work_city = forms.CharField(label=_('City'), max_length=100,
                                widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    work_state = forms.CharField(label=_('State'), max_length=100,
                                 widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    work_zip = forms.CharField(label=_('Zip'), max_length=50,
                               widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    work_country = forms.CharField(label=_('Country'), max_length=100,
                                   widget=forms.TextInput(attrs={'class': 'txt'}), required=False)

    birth_date = forms.CharField(label=_('Date of Birth'), max_length=100,
                                 widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    secondary_phone = forms.CharField(label=_('Cell Phone'), max_length=12,
                                      widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    # affiliation = forms.CharField(label=_('Affiliations'), max_length=150,
    #                               widget=forms.TextInput(attrs={'class': 'txt'}), required=False)
    # social_media_link = forms.CharField(label=_('Social Media Links'), max_length=150,
    #                                     widget=forms.TextInput(attrs={'class': 'txt'}), required=False)

    notes = forms.CharField(label=_(''), widget=forms.Textarea(attrs={'class': 'txt'}), required=False)

    password1 = forms.CharField(label=_('Password'),
                                widget=forms.PasswordInput(attrs={'class': 'txt pswd'}), required=False)
    password2 = forms.CharField(label=_('Password confirmation'),
                                widget=forms.PasswordInput(attrs={'class': 'txt pswd'}),
                                required=False,
                                help_text=_('Enter the same password as above, for verification.'))

    def __init__(self, *args, **kwargs):
        super(MembershipBaseForm, self).__init__(*args, **kwargs)
        self.fields['add_another'] = forms.BooleanField(widget=forms.HiddenInput(), required=False, initial=False)
        self.fields['role'] = forms.IntegerField(widget=forms.HiddenInput(), required=False)
        self.fields['custom_role_name'] = forms.CharField(label=_('Role in Organization'),
                                                          widget=ListTextWidget(data_list=[],
                                                                                name="custom_role_name",
                                                                                attrs={
                                                                                    'id': 'edit-role-box',
                                                                                    'autocomplete': 'off',
                                                                                    'placeholder': 'Select or enter custom role',
                                                                                    'title': 'Select or enter custom role'
                                                              }),
                                                          max_length=50,
                                                          required=True)

        self.fields['is_active'] = forms.ChoiceField(label=_('Status in Organization'), choices=[])

        self.fields['committees'] = forms.ModelMultipleChoiceField(
            queryset=Committee.objects.filter(account=self.initial['account']),
            widget=forms.SelectMultiple(attrs={'class': 'multiple selectize-270px'}),
            required=False,
            label=_('Committees')
        )

        self.fields['term_start'] = forms.DateField(label=_('Start Date of Board Term'), input_formats=['%b. %d, %Y'],
                                                    widget=forms.DateInput(format='%b. %d, %Y', attrs={
                                                        'placeholder': '{:%b. %d, %Y}'.format(timezone.now())}
            ), required=False)
        self.fields['term_expires'] = forms.DateField(label=_('End Date of Board Term'), input_formats=['%b. %d, %Y'],
                                                      widget=forms.DateInput(format='%b. %d, %Y', attrs={
                                                          'placeholder': '{:%b. %d, %Y}'.format(timezone.now())}
            ), required=False)
        self.fields['timezone'].label = _('Time Zone')
        self.initial['timezone'] = self.instance.timezone if self.instance.timezone else timezone.get_current_timezone()

        self.fields['is_admin'] = forms.BooleanField(widget=forms.CheckboxInput,
                                                     label=_('Is an Administrator?'), required=False)

        key_order = ['add_another',
                     'avatar', 'x1', 'x2', 'y1', 'y2',
                     'first_name', 'last_name', 'email', 'timezone', 'secondary_phone', 'phone_number',
                     'role', 'custom_role_name', 'is_active', 'term_start', 'term_expires',
                     'committees', 'is_admin',
                     'address', 'secondary_address', 'city', 'state', 'zip', 'country', 'birth_date',

                     'employer', 'job_title', 'work_email', 'work_number',
                     'work_address', 'work_secondary_address', 'work_city', 'work_state', 'work_zip', 'work_country',
                     'intro', 'bio',

                     'notes',
                     'password1', 'password2']

        self.fields = reorder_form_fields(self.fields, key_order)

    by_tabs = OrderedDict([('avatar', (_('Personal'), _('Personal Info'))),
                           ('employer', (_('Work Details'), _("Work Details"))),
                           ('notes', (_("Notes"), _("Notes"))),
                           ('password1', (_('Security'), _('Security')))])

    def visible_fields_by_tabs(self):
        """ for tabbed form returns list of tabs with list of available fields """

        alltabs = []
        tab = None
        for vf in self.visible_fields():
            if vf.name in self.by_tabs.keys():
                if tab is not None:
                    alltabs.append(tab)
                tab = {'name': self.by_tabs[vf.name][0], 'header': self.by_tabs[vf.name][1], 'fields': [vf, ]}
            else:
                if tab is not None:
                    tab['fields'].append(vf)

        if tab is not None:
            alltabs.append(tab)

        return alltabs

    def clean(self):

        cleaned_data = super(MembershipBaseForm, self).clean()

        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(_("The two password fields didn't match."))
        else:
            cleaned_data['password1'] = cleaned_data['password2'] = None

        return cleaned_data

    class Meta:
        model = Membership
        exclude = []

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email__iexact=email)
        if qs.count() > 0:
            raise forms.ValidationError(_('This email is already in use.'))
        return email

    def clean_phone_number(self):
        phones = self.cleaned_data['phone_number']
        pattern = r'^\d{3}-\d{3}-\d{4,5}$'
        parsed = []
        for phone in phones.split(','):
            phone = phone.strip('_')
            if phone and (not re.match(pattern, phone) or len(phone) not in range(12, 14)):
                raise forms.ValidationError(_('Phone number is invalid.'))
            parsed.append(phone)
        return ','.join(parsed)


class MembershipEditForm(MembershipBaseForm):

    by_tabs = OrderedDict([('avatar', (_('Personal'), _('Personal Info'))),
                           ('employer', (_('Work Details'), _("Work Details"))),
                           ('password1', (_('Security'), _('Security')))])

    def __init__(self, *args, **kwargs):
        super(MembershipEditForm, self).__init__(*args, **kwargs)

        fields = self.fields
        for key in ['role', 'custom_role_name', 'is_active', 'committees', 'term_start', 'term_expires', 'is_admin', 'notes']:
            del fields[key]

    def clean_email(self):
        email = self.cleaned_data['email']
        if email != self.initial['email']:
            qs = User.objects.filter(email__iexact=email)
            if qs.count() > 0:
                raise forms.ValidationError(_('This email is already in use.'))

        return email


class MembershipAdminEditForm(MembershipBaseForm):
    def __init__(self, *args, **kwargs):
        super(MembershipAdminEditForm, self).__init__(*args, **kwargs)
        self.roles = self.get_roles()
        status = [s for s in Membership.STATUS if s[0] in (Membership.STATUS.active, Membership.STATUS.inactive)]

        self.fields['custom_role_name'].widget = ListTextWidget(data_list=self.roles,
                                                                name="custom_role_name",
                                                                attrs={
                                                                    'id': 'edit-role-box',
                                                                    'autocomplete': 'off',
                                                                    'placeholder': 'Select or enter custom role',
                                                                    'title': 'Select or enter custom role'
                                                                })

        if self.instance.custom_role_name is None or self.instance.custom_role_name == '':
            self.initial['custom_role_name'] = self.instance.get_role_display

        self.fields['is_active'] = forms.ChoiceField(label=_('Status in Organization'), choices=status)

        self.initial['committees'] = self.instance.committees.all()

        if self.instance.is_guest:
            fields = self.fields
            del fields['term_start']
            del fields['term_expires']

    def get_roles(self):

        role_groups = (
            (Membership.ROLES.chair, Membership.ROLES.ceo, Membership.ROLES.director, Membership.ROLES.member),
            (Membership.ROLES.assistant,),
            (Membership.ROLES.guest, Membership.ROLES.vendor, Membership.ROLES.staff, Membership.ROLES.consultant),
        )
        for group in role_groups:

            if self.instance.role in group:

                hardroles = [r[1] for r in Membership.ROLES if r[0] in group]

                # add also all manual entered roles
                if self.initial.get('account'):
                    qs = Membership.objects.filter(is_active=True, account=self.initial['account'])\
                        .order_by().values_list('custom_role_name', flat=True).distinct()
                    custroles = set(filter(lambda x: len(x) > 0, qs))
                else:
                    custroles = []

                for c in custroles:
                    if c not in hardroles:
                        hardroles.append(c)

                return hardroles

    def clean_email(self):
        email = self.cleaned_data['email']
        if email != self.initial['email']:
            qs = User.objects.filter(email__iexact=email)
            if qs.count() > 0:
                raise forms.ValidationError(_('This email is already in use.'))

        return email

    def clean(self):
        cleaned_data = super(MembershipAdminEditForm, self).clean()

        custom_name = cleaned_data.get('custom_role_name')

        if self.instance.is_guest:
            cleaned_data['role'] = Membership.ROLES.guest
        else:
            cleaned_data['role'] = Membership.ROLES.member

        if custom_name is None:
            raise forms.ValidationError(_('Role is required.'))

        if custom_name in self.roles:
            for role in Membership.ROLES:
                if role[1] == custom_name:
                    cleaned_data['role'] = role[0]
                    break

        return cleaned_data


class MemberAddForm(MembershipBaseForm):
    def __init__(self, *args, **kwargs):
        super(MemberAddForm, self).__init__(*args, **kwargs)
        self.roles = self.get_roles()
        status = [s for s in Membership.STATUS if s[0] in (Membership.STATUS.active, Membership.STATUS.inactive)]

        self.fields['custom_role_name'].widget = ListTextWidget(data_list=self.roles,
                                                                name="custom_role_name",
                                                                attrs={
                                                                    'id': 'edit-role-box',
                                                                    'autocomplete': 'off',
                                                                    'placeholder': 'Select or enter custom role',
                                                                    'title': 'Select or enter custom role'
                                                                })
        self.fields['is_active'] = forms.ChoiceField(label=_('Status in Organization'), choices=status)

    def get_roles(self):
        roles = (Membership.ROLES.chair, Membership.ROLES.ceo, Membership.ROLES.director, Membership.ROLES.member)
        hardroles = [r[1] for r in Membership.ROLES if r[0] in roles]

        # add also all manual entered roles
        if self.initial.get('account'):
            qs = Membership.objects.filter(is_active=True, account=self.initial['account'])\
                .order_by().values_list('custom_role_name', flat=True).distinct()
            custroles = set(filter(lambda x: len(x) > 0, qs))
        else:
            custroles = []

        for c in custroles:
            if c not in hardroles:
                hardroles.append(c)

        return hardroles

    def clean(self):
        cleaned_data = super(MemberAddForm, self).clean()

        custom_name = cleaned_data['custom_role_name']

        cleaned_data['role'] = Membership.ROLES.member

        if custom_name is None:
            raise forms.ValidationError(_('Role is required.'))

        if custom_name in self.roles:
            for role in Membership.ROLES:
                if role[1] == custom_name:
                    cleaned_data['role'] = role[0]
                    break

        return cleaned_data


class GuestAddForm(MembershipBaseForm):
    def __init__(self, *args, **kwargs):
        super(GuestAddForm, self).__init__(*args, **kwargs)
        self.roles = self.get_roles()
        status = [s for s in Membership.STATUS if s[0] in (Membership.STATUS.active, Membership.STATUS.inactive)]

        self.fields['custom_role_name'].widget = ListTextWidget(data_list=self.roles,
                                                                name="custom_role_name",
                                                                attrs={
                                                                    'id': 'edit-role-box',
                                                                    'autocomplete': 'off',
                                                                    'placeholder': 'Select or enter custom role',
                                                                    'title': 'Select or enter custom role'
                                                                })

        self.fields['is_active'] = forms.ChoiceField(label=_('Status in Organization'), choices=status)

        fields = self.fields
        del fields['term_start']
        del fields['term_expires']

    def get_roles(self):

        roles = (Membership.ROLES.guest, Membership.ROLES.vendor,
                 Membership.ROLES.staff, Membership.ROLES.consultant,
                 Membership.ROLES.assistant)
        hardroles = [r[1] for r in Membership.ROLES if r[0] in roles]

        # add also all manual entered roles
        if self.initial.get('account'):
            qs = Membership.objects.filter(is_active=True, account=self.initial['account'])\
                .order_by().values_list('custom_role_name', flat=True).distinct()
            custroles = set(filter(lambda x: len(x) > 0, qs))
        else:
            custroles = []

        for c in custroles:
            if c not in hardroles:
                hardroles.append(c)

        return hardroles

    def clean(self):
        cleaned_data = super(GuestAddForm, self).clean()

        custom_name = cleaned_data['custom_role_name']

        cleaned_data['role'] = Membership.ROLES.guest

        if custom_name is None:
            raise forms.ValidationError(_('Role is required.'))

        if custom_name in self.roles:
            for role in Membership.ROLES:
                if role[1] == custom_name:
                    cleaned_data['role'] = role[0]
                    break

        return cleaned_data


class AssistantAddForm(MembershipBaseForm):

    by_tabs = OrderedDict([('first_name', (_('Personal'), _('Personal Info'))),
                           ('employer', (_('Work Details'), _("Work Details"))),
                           ('notes', (_("Notes"), _("Notes"))),
                           ('password1', (_('Security'), _('Security')))])

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.initial['timezone'] = timezone.get_current_timezone()

    class Meta(MembershipBaseForm.Meta):
        fields = ('first_name', 'last_name', 'email', 'timezone', 'avatar', 'phone_number')


class AssistantEditForm(MembershipEditForm):

    def __init__(self, *args, **kwargs):
        super(AssistantEditForm, self).__init__(*args, **kwargs)

        fields = self.fields
        for key in ['role', 'custom_role_name', 'is_active', 'committees', 'term_start', 'term_expires', 'is_admin', 'notes']:
            if key in fields:
                del fields[key]

        self.initial['timezone'] = timezone.get_current_timezone()

    class Meta(MembershipEditForm.Meta):
        fields = ('first_name', 'last_name', 'email', 'timezone', 'avatar', 'phone_number')
