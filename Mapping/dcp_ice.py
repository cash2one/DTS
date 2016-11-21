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
# Generated from file `dcp.ice'
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

if 'DCPDataService' not in _M_api.__dict__:
    _M_api.DCPDataService = Ice.createTempClass()
    class DCPDataService(Ice.Object):
        def __init__(self):
            if Ice.getType(self) == _M_api.DCPDataService:
                raise RuntimeError('api.DCPDataService is an abstract class')

        def ice_ids(self, current=None):
            return ('::Ice::Object', '::api::DCPDataService')

        def ice_id(self, current=None):
            return '::api::DCPDataService'

        def ice_staticId():
            return '::api::DCPDataService'
        ice_staticId = staticmethod(ice_staticId)

        def neoQuery(self, idCard, cell, email, qq, weibo, depth, current=None):
            pass

        def neoQueryOriginal(self, idCard, cell, email, qq, weibo, depth, current=None):
            pass

        def findQunNumByQQNum(self, qqnum, current=None):
            pass

        def findAllPhoneByPhone(self, phone, current=None):
            pass

        def __str__(self):
            return IcePy.stringify(self, _M_api._t_DCPDataService)

        __repr__ = __str__

    _M_api.DCPDataServicePrx = Ice.createTempClass()
    class DCPDataServicePrx(Ice.ObjectPrx):

        def neoQuery(self, idCard, cell, email, qq, weibo, depth, _ctx=None):
            return _M_api.DCPDataService._op_neoQuery.invoke(self, ((idCard, cell, email, qq, weibo, depth), _ctx))

        def begin_neoQuery(self, idCard, cell, email, qq, weibo, depth, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.DCPDataService._op_neoQuery.begin(self, ((idCard, cell, email, qq, weibo, depth), _response, _ex, _sent, _ctx))

        def end_neoQuery(self, _r):
            return _M_api.DCPDataService._op_neoQuery.end(self, _r)

        def neoQueryOriginal(self, idCard, cell, email, qq, weibo, depth, _ctx=None):
            return _M_api.DCPDataService._op_neoQueryOriginal.invoke(self, ((idCard, cell, email, qq, weibo, depth), _ctx))

        def begin_neoQueryOriginal(self, idCard, cell, email, qq, weibo, depth, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.DCPDataService._op_neoQueryOriginal.begin(self, ((idCard, cell, email, qq, weibo, depth), _response, _ex, _sent, _ctx))

        def end_neoQueryOriginal(self, _r):
            return _M_api.DCPDataService._op_neoQueryOriginal.end(self, _r)

        def findQunNumByQQNum(self, qqnum, _ctx=None):
            return _M_api.DCPDataService._op_findQunNumByQQNum.invoke(self, ((qqnum, ), _ctx))

        def begin_findQunNumByQQNum(self, qqnum, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.DCPDataService._op_findQunNumByQQNum.begin(self, ((qqnum, ), _response, _ex, _sent, _ctx))

        def end_findQunNumByQQNum(self, _r):
            return _M_api.DCPDataService._op_findQunNumByQQNum.end(self, _r)

        def findAllPhoneByPhone(self, phone, _ctx=None):
            return _M_api.DCPDataService._op_findAllPhoneByPhone.invoke(self, ((phone, ), _ctx))

        def begin_findAllPhoneByPhone(self, phone, _response=None, _ex=None, _sent=None, _ctx=None):
            return _M_api.DCPDataService._op_findAllPhoneByPhone.begin(self, ((phone, ), _response, _ex, _sent, _ctx))

        def end_findAllPhoneByPhone(self, _r):
            return _M_api.DCPDataService._op_findAllPhoneByPhone.end(self, _r)

        def checkedCast(proxy, facetOrCtx=None, _ctx=None):
            return _M_api.DCPDataServicePrx.ice_checkedCast(proxy, '::api::DCPDataService', facetOrCtx, _ctx)
        checkedCast = staticmethod(checkedCast)

        def uncheckedCast(proxy, facet=None):
            return _M_api.DCPDataServicePrx.ice_uncheckedCast(proxy, facet)
        uncheckedCast = staticmethod(uncheckedCast)

        def ice_staticId():
            return '::api::DCPDataService'
        ice_staticId = staticmethod(ice_staticId)

    _M_api._t_DCPDataServicePrx = IcePy.defineProxy('::api::DCPDataService', DCPDataServicePrx)

    _M_api._t_DCPDataService = IcePy.defineClass('::api::DCPDataService', DCPDataService, -1, (), True, False, None, (), ())
    DCPDataService._ice_type = _M_api._t_DCPDataService

    DCPDataService._op_neoQuery = IcePy.Operation('neoQuery', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)), (), ((), _M_api._t_kvs, False, 0), ())
    DCPDataService._op_neoQueryOriginal = IcePy.Operation('neoQueryOriginal', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_string, False, 0), ((), IcePy._t_int, False, 0)), (), ((), _M_api._t_set, False, 0), ())
    DCPDataService._op_findQunNumByQQNum = IcePy.Operation('findQunNumByQQNum', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), IcePy._t_string, False, 0),), (), ((), _M_api._t_set, False, 0), ())
    DCPDataService._op_findAllPhoneByPhone = IcePy.Operation('findAllPhoneByPhone', Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent, False, None, (), (((), IcePy._t_string, False, 0),), (), ((), _M_api._t_set, False, 0), ())

    _M_api.DCPDataService = DCPDataService
    del DCPDataService

    _M_api.DCPDataServicePrx = DCPDataServicePrx
    del DCPDataServicePrx

# End of module api