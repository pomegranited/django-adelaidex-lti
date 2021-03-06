# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-30 12:12
from __future__ import unicode_literals

from django.db import migrations, models
import django_adelaidex.lti.models


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            'user',
            managers=[
                ('objects', django_adelaidex.lti.models.UserManager()),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(verbose_name='last login', blank=True, null=True),
        ),
    ]
