#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, time
import Ice
import dac
import traceback


CONF = {#'Ice.Default.Locator': 'BrIceGrid/Locator:tcp -h 192.168.23.111 -p 4061:tcp -h 192.168.23.112 -p 4061',  # 测试
        "Ice.Default.Locator":"DacIceGrid/Locator:tcp -h 192.168.22.58 -p 4061: default -h 192.168.22.59 -p 4061",
        #"Ice.Default.Locator":"DacIceGrid/Locator:tcp -h 192.168.22 -p 4061: default -h 192.168.23.112 -p 4061",
        'Ice.ThreadPool.Client.Size':'20',
        #'Ice.ThreadPool.Client.StackSize':'1024',
        'Ice.ThreadPool.Client.SizeMax':'100',
        'Ice.Override.ConnectTimeout':'10000',
        #'Ice.Default.InvocationTimeout':'10000',
        'Ice.RetryIntervals':'0 1000 5000',
        }
ID = 'DacServiceV1.0.0'
#ID = 'DacIceFactory:default 192.168.22.51 -p 10502'


class DataIce(object):
    """DataIce"""
    def __init__(self):
        super(DataIce, self).__init__()
        self.initializationData = Ice.InitializationData()
        self.initializationData.properties = Ice.createProperties()
        self.communicator = None
        self.dac_server = None

    def initialize(self):
        try:
            for key in CONF.keys():
                self.initializationData.properties.setProperty(key, CONF[key])
            self.communicator = Ice.initialize(self.initializationData)
            base = self.communicator.stringToProxy(ID)
            try:
                self.dac_server = dac.DacServicePrx.checkedCast(base)
            except Ice.ConnectTimeoutException:
                print traceback.format_exc()
                raise RuntimeError("Ice::ConnectTimeoutException")
            if not self.dac_server:
                raise RuntimeError("Ice::Invalid proxy")
        except Exception, e:
            print traceback.format_exc()

        return None

    def get_data(self, info):
        try:
            if info[1] in ['zdy_vuici', 'zdy_getState', 'zdy_gtll']:
                time.sleep(0.2)
            result = self.dac_server.getData(json.dumps(info[0]), info[1])
            result = result.data
        except:
            result = None
        return result

    def destroy(self):
        if self.communicator:
            self.communicator.destroy()


if __name__ == '__main__':
    dataice = DataIce()
    dataice.initialize()

    info = {'phone': '15123934043',
            'queryid':'0000000100000',
            'client_type': '100002',
            'swift_number': 'zhaoyu_091273490875940387698'}
    ret = dataice.get_data((info, 'zyhl_ydsj'))

    print ret
    dataice.destroy()

