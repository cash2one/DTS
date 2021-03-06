# **********************************************************************
#
# Copyright (c) 2003-2016 ZeroC, Inc. All rights reserved.
#
# This copy of Ice is licensed to you under the terms described in the
# ICE_LICENSE file included in this distribution.
#
# **********************************************************************
#
# Ice version 3.6.2
#
# <auto-generated>
#
# Generated from file `es_data_service.ice'
#
# Warning: do not edit this file.
#
# </auto-generated>
#

import Ice, IcePy

# Start of module api
_M_api = Ice.openModule('api')
__name__ = 'api'

if 'KV' not in _M_api.__dict__:
    _M_api.KV = Ice.createTempClass()
    class KV(object):
        def __init__(self, k='', v=''):
            self.k = k
            self.v = v

        def __hash__(self):
            _h = 0
            _h = 5 * _h + Ice.getHash(self.k)
            _h = 5 * _h + Ice.getHash(self.v)
            return _h % 0x7fffffff

        def __compare(self, other):
            if other is None:
                return 1
            elif not isinstance(other, _M_api.KV):
                return NotImplemented
            else:
                if self.k is None or other.k is None:
                    if self.k != other.k:
                        return (-1 if self.k is None else 1)
                else:
                    if self.k < other.k:
                        return -1
                    elif self.k > other.k:
                        return 1
                if self.v is None or other.v is None:
                    if self.v != other.v:
                        return (-1 if self.v is None else 1)
                else:
                    if self.v < other.v:
                        return -1
                    elif self.v > other.v:
                        return 1
                return 0

        def __lt__(self, other):
            r = self.__compare(other)
            if r is NotImplemented:
                return r
            else:
                return r < 0

        def __le__(self, other):
            r = self.__compare(other)
            if r is NotImplemented:
                return r
            else:
                return r <= 0

        def __gt__(self, other):
            r = self.__compare(other)
            if r is NotImplemented:
                return r
            else:
                return r > 0

        def __ge__(self, other):
            r = self.__compare(other)
            if r is NotImplemented:
                return r
            else:
                return r >= 0

        def __eq__(self, other):
            r = self.__compare(other)
            if r is NotImplemented:
                return r
            else:
                return r == 0

        def __ne__(self, other):
            r = self.__compare(other)
            if r is NotImplemented:
                return r
            else:
                return r != 0

        def __str__(self):
            return IcePy.stringify(self, _M_api._t_KV)

        __repr__ = __str__

    _M_api._t_KV = IcePy.defineStruct('::api::KV', KV, (), (
        ('k', (), IcePy._t_string),
        ('v', (), IcePy._t_string)
    ))

    _M_api.KV = KV
    del KV

if '_t_set' not in _M_api.__dict__:
    _M_api._t_set = IcePy.defineSequence('::api::set', (), IcePy._t_string)

if '_t_kvs' not in _M_api.__dict__:
    _M_api._t_kvs = IcePy.defineSequence('::api::kvs', (), _M_api._t_KV)

if 'ESDataServiceInterface' not in _M_api.__dict__:
    _M_api.ESDataServiceInterface = Ice.createTempClass()
    class ESDataServiceInterface(Ice.Object):
        def __init__(self):
            if Ice.getType(self) == _M_api.ESDataServiceInterface:
                raise RuntimeError('api.ESDataServiceInterface is an abstract class')

        def ice_ids(self, current=None):
            return ('::Ice::Object', '::api::ESDataServiceInterface')

        def ice_id(self, current=None):
            return '::api::ESDataServiceInterface'

        def ice_staticId():
            return '::api::ESDataServiceInterface'
        ice_staticId = staticmethod(ice_staticId)

        def getAddrData(self, querys, current=None):
            pass

        def getApplyLoanData(self, keys, current=None):
            pass

        def getBlackListData(self, keys, current=None):
            pass

        def getContactData(self, phone, current=None):
            pass

        def getQQData(self, qq, current=None):
            pass

        def getSubCate3Data(self, keys, current=None):
            pass

        def getSubClientNewData(self, keys, current=None):
            pass

        def __str__(self):
            return IcePy.stringify(self, _M_api._t_ESDataServiceInterface)

        __repr__ = __str__

    _M_api.ESDataServiceInterfacePrx = Ice.createTempClass()
    class ESDataServiceInterfacePrx(Ice.ObjectPrx):

        def getAddrData(self, querys, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getAddrData.invoke(self, ((querys, ), _ctx))

        def begin_getAddrData(self, querys, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getAddrData.begin(self, ((querys, ), _response, _ex, _sent, _ctx))

        def end_getAddrData(self, _r):
            return _M_api.ESDataServiceInterface._op_getAddrData.end(self, _r)

        def getApplyLoanData(self, keys, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getApplyLoanData.invoke(self, ((keys, ), _ctx))

        def begin_getApplyLoanData(self, keys, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getApplyLoanData.begin(self, ((keys, ), _response, _ex, _sent, _ctx))

        def end_getApplyLoanData(self, _r):
            return _M_api.ESDataServiceInterface._op_getApplyLoanData.end(self, _r)

        def getBlackListData(self, keys, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getBlackListData.invoke(self, ((keys, ), _ctx))

        def begin_getBlackListData(self, keys, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getBlackListData.begin(self, ((keys, ), _response, _ex, _sent, _ctx))

        def end_getBlackListData(self, _r):
            return _M_api.ESDataServiceInterface._op_getBlackListData.end(self, _r)

        def getContactData(self, phone, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getContactData.invoke(self, ((phone, ), _ctx))

        def begin_getContactData(self, phone, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getContactData.begin(self, ((phone, ), _response, _ex, _sent, _ctx))

        def end_getContactData(self, _r):
            return _M_api.ESDataServiceInterface._op_getContactData.end(self, _r)

        def getQQData(self, qq, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getQQData.invoke(self, ((qq, ), _ctx))

        def begin_getQQData(self, qq, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getQQData.begin(self, ((qq, ), _response, _ex, _sent, _ctx))

        def end_getQQData(self, _r):
            return _M_api.ESDataServiceInterface._op_getQQData.end(self, _r)

        def getSubCate3Data(self, keys, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getSubCate3Data.invoke(self, ((keys, ), _ctx))

        def begin_getSubCate3Data(self, keys, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getSubCate3Data.begin(self, ((keys, ), _response, _ex, _sent, _ctx))

        def end_getSubCate3Data(self, _r):
            return _M_api.ESDataServiceInterface._op_getSubCate3Data.end(self, _r)

        def getSubClientNewData(self, keys, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getSubClientNewData.invoke(self, ((keys, ), _ctx))

        def begin_getSubClientNewData(self, keys, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.ESDataServiceInterface._op_getSubClientNewData.begin(self, ((keys, ), _response, _ex, _sent, _ctx))

        def end_getSubClientNewData(self, _r):
            return _M_api.ESDataServiceInterface._op_getSubClientNewData.end(self, _r)

        def checkedCast(proxy, facetOrCtx=None, _ctx=None):
            return _M_api.ESDataServiceInterfacePrx.ice_checkedCast(proxy, '::api::ESDataServiceInterface', facetOrCtx, _ctx)
        checkedCast = staticmethod(checkedCast)

        def uncheckedCast(proxy, facet=None):
            return _M_api.ESDataServiceInterfacePrx.ice_uncheckedCast(proxy, facet)
        uncheckedCast = staticmethod(uncheckedCast)

        def ice_staticId():
            return '::api::ESDataServiceInterface'
        ice_staticId = staticmethod(ice_staticId)

    _M_api._t_ESDataServiceInterfacePrx = IcePy.defineProxy('::api::ESDataServiceInterface', ESDataServiceInterfacePrx)

    _M_api._t_ESDataServiceInterface = IcePy.defineClass('::api::ESDataServiceInterface', ESDataServiceInterface, -1, (), True, False, None, (), ())
    ESDataServiceInterface._ice_type = _M_api._t_ESDataServiceInterface

    ESDataServiceInterface._op_getAddrData = IcePy.Operation('getAddrData', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), _M_api._t_kvs, False, 0),), (), ((), _M_api._t_set, False, 0), ())
    ESDataServiceInterface._op_getApplyLoanData = IcePy.Operation('getApplyLoanData', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), _M_api._t_set, False, 0),), (), ((), _M_api._t_set, False, 0), ())
    ESDataServiceInterface._op_getBlackListData = IcePy.Operation('getBlackListData', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), _M_api._t_set, False, 0),), (), ((), _M_api._t_set, False, 0), ())
    ESDataServiceInterface._op_getContactData = IcePy.Operation('getContactData', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), IcePy._t_string, False, 0),), (), ((), _M_api._t_set, False, 0), ())
    ESDataServiceInterface._op_getQQData = IcePy.Operation('getQQData', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), IcePy._t_string, False, 0),), (), ((), _M_api._t_set, False, 0), ())
    ESDataServiceInterface._op_getSubCate3Data = IcePy.Operation('getSubCate3Data', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), _M_api._t_set, False, 0),), (), ((), _M_api._t_set, False, 0), ())
    ESDataServiceInterface._op_getSubClientNewData = IcePy.Operation('getSubClientNewData', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), _M_api._t_set, False, 0),), (), ((), _M_api._t_set, False, 0), ())

    _M_api.ESDataServiceInterface = ESDataServiceInterface
    del ESDataServiceInterface

    _M_api.ESDataServiceInterfacePrx = ESDataServiceInterfacePrx
    del ESDataServiceInterfacePrx

# End of module api
