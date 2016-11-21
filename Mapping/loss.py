# -*- coding: utf-8 -*-

import Ice
from api import DCPDataServicePrx
from functools import partial



CONF = {
    # 'Ice.Default.Locator': 'BrIceGrid/Locator:tcp -h 192.168.162.181 -p 4061:tcp -h 192.168.162.182 -p 4061',  # 测试
    'Ice.Default.Locator': 'BrIceGrid/Locator:tcp -h 192.168.23.111 -p 4061:tcp -h 192.168.23.112 -p 4061',  # 预发布
    # 'Ice.Default.EncodingVersion': '1.0',  # 如果ice版本>=3.5应该加上这条, 否则报编码错误
    # 'Ice.ThreadPool.Client.Size': '4',
    # 'Ice.ThreadPool.Client.SizeMax': '1000',
    # 'Ice.ThreadPool.Client.StackSize': '65535',
    # 'Ice.MessageSizeMax': '2048',
    # 'Ice.Override.Timeout': '10000',
    # 'Ice.Override.ConnectTimeout': '1000',
    # 'Ice.RetryIntervals': '-1',
    # 'Ice.Trace.Network': '2',
}

ID = 'DCPDataServiceV1.0.0'


class Loss(object):

    def __init__(self):
        props = Ice.createProperties()
        for k, v in CONF.items():
            props.setProperty(k, v)
        init_data = Ice.InitializationData()
        init_data.properties = props
        self.communicator = Ice.initialize(init_data)
        self.proxy = None

    def initialize(self):
        base = self.communicator.stringToProxy(ID)
        try:
            # 创建一个代理, 询问服务器是不是设定接口的代理, 是->proxy, 不是->none
            self.proxy = DCPDataServicePrx.checkedCast(base)

        except Ice.ConnectTimeoutException:
            raise RuntimeError("Ice::ConnectTimeoutException")
        if not self.proxy:
            raise RuntimeError("Invalid proxy")

    def neoQuery(self, idCard, cell, email, qq, weibo, depth):
        return self.proxy.neoQuery(idCard, cell, email, qq, weibo, depth)

    def neoQueryOriginal(self ,idCard, cell, email, qq, weibo, depth):
        return self.proxy.neoQueryOriginal(idCard, cell, email, qq, weibo, depth)


    def findQunNumByQQNum(self, qqnum):
        return self.proxy.findQunNumByQQNum(qqnum)

    def findAllPhoneByPhone(self, phone):
        return self.proxy.findAllPhoneByPhone(phone)



    def destroy(self):
        if self.communicator:
            self.communicator.destroy()


if __name__ == "__main__":
    l = Loss()
    try:
        l.initialize()
        print l.findQunNumByQQNum('599276452')
        print l.findAllPhoneByPhone('13920966518')
        
        #print l.neoQueryOriginal('120110198012100028', '13920966518', None,None, None,5)
        result = l.neoQuery('450121198209266641', '', None, None, None, 5)
        print result

    except:
        raise
    finally:
        l.destroy()
