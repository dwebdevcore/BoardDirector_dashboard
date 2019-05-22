# -*- coding: utf-8 -*-
from django.contrib import admin
from permissions.models import RolePermission, ObjectPermission


class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'content_type', 'permission')
    list_filter = ('role', 'permission')


class ObjectPermissionAdmin(admin.ModelAdmin):
    def content_object_name(self, obj):
        return str(obj.content_object) if obj.content_object else ''
    content_object_name.short_description = 'Content object'

    list_display = ('content_object_name', 'content_type', 'role', 'membership', 'permission')
    search_fields = ('membership__user__email', 'membership__account__name')
    list_filter = ('role', 'permission')
    readonly_fields = ('content_object_name',)


admin.site.register(RolePermission, RolePermissionAdmin)
admin.site.register(ObjectPermission, ObjectPermissionAdmin)
