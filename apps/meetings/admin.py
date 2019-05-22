# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Meeting, CalendarConnection, MeetingAttendance


class MeetingAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end', 'committee', 'account', 'is_event')


class CalendarConnectionAdmin(admin.ModelAdmin):
    list_display = ('account', 'email', 'provider')


class MeetingAttendanceAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'user', 'present')
    readonly_fields = ('meeting', 'user')

    def has_add_permission(self, request):
        return False


admin.site.register(Meeting, MeetingAdmin)
admin.site.register(CalendarConnection, CalendarConnectionAdmin)
admin.site.register(MeetingAttendance, MeetingAttendanceAdmin)
