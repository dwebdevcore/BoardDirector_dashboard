# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-28 20:24
from __future__ import unicode_literals

import common.utils
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0014_auto_20170915_0653'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='custom_role_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='custom role name'),
        ),
    ]
