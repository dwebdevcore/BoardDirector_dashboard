# -*- coding: utf-8 -*-
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Folder, Document, AuditTrail


class FolderAdmin(MPTTModelAdmin):
    mptt_level_indent = 10
    list_display = ('name', 'created', 'protected')
    search_fields = ('name', 'account__name', 'account__url')
    list_filter = ('created', 'protected')
    date_hierarchy = 'created'
    raw_id_fields = ('user', 'account', 'meeting')
    readonly_fields = ('slug',)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('file', 'name', 'type', 'created_at',)
    raw_id_fields = ('user', 'account', 'folder')


class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('file', 'name', 'type', 'change_type', 'created_at',)
    raw_id_fields = ('user',)

admin.site.register(Folder, FolderAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(AuditTrail, AuditTrailAdmin)
