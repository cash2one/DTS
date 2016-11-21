# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_auto_20161121_1015'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filter',
            name='api_list',
        ),
    ]
