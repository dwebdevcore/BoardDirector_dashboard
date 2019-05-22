# -*- coding: utf-8 -*-
from django.contrib import admin

from common.forms import TemplateForm
from .models import Feedback, TemplateModel, UpdateNotification


class TemplateAdmin(admin.ModelAdmin):
    form = TemplateForm

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class UpdateNotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_text', 'publish_date', 'is_active', 'details_link']


admin.site.register(Feedback)
admin.site.register(TemplateModel, TemplateAdmin)
admin.site.register(UpdateNotification, UpdateNotificationAdmin)
