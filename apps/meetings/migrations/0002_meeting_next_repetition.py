# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-21 09:51
from __future__ import unicode_literals

from django.db import migrations


def forward(apps, schema_editor):
    from meetings.advanced_migrations import meeting_next_repetitions_migration
    meeting_next_repetitions_migration(schema_editor.connection, schema_editor.execute)


def backward(apps, schema_editor):
    schema_editor.execute('drop view meetings_meetingnextrepetition')


class Migration(migrations.Migration):
    dependencies = [
        ('meetings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forward, backward)
    ]
