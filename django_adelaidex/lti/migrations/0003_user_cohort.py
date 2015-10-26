# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0002_cohort'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cohort',
            field=models.ForeignKey(default=None, blank=True, to='lti.Cohort', null=True),
            preserve_default=True,
        ),
    ]
