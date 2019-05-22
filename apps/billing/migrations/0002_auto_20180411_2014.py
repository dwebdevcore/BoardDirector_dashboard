# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-12 01:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billingsettings',
            name='card_number',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='credit card number'),
        ),
        migrations.AlterField(
            model_name='billingsettings',
            name='cvv',
            field=models.CharField(blank=True, max_length=4, null=True, verbose_name='cvv'),
        ),
    ]
