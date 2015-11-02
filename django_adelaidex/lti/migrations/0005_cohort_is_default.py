# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_adelaidex.util.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0004_auto_20151023_1224'),
    ]

    operations = [
        migrations.AddField(
            model_name='cohort',
            name='is_default',
            field=django_adelaidex.util.fields.UniqueBooleanField(default=False, help_text='Optional. Cohort to use for non-authenticated users. Only one Cohort can be the default.'),
            preserve_default=True,
        ),
    ]
