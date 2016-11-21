# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_remove_filter_api_list'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='api_list',
            field=models.TextField(max_length=65535, null=True, blank=True),
            preserve_default=True,
        ),
    ]
