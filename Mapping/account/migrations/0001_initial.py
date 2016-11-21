# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip_list', models.TextField(max_length=65535, null=True, blank=True)),
                ('api_list', models.TextField(max_length=65535, null=True, blank=True)),
            ],
            options={
                'verbose_name': '\u8fc7\u6ee4\u540d\u5355',
                'verbose_name_plural': '\u8fc7\u6ee4\u540d\u5355\u5217\u8868',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name=b'\xe5\x90\x8d\xe7\xa7\xb0')),
                ('is_has_new_report', models.BooleanField(default=False)),
                ('b_done_over', models.BooleanField(default=False)),
                ('b_first_modify_passwd', models.BooleanField(default=False)),
                ('mem_type', models.IntegerField(default=1, max_length=4, choices=[(1, b'Custom'), (2, b'Analysts'), (3, b'DataTrans'), (0, b'Checker'), (4, b'Single'), (5, b'Phone'), (6, b'Meal'), (7, b'Coder')])),
                ('thread_num', models.IntegerField(default=5, max_length=4)),
                ('passwd_wrong_count', models.IntegerField(default=0, max_length=4)),
                ('allow_ips', models.TextField(max_length=800, null=True, blank=True)),
                ('last_login_ip', models.CharField(max_length=20, null=True, blank=True)),
                ('block_reason', models.CharField(max_length=100, null=True, blank=True)),
                ('last_login_time', models.DateTimeField(null=True, blank=True)),
                ('email', models.CharField(max_length=100, null=True, blank=True)),
                ('out_in_member', models.IntegerField(default=1, help_text=b'\xe5\x86\x85\xe9\x83\xa8\xe4\xba\xba\xe5\x91\x98\xe4\xb8\xba1,\xe5\xa4\x96\xe9\x83\xa8\xe4\xba\xba\xe5\x91\x98\xe4\xb8\xba0', max_length=4)),
                ('permission', models.TextField(default=b'null', help_text=b'\xe6\x8e\xa5\xe5\x8f\xa3\xe8\xaf\xb7\xe6\xb1\x82\xe5\x90\x8d\xe7\xa7\xb0\xef\xbc\x9a1\xe4\xb8\xba\xe5\xbc\x80\xe9\x80\x9a', max_length=800, verbose_name=b'\xe6\x8e\xa5\xe5\x8f\xa3\xe6\x9d\x83\xe9\x99\x90')),
                ('permission2', models.CharField(default=b'0000000000', help_text=b'\xe4\xbd\x9c\xe5\xba\x9f', max_length=10, verbose_name=b'\xe6\x96\xb0\xe6\x8e\xa5\xe5\x8f\xa3\xe6\x9d\x83\xe9\x99\x90')),
                ('portrait_permission', models.CharField(default=b'1000', help_text=b'\xe4\xbd\x9c\xe5\xba\x9f', max_length=10, verbose_name=b'\xe7\x94\xbb\xe5\x83\x8f\xe6\x9d\x83\xe9\x99\x90')),
                ('credit_permission', models.CharField(default=b'1000', help_text=b'\xe4\xbd\x9c\xe5\xba\x9f', max_length=10, verbose_name=b'\xe4\xbf\xa1\xe8\xb4\xb7\xe6\x9d\x83\xe9\x99\x90')),
                ('portrait3_permission', models.TextField(default=b'null', max_length=800, verbose_name=b'\xe9\x80\x9a\xe7\x94\xa8\xe7\x89\x883.0\xe6\x9d\x83\xe9\x99\x90')),
                ('credit3_permission', models.TextField(default=b'null', max_length=800, verbose_name=b'\xe4\xbf\xa1\xe8\xb4\xb73.0\xe6\x9d\x83\xe9\x99\x90')),
                ('credit3_permission2', models.CharField(default=b'000000000', help_text=b'\xe6\x9c\x88\xe5\xba\xa6\xe6\x94\xb6\xe6\x94\xaf\xe7\xad\x89\xe7\xba\xa7/\xe6\x89\x8b\xe6\x9c\xba\xe6\x9c\x89\xe6\x95\x88\xe6\x80\xa7/\xe9\x93\xb6\xe8\xa1\x8c\xe5\xae\xa2\xe7\xbe\xa4\xe8\xaf\x84\xe5\x88\x86/p2p\xe5\xae\xa2\xe7\xbe\xa4\xe8\xaf\x84\xe5\x88\x86/\xe6\xb6\x88\xe8\xb4\xb9\xe9\x87\x91\xe8\x9e\x8d\xe5\xae\xa2\xe7\xbe\xa4\xe8\xaf\x84\xe5\x88\x86', max_length=12, verbose_name=b'\xe4\xbf\xa1\xe8\xb4\xb73.0\xe6\x9d\x83\xe9\x99\x902')),
                ('custom_num', models.CharField(max_length=15, null=True, blank=True)),
                ('sampling_sort', models.IntegerField(default=1, max_length=5, verbose_name=b'\xe6\x95\xb0\xe6\x8d\xae\xe9\x9b\x86\xe5\xb8\x82\xe4\xb8\xad\xe6\x96\x87\xe4\xbb\xb6\xe4\xb8\xaa\xe6\x95\xb0')),
                ('custom_city', models.CharField(max_length=50, null=True, verbose_name=b'\xe5\xae\xa2\xe6\x88\xb7\xe6\x80\xbb\xe9\x83\xa8\xe6\x89\x80\xe5\x9c\xa8\xe5\x9f\x8e\xe5\xb8\x82', blank=True)),
                ('taskid', models.CharField(max_length=200, null=True, verbose_name=b'taskid', blank=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('analyst_custom', models.ForeignKey(related_name=b'analycus', blank=True, to='account.Member', null=True)),
                ('checker_custom', models.OneToOneField(related_name=b'checker', null=True, blank=True, to='account.Member')),
                ('datatran_custom', models.ForeignKey(related_name=b'datatrancus', blank=True, to='account.Member', null=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-id'],
                'verbose_name': '\u7cfb\u7edf\u6210\u5458',
                'verbose_name_plural': '\u7cfb\u7edf\u6210\u5458\u5217\u8868',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Queryer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('passwd', models.CharField(max_length=20)),
                ('apicode', models.CharField(max_length=20)),
                ('extra_info', models.CharField(max_length=200, null=True, blank=True)),
                ('is_busy', models.BooleanField(default=False)),
                ('do_on_file', models.CharField(max_length=100, null=True, blank=True)),
                ('start_match', models.DateTimeField(null=True, blank=True)),
                ('end_match', models.DateTimeField(null=True, blank=True)),
                ('mapping_files', models.CharField(max_length=1700, null=True, verbose_name=b'\xe8\xbf\x91\xe6\x9c\x9f\xe5\x8c\xb9\xe9\x85\x8d\xe7\x9a\x84\xe6\x96\x87\xe4\xbb\xb6\xe8\xae\xb0\xe5\xbd\x95', blank=True)),
                ('real_name', models.CharField(max_length=50, null=True, blank=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('constom', models.OneToOneField(null=True, blank=True, to='account.Member')),
            ],
            options={
                'ordering': ['-id'],
                'verbose_name': '\u753b\u50cf\u67e5\u8be2\u5e10\u53f7',
                'verbose_name_plural': '\u753b\u50cf\u67e5\u8be2\u5e10\u53f7\u5217\u8868',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='member',
            unique_together=set([('email', 'mem_type')]),
        ),
    ]
