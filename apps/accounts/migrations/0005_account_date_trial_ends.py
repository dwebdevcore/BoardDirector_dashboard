# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-31 11:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20170615_0445'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='date_trial_ends',
            field=models.DateTimeField(blank=True, null=True, verbose_name='trial end date'),
        ),
    ]
