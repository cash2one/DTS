# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_auto_20161121_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='ip_list',
            field=models.TextField(max_length=65535, null=True, blank=True),
        ),
    ]
