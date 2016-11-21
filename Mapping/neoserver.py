# -*- coding: utf-8 -*-

import Ice
from neo import NeoServicePrx
import json



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

ID = 'NeoServiceV1.0.0'


class Neo(object):

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
            self.proxy = NeoServicePrx.checkedCast(base)

        except Ice.ConnectTimeoutException:
            raise RuntimeError("Ice::ConnectTimeoutException")
        if not self.proxy:
            raise RuntimeError("Invalid proxy")

    def searchRelationship(self,jsonString, appKey):
    	return self.proxy.searchRelationship(jsonString, appKey)

    def searchNodes(self,jsonString, appKey):
    	return self.proxy.searchNodes(jsonString, appKey)


    def destroy(self):
        if self.communicator:
            self.communicator.destroy()


if __name__ == "__main__":
    l = Neo()
    dic = {
		    "max_depth": "3",
		    "max_count": "10",
		    "cur_date": "0",         
		    "neo_cluster": "nc1",   
		    "cache_status": "1",    
		    "match": {
		        "cell": [
		            "" 
		        ],
		        "id": [
		            "110226198309260529" 
		        ],
		        "mail": [
		            "" 
		        ],
				"qq": [
					""
				]
		    }
	    }
    jsonString = json.dumps(dic)
    appKey = 'S1007'


    try:
        l.initialize()
        #print l.searchRelationship(jsonString,appKey)
        res = l.searchNodes(jsonString,appKey)
        print res
    #     print type(res.data)           #str
    #     r = json.loads(res.data)         #list
    #     print r                #list
    #     id_num = ''
    #     mail = ''
    #     qq = ''
    #     cell = ''
    #     weibo =''
    #     for i in r:
    #     	d = json.loads(i)           #dict
    #     	for key in d['list']:
				# if key.startswith('id'):
				#     id_num = id_num + key.split('->')[1] + ','
				# if key.startswith('mail'):
				#     mail = mail + key.split('->')[1] + ','
				# if key.startswith('cell'):
				#     cell = cell + key.split('->')[1] + ','
				# if key.startswith('qq'):
				#     qq = qq + key.split('->')[1] + ','
				# if key.startswith('weibo'):
				#     weibo = weibo + key.split('->')[1]
    #     print id_num,'id_num'
    #     print mail,'mail'
    #     print qq,'qq'
    #     print cell,'cell'
    #     print weibo

    except:
        raise
    finally:
        l.destroy()
