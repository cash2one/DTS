#-*- coding:utf-8 -*-
import Ice
#from api import DCPDataServicePrx
from api import ESDataServiceInterfacePrx as ESPrx
from api import KV

CONF = {
    # 'Ice.Default.Locator': 'BrIceGrid/Locator:tcp -h 192.168.162.181 -p 4061:tcp -h 192.168.162.182 -p 4061',  # 测试
    'Ice.Default.Locator': 'BrIceGrid/Locator:tcp -h 192.168.23.111 -p 4061:tcp -h 192.168.23.112 -p 4061',  # 预发布:tcp -h 192.168.23.112 -p 4061
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

ID = 'ESDataServiceInterfaceV1.0.0'


class Es(object):

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
            self.proxy = ESPrx.checkedCast(base)

        except Ice.ConnectTimeoutException:
            raise RuntimeError("Ice::ConnectTimeoutException")
        if not self.proxy:
            raise RuntimeError("Invalid proxy")

    def getAddrData(self, querys):
        return self.proxy.getAddrData(querys)

    def getApplyLoanData(self, keys):
        return self.proxy.getApplyLoanData(keys)

    def getBlackListData(self, keys):
        return self.proxy.getBlackListData(keys)

    def getContactData(self, phone):
        return self.proxy.getContactData(phone)

    def getQQData(self, qq):
        return self.proxy.getQQData(qq)

    def getSubCate3Data(self, keys):
        return self.proxy.getSubCate3Data(keys)

    def getSubClientNewData(self, keys):
        return self.proxy.getSubClientNewData(keys)



    def destroy(self):
        if self.communicator:
            self.communicator.destroy()


if __name__ == "__main__":
    cell_md5 = KV(k="cell_md5",v="470072b34e5c7edb6543b5f78835f1ad")
    mail_md5 = KV(k="mail_md5",v="6e5dbd5fd3bebf9ff968e820c69811a0")
    id_md5  = KV(k="id_md5",v="120110198012100028") 

    l = Es()

    try:
        l.initialize()

        #print l.getQQData('599276452')
        #print l.getContactData('18638216077'),11111111

        
        print l.getAddrData([mail_md5,mail_md5])
        #,"mail_md5": "7ff53830e450202d1275ff323d8ee7e8", "cell_md5": "470072b34e5c7edb6543b5f78835f1ad"}])
    except:
        raise
    finally:
        l.destroy()
