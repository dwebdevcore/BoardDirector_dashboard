# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-15 15:33
from __future__ import unicode_literals

import croppy.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_auto_20170410_1510'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='crops',
            field=croppy.fields.CropField(editable=False, image_field=b'avatar'),
        ),
    ]
