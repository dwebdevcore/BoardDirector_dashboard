# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-18 13:22
from __future__ import unicode_literals

import common.storage_backends
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_account_plan'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='logo',
            field=models.ImageField(blank=True, null=True, storage=common.storage_backends.StableS3BotoStorage(acl=b'private', file_overwrite=False), upload_to=b'logotypes/%Y%m%d', verbose_name='logotype'),
        ),
    ]
