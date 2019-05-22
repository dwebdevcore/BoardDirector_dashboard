# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Committee


class CommitteeAdmin(admin.ModelAdmin):
    list_display = ('name', 'account',)

admin.site.register(Committee, CommitteeAdmin)
