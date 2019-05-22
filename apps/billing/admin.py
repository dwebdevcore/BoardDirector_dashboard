# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Plan, BillingSettings, Invoice


class PlanAdmin(admin.ModelAdmin):
    list_display = ('name_str', 'available', 'max_members', 'max_storage',
                    'month_price', 'year_price',
                    'stripe_month_plan_id', 'stripe_year_plan_id',)
    list_display_links = list_display
    search_fields = ['pname', 'stripe_year_plan_id', 'stripe_month_plan_id']


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('account', 'payment', 'status', 'created_at', 'payed_period_end')
    search_fields = ['account', ]

admin.site.register(Plan, PlanAdmin)
admin.site.register(BillingSettings)
admin.site.register(Invoice, InvoiceAdmin)
