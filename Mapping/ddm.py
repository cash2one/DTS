# -*- coding: utf-8 -*-

"""
100credit--电话虫Ice接口
"""

import json
import Ice
from phone import PhoneServicePrx


CONF = {
    'Ice.Default.Locator': 'BrIceGrid/Locator:tcp -h 192.168.21.54 -p 4061:tcp -h 192.168.21.55 -p 4061',  # 测试
    # 'Ice.Default.Locator': 'BrIceGrid/Locator:tcp -h m21p54 -p 4061:tcp -h m21p55 -p 4061',  # 正式
    # 'Ice.Default.EncodingVersion': '1.0',  # 如果ice版本>=3.5应该加上这条,否则报编码错误
    # 'Ice.ThreadPool.Client.Size': '4',
    # 'Ice.ThreadPool.Client.SizeMax': '256',
    # 'Ice.ThreadPool.Client.StackSize': '65536',
    'Ice.MessageSizeMax': '65536',
    # 'Ice.Override.Timeout': '10000',
    # 'Ice.Override.ConnectTimeout': '10000',
    # 'Ice.RetryIntervals': '-1',
    # 'Ice.Trace.Network': '2',
}

ID = 'PhoneServiceV1.0.0'

PRIORITY = range(10)  # 电话虫的优先级范围 0->9


class DDM(object):

    """ PhoneService """

    def __init__(self):
        self.initializationData = Ice.InitializationData()
        self.initializationData.properties = Ice.createProperties()
        for k, v in CONF.items():
            self.initializationData.properties.setProperty(k, v)
        self.communicator = None
        self.proxy = None

    def initialize(self):
        self.communicator = Ice.initialize(self.initializationData)
        try:
            # 创建一个代理, 询问服务器是不是设定接口的代理, 是->proxy, 不是->none
            self.proxy = PhoneServicePrx.checkedCast(self.communicator.stringToProxy(ID))
        except Ice.ConnectTimeoutException:
            raise RuntimeError("Ice::ConnectTimeoutException")
        if not self.proxy:
            raise RuntimeError("Ice::Invalid proxy")

    def upload_phone_number(self, priority, strategy, phone_number, project_name):
        """
        :param strategy 暂无 先默认个'0'
        """
        return self.proxy.uploadPhoneNumber(priority, strategy, phone_number, project_name)

    def download_result(self, task_id, mode, project_name):
        return self.proxy.downloadResult(task_id, mode, project_name)

    def destroy(self):
        if self.communicator:
            self.communicator.destroy()


def upload_phone_number(priority, phone_number):
    """给电话虫添加任务(上传电话号码)

    Usage::
        >>> from ddm import upload_phone_number
        >>> upload_phone_number(1, ['13834567890', '13612345789'])

    :param priority: 优先级 0->9
    :param phone_number: 电话号码 字符串列表
    :rtype: dict
    结果示例:
    {
        "code": 1,
        "message": "成功",
        "data": {
            "taskId": 39296,
            "phoneUploadFail": ["19963994625", "19901060973"]  # 不符合格式的电话号码
        }
    }
    """
    if int(priority) not in PRIORITY:
        raise ValueError('priority: 0 -> 9')
    ddm = DDM()
    try:
        ddm.initialize()
    except RuntimeError:
        return
    ret = ddm.upload_phone_number(str(priority), '0', json.dumps(phone_number), 'DTS')
    ddm.destroy()
    return json.loads(ret)


def download_result(task_id, mode='1'):
    """下载结果

    Usage::
        >>> from ddm import download_result
        >>> download_result('10000000')

    :param task_id: 任务id
    :param mode: 模式  1: 正常返回结果 -- 任务结束返回结果, 不结束返回任务进度;
                      2: 强制返回结果 -- 无论任务是否结束均返回结果, 未识别的电话号将归入可打通电话;
    :rtype: dict
    参数说明:
        code
        message
        totalNum           总数
        finishNum          完成总数
        proportion         完成比例
        succPhoneList      可打通电话列表
        succTotal          可打通电话数
        failPhoneList      不可打通电话列表
        failTotal          不可打通电话数
    code含义:
        (1, "成功")
        (2, "失败")
        (3, "正在识别")
        (4, "taskId查询不到结果")
        (5, "任务状态超出范围")
        (6, "taskId与项目名不符")
        (7, "不符合电话号码格式")
        (8, "参数不可转换为int类型")
    结果示例:
    {
        "code": 1,
        "message": "成功",
        "data": {
            "totalNum": 10,
            "finishNum": 10,
            "proportion": "1",
            "succPhoneList": [
                "13932925877",
                "13031126346",
                "13621101019",
                "13693362145",
                "15101060973"
            ],
            "succTotal": 5,
            "failPhoneList": [
                "13722915606",
                "13260450140",
                "13520400966",
                "13699230498",
                "13863994625"
            ],
            "failTotal": 5
        }
    }

    {
        "code": 3,
        "message": "正在识别",
        "data": {
            "totalNum": 10,
            "finishNum": 5,
            "proportion": "0.5"
        }
    }
    """
    ddm = DDM()
    try:
        ddm.initialize()
    except RuntimeError:
        return
    ret = ddm.download_result(str(task_id), mode, 'DTS')
    ddm.destroy()
    return json.loads(ret)


if __name__ == "__main__":
    #ret = upload_phone_number('1', ['13508603580',
# '13508603580',
# '15091262661',
# '18623199393',
# '15637770777',
# '15907200008',
# '13097311818',
# '18607330836',
# '13608659421',
# '18609278999',
# '18609278999',
# '13333796444',
# '18638866677',
# '18638866677',
# '13766310955',
# '13803771035',
# '13603417333',
# '13603417333',
# '13955555303',
# '13698030009',
# '15038500880',
# '18773337373',
# '13903883884',
# '15090296665',
# '15090296665',
# '13407078129',
# '15197358931',
# '15973306197',
# '13575159488',
# '13762347902'])
    #print ret
    #print ret
    print  download_result('10000233')
    # print ret

    ddm = DDM()
    try:
        ddm.initialize()
    except:
        raise
    finally:
        ddm.destroy()
