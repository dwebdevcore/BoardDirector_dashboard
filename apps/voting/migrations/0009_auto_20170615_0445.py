# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-15 09:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0008_merge_20170524_1859'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='voteranswer',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='votingquestionanswer',
            options={'ordering': ['id']},
        ),
        migrations.AlterField(
            model_name='voteranswer',
            name='answers',
            field=models.ManyToManyField(blank=True, to='voting.VotingQuestionAnswer'),
        ),
        migrations.AlterUniqueTogether(
            name='voteranswer',
            unique_together=set([('voter', 'question')]),
        ),
    ]
