# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import django_adelaidex.util.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lti', '0003_user_cohort'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=django_adelaidex.util.fields.NullableCharField(default=None, validators=[django.core.validators.RegexValidator(b'^[\\w.@+-]+$', 'Please enter a valid nickname.', b'invalid')], max_length=255, blank=True, help_text='255 characters or fewer. Letters, digits and @/./+/-/_ only.', null=True, verbose_name='nickname'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='user',
            unique_together=set([('first_name', 'cohort')]),
        ),
    ]
