# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-13 18:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='votingquestion',
            name='question_type',
            field=models.IntegerField(choices=[(1, 'Yes/no'), (2, 'Single Select'), (3, 'Multiple Select'), (4, 'Election')], default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='voting',
            name='state',
            field=models.IntegerField(choices=[(0, 'Draft'), (1, 'Published')]),
        ),
        migrations.AlterField(
            model_name='votingvoter',
            name='email',
            field=models.EmailField(blank=True, max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='votingvoter',
            name='first_name',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='votingvoter',
            name='last_name',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='votingvoter',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='profiles.Membership'),
        ),
    ]