# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0002_auto_20151230_1212'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text='Required. Will be displayed to students as the "course name" on the login screen.', max_length=500, verbose_name='title')),
                ('login_url', models.URLField(help_text='Required. Choose a URL in your course that displays the LTI component.', max_length=500, verbose_name='login url')),
                ('enrol_url', models.URLField(default=None, max_length=500, blank=True, help_text='Optional. Provide a URL for students to enrol in your course.', null=True, verbose_name='enrol url')),
                ('oauth_key', models.CharField(help_text='Required. 255 characters or fewer, but must be unique. Letters, digits and .+:_- only.', unique=True, max_length=255, verbose_name='oauth key', validators=[django.core.validators.RegexValidator(b'^[\\w.@+:-]+$', 'Enter a valid oauth key.', b'invalid')])),
                ('oauth_secret', models.CharField(help_text='Required. 255 characters or fewer. Letters, digits, spaces and .+:_- only.', unique=True, max_length=255, verbose_name='oauth secret', validators=[django.core.validators.RegexValidator(b'^[\\w\\s.@+:-]+$', 'Enter a valid oauth secret.', b'invalid')])),
                ('_persist_params', models.TextField(default=None, help_text='List of parameters sent by the LTI producer to this application, which should be preserved during authentication. Put each parameter name on a new line.', null=True, verbose_name='persistent parameters', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'auth_cohort',
            },
            bases=(models.Model,),
        ),
    ]
