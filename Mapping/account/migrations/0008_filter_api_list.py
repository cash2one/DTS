# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_remove_filter_api_list'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='api_list',
            field=models.TextField(help_text=b'\xe6\xa0\xbc\xe5\xbc\x8f\xef\xbc\x9a\xe5\x88\x86\xe6\x9e\x90\xe5\xb8\x88\xe8\xb4\xa6\xe6\x88\xb7:apicode1,apicode2;', max_length=65535, null=True, verbose_name=b'apicode', blank=True),
            preserve_default=True,
        ),
    ]
