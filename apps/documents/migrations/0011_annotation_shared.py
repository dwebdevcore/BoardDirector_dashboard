# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-10 14:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0010_auto_20171119_2354'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='shared',
            field=models.BooleanField(default=False),
        ),
    ]
