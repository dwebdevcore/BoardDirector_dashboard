# -*- coding: utf-8 -*-
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from .forms import UserChangeForm, UserCreationForm
from .models import User, Membership


class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ()}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
         ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'is_active', 'is_admin', 'role', 'account', 'membership_actions')
    search_fields = ['user__email', 'account__name', 'first_name', 'last_name']

    def full_name(self, membership):
        return membership.get_full_name()

    def membership_actions(self, membership):
        return format_html('<a href="%s?user_id=%d" class="button">Login as user</a>' % (reverse('profiles:switch_user'), membership.user.id))


admin.site.register(User, UserAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.unregister(Group)
