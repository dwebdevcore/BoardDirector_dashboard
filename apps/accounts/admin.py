# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Account
from billing.models import BillingSettings


class BillingSettingsInline(admin.StackedInline):
    model = BillingSettings
    extra = 1


class AccountAdmin(admin.ModelAdmin):
    inlines = [BillingSettingsInline, ]
    list_display = ('name', 'plan', 'is_active', 'total_storage_size')
    search_fields = ['name', 'url', ]
    list_filter = ('is_active', 'unlimited_trial', 'plan')

admin.site.register(Account, AccountAdmin)
