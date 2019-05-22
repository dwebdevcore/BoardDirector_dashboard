# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-15 09:45
from __future__ import unicode_literals

import common.utils
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0007_merge_20170605_0631'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='is_admin',
            field=models.BooleanField(default=False, verbose_name='admin'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='avatar',
            field=models.ImageField(blank=True, storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/avatars/', location=b'/home/ubuntu/www/boarddirector/public/media/avatars'), upload_to=common.utils.avatar_upload_to),
        ),
        migrations.AlterField(
            model_name='membership',
            name='role',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Board Chair'), (20, 'CEO'), (21, 'Executive Director'), (2, 'Board Member'), (3, 'Executive Assistant'), (4, 'Guest'), (5, 'Vendor'), (6, 'Staff'), (7, 'Consultant')], default=2, verbose_name='role'),
        ),
    ]