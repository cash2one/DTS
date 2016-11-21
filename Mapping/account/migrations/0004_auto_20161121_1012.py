# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_filter_api_list'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='ip_list',
            field=models.TextField(max_length=10000, null=True, blank=True),
        ),
    ]
