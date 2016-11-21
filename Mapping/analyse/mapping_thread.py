# coding=utf-8
# !/usr/bin/python

import threading
import time
import Queue
import logging
import traceback
import requests
from django.conf import settings

errlog = logging.getLogger('daserr')
q = Queue.Queue(0)

class MyThread(threading.Thread):

    def __init__(self, input, worktype):
        self._jobq = input
        self._work_type = worktype
        threading.Thread.__init__(self)

    def run(self):
        delay = 50
        count = 0
        while True:
            if self._jobq.qsize() > 0:
                while True:
                    try:
                        time.sleep(delay)
                        count = count + 1
                        url = settings.MAIL_URL
                        headers = {'content-type': 'application/json'}
                        requests.get(url)
                    except Exception, e:
                        errlog.error("in run(), 线程出错" + str(traceback.format_exc()))


def mails():
    try:
        for i in range(1):
            q.put(i) 
        for x in range(1):
            MyThread(q, x).start()
    except Exception, e:
        errlog.error("线程出错" + str(traceback.format_exc()))
