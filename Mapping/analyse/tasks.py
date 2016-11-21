#!/usr/bin/python
# -*- coding:utf-8 -*-
import django
django.setup()
import time
import logging
from celery.task import task
import analy, mapping

errlog = logging.getLogger('daserr')


@task()
def for_ice(file, member, select, ip, username, modal):
    start = mapping.BaseMapping(file, member, select, ip, username, modal)
    result = start.match()
    return result


@task()
def for_hx(srcfile, member, select, ip, username, modal):
    result = mapping.start_mapping(srcfile, member, select, ip, username, modal)
    return result


@task()
def wait(srcfile_id, member_id, select, ip, username, modal):
    time.sleep(60)
    analy.task_queue(srcfile_id, member_id, select, ip, username, modal)
