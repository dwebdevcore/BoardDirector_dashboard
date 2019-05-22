# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-09 09:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, verbose_name='email address')),
                ('message', models.TextField(verbose_name='message')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Feedback',
                'verbose_name_plural': 'Feedbacks',
            },
        ),
        migrations.CreateModel(
            name='TemplateModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.IntegerField(choices=[(1, 'account activation template'), (2, 'password reset template'), (3, 'meeting invitation template'), (4, 'member invitation template'), (5, 'account canceled template'), (6, 'trial is over template'), (7, 'trial is over and account cancel template'), (8, 'paid is over template'), (9, 'trial reminder template'), (10, 'add document template'), (11, 'document updated template'), (12, 'meeting reminder updated template')], editable=False, max_length=100, unique=True, verbose_name='name')),
                ('title', models.CharField(max_length=100, verbose_name='subject')),
                ('html', models.TextField(help_text='Do not change text in braces', verbose_name='content')),
            ],
            options={
                'verbose_name': 'Template editor',
                'verbose_name_plural': 'Template editors',
            },
        ),
    ]
