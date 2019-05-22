# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from voting.models import Voting


class VotingAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'name', 'description', 'is_anonymous', 'is_active', 'end_time']
    list_filter = ['account', 'is_active', 'is_anonymous']


admin.site.register(Voting, VotingAdmin)
