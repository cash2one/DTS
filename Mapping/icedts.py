#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json, csv, datetime
from multiprocessing.dummy import Pool as ThreadPool
import sys
import time 
import logging
import traceback
import random
import re
import copy
import csv
from analyse import util
from account.models import Queryer
from analyse.models import Interface
reload(sys)
sys.setdefaultencoding('utf-8')
from ice import DataIce
from loss import Loss
# from functools import partial
import hashlib
from api import KV
from es import Es
from neoserver import Neo



# 原文件中必须要包含这些字段，才能完成查询
HEADER_REL = {
    'fy_ydcmoi': ('cell', ),
    'fy_ydms': ('cell', ),
    'fy_ydcmci': ('cell', ),
    "xxx001": ('cell', ),
    "zdy_gtll": ('cell', ),
    "zdy_getState": ('cell', ),
    "zdy_vuici": ('name','id','cell'),
    "blxxb": ('name', 'id'),
    "zcx_sxzx" : ('biz_name', 'name', 'id', 'other_var5'),
    'dn_ftl':('cell',),
    'dn_tl':('cell',),
    'dn_tb':('cell',),
    'dn_state':('cell',),
    'dn_balance':('cell',),
    'dn_mcip':('cell',),
    "szdj" : ('cell',),
    "fy_dxyz" : ('name','id','cell'),
    "fy_ltyz" : ('name', 'id', 'cell'),
    "fy_ydyz" : ('name', 'id', 'cell'),
    "xlxxcx" : ('id', 'name'),
    "ld" : ('cell',),
    "idnph" : ('id', 'name'),
    "clwz" : ('driver_number', 'car_code', 'vehicle_id'),
    "dwtz" : ("id",),
    "qytz" : ('biz_name',),
    "qyjb" : ('biz_name',),
    #"idjy" : ('id', 'name'),
    "dd" : ('other_var5',), 
    "bcjq" : ('id', 'cell', 'name'),                 
    "ltst|ltid|dxst|dxid" : ('cell', 'id', 'name'),    
    "bchx" : ('name','other_var5'),
    "shbcty" : ('bank_card1', 'bank_card2'),
    "shbc" : ('bank_card1', 'bank_card2'),
    "jz" : ('id',),
    "ldzh" : ('cell',),
    "mmd" : ('id', 'name'),
    "zskj_idjy": ('id', 'name'),
    "hjkj_bcjq": ('id', 'name' ,'other_var5', 'bank_card1'),
    "qcc_qydwtz": ('biz_name',),
    "qcc_qydwtztp": ('other_var5',),
    "qcc_qyygdgxtztp": ('other_var5',),
    "qcc_qyszgxzpcx": ('other_var5',),
    "qcc_dwtz": ('id',),
    "lw_clztcx": ('id', 'vehicle_id', 'type_vehicle_id'),
    "lw_cphsfzyz": ('id', 'vehicle_id', 'type_vehicle_id'),
    "zhx_hvvkjzpf": ('id',),
    "zhx_hvgcfxbq": ('id',),
    "zhx_hvgjfxbq": ('passport_number',),
    "ylzc_zfxfxwph": ('bank_card1', 'apply_date'),
    "xb_shsb": ('name', 'id'),
    "hjxxcx": ('name', 'id'),
    "rjh_ltsz": ('cell',),
    "sy_sfztwo": ('name', 'id'),
    "qcc_qygjzmhcx": ('other_var5',),
    'xz_sjzwzt': ('cell',),
    'xz_sjzwsc': ('cell',),
    'xz_sjsys': ('cell', 'id', 'name'),
    'blxxd': ('id', 'name'),
    "zyhl_ydsj1": ('cell',),
    "zyhl_ydsj2": ('cell',),
    "zyhl_ydsj3": ('cell',),
    "fy_mbtwo": ('cell', 'name'),
}

HEADER_TRAN = {
    "zcx_sxzx" : {'cid': 'id', 'name': 'name'},
    "jz" : {'pid':'idNo'},
    "ldzh" : {'cell':'mobiles', 'user_date':'querymonth'},
    "mmd" : {'id':'idNo','cell':'mobile', 'mail':'email'},
}

errlog = logging.getLogger('daserr')

JZD_HEAD = {'TNum': 'at_num_', 'FNum':  'at_first_', 'BNum': 'at_business_', 'YNum': 'at_economy_', 'DNum': 'at_dom_', 'ArrMostCity': 'at_arr_cty_'}

#支付画像接口
BCHX_INDEX = {'S0534': 'pf_pos_m12_paylist', 'S0537': 'pf_pos_m12_numlist', 'S0574': 'pf_m3_pay_citylist', 'S0575': 'pf_m3_num_citylist', 'S0334': 'pf_bank_m6_tran_num', 'S0331': 'pf_bank_m6_tran_amt', 'S0684': 'pf_bank_m6_in_amt', 'S0685': 'pf_bank_m6_in_num', 'S0630': 'pf_bank_m12_cash_amtlist', 'S0631': 'pf_bank_m12_cash_numlist', 'S0337': 'pf_bank_m6_bigtran_amt', 'S0340': 'pf_bank_m6_bigtran_num', 'S0343': 'pf_bank_m6_midtran_amt', 'S0346': 'pf_bank_m6_midtran_num', 'S0307': 'pf_bank_m6_bigin_amt', 'S0313': 'pf_m6_tran_bigin_pct', 'S0316': 'pf_m6_cash_bigin_pct', 'S0319': 'pf_m6_pos_bigin_pct', 'S0571': 'pf_pos_m12_top5amt_list', 'S0013': 'pf_m12_bigamt_bizlist', 'S0647': 'pf_m12_mcc_paylist', 'S0649': 'pf_m12_mcc_numlist', 'S0682': 'pf_m12_echannel_list', 'validate': 'flag_pf', 'active': 'pf_cardactive'}


def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def list_get(lst, index, default=None):
    if -len(lst) <= index < len(lst) : return lst[index]
    else:return default


class FileReader(object):
    """reader for src_file"""
    def __init__(self, filepath, header, fields_src, startline=1, port_type = 'ld'):#port=select
        super(FileReader, self).__init__()
        self.filepath = filepath
        self.header = header  # 接口必须包含的字段
        self.fields = None  # 文件中的原始字段名列表
        self.fields_rel = None  # 针对相应接口翻译后的字段名列表
        self.fields_src = fields_src  # 标注的字段
        self.startline = int(startline)  # 起始行
        self.port_type = port_type

    def exist(self):
        return  os.path.exists(self.filepath)

    def detect_filetype(self):
        ext = os.path.splitext(self.filepath)
        return ext[1]

    def checkfields(self, splitor=','):
        '''检查标注的字段是否包含了必须的字段'''
        line = self.fields_src
        line = line.strip()
        line = line.split(splitor)
        ok = False not in [i in line for i in self.header]
        if self.port_type in ('bcjq', 'bchx') and ok == True:
            if 'bank_card1' in line or 'bank_card2' in line:
                ok = True
        if self.port_type == 'shbc' or self.port_type == 'shbcty':
            if 'bank_card1' in line or 'bank_card2' in line:
                ok = True
        elif self.port_type == 'jz':
            if 'id_num' in line:
                ok = True
        elif self.port_type == 'qyjb':
            if 'reg_num' in line or 'biz_name' in line or 'org_num' in line:
                ok = True
        elif self.port_type == 'qytz':
            if 'reg_num' in line or 'biz_name' in line:
                ok = True
        if ok:
            self.fields = line
        return ok

    def check_line(self):
        '''检查文件是否有空行或干脆没有数据行'''
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
        if len(lines) <= self.startline:
            return False
        for idx, line in enumerate(lines[self.startline:]):
            line = line.strip()
            if line == '':
                return False, '源文件错误，请删掉第%d行的空行' % (idx+self.startline+1)
        return True

    def translate(self, rel, fields):
        # '''将文件中标注的字段名改成与接口对应的字段名'''
        if fields:
            rel_keys = rel.keys()
            fields_rel = [rel[i] if i in rel_keys else i for i in fields]
        return fields_rel

    def read_user_data(self, fields, splitor=','):    #增加fields参数
        '''
        将文件中的每行数据读出，用splitor分割成列表.
        如果列表长度和字段头的列表长度相等，说明数据没问题, 加入输出列表
        '''
        _, ext = os.path.splitext(self.filepath)
        if ext == '.xls' or ext == '.xlsx':
            lines = util.iter_xls(self.filepath)
            lines.next()
        else:
            with open(self.filepath, 'r') as f:
                lines = f.readlines()
            lines = lines[self.startline:]
        fields_length = len(fields)
        user_data = []
        for line in lines:
            line = line.strip()
            line = line.split(splitor)
            if len(line) < fields_length:
                for i in range(fields_length-len(line)):
                    line.append('')
            user_data.append(line)
        return user_data

    def tansform_user_data(self, user_data, fields, fields_rel):
        '''将列表构建成和字段对应的字典'''
        dict_list = []
        if 'user_date' not in fields:
            fields.append('user_date')
            fields_rel.append('querymonth')
        for data in user_data:
            dt = dict({'mobiles':'', 'querymonth':''})
            for idx, field in enumerate(fields_rel):
                dt[field] = list_get(data, idx, default='')
            if dt['querymonth'] == '':
                dt['querymonth'] = datetime.datetime.now().strftime('%Y-%m')
            dict_list.append(dt)
        return dict_list

    def tansform_user_data_mmd(self, user_data, fields, fields_rel):
        '''将列表构建成和字段对应的字典'''
        dict_list = []
        for data in user_data:
            dt = dict({'idNo':'', 'name':''})
            for idx, field in enumerate(fields_rel):
                dt[field] = list_get(data, idx, default='')
            dict_list.append(dt)
        return dict_list

class IceLD(object):
    '''账户变动的ice接口'''
    def __init__(self, filereader, apicode):
        super(IceLD, self).__init__()
        self.filereader = filereader
        self.dataice = None
        self.user_dict_list = None
        self.apicode = apicode

    def ice_init(self):
        self.dataice = DataIce()
        try:
            self.dataice.initialize()
        except Exception, e:
            errlog.error('ice error is :'+traceback.format_exc())
            errlog.error('in the  ice init ,there is out of runtime')
            return False
        return True

    def check_ice(self, modal, select = 'ld'):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {
            'mobiles':'13439065818',
            'count':'1',
            'querymonth':'2014-11',
            'datetime':timestamp(),
            'client_type':'100002',
            'swift_number': swift_number
        }
        ret = self.dataice.get_data((info, 'ld'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:
                ret = True
        return ret

    def destroy(self):
        self.dataice.destroy()

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number   = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            mobile = line['mobiles'].strip()
            if 'apply_date' in line.keys() and len(line['apply_date']) > 6:
                month = line['apply_date']
                month = month[:7]
                if month[4:5] != '-':
                    month = line['querymonth']
            else:
                month = line['querymonth']
            user_info = dict({'mobiles':mobile,
                              'count':'1',
                              'querymonth': month,
                              'datetime':timestamp(),
                              'client_type':'100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'ld'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()

        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt, results)
        return results, list_txt

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            outdata = [data[i] for i in fields_rel]
            ret_list.append([openid] + outdata + results[idx])
        return ret_list

    @staticmethod
    def transforms(datas):
        results = []
        for data in datas:
            result = IceLD.transform(data)
            results.append(result)
        return results

    @staticmethod
    def transform(data):
        if data == None:
            return DEFAULT_LD
        if data['retcode'] != '0000':
            return DEFAULT_LD
        if 'resultinfo' not in data.keys():
            return DEFAULT_LD
        result_data = data['resultinfo']
        result_data_keys = set(result_data.keys())
        return [result_data[i] if i in result_data_keys else '' for i in SRC_FIELD_LIST]

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results = IceLD.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields + AC_FIELD_LIST
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename, 'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        writer = csv.writer(f,delimiter=',')
        writer.writerow(headers)
        for line in lines:
            if crypt:
                if 'id' in headers:
                    index = headers.index('id')
                    if line[index]:
                        try:
                            line[index] = line[index][:-4] + '##' + line[index][-2] + '#'
                        except:line[index] = ''
                if 'name' in headers:
                    index = headers.index('name')
                    line[index] = '####'
                if 'cell' in headers:
                    index = headers.index('cell')
                    if line[index]:
                        line[index] = line[index][:-4]+'####'
                if 'ac_mobile_id' in headers:
                    index = headers.index('ac_mobile_id')
                    if line[index]:
                        line[index] = line[index][:-4]+'####'
                if 'bank_card2' in headers:
                    index = headers.index('bank_card2')
                    if line[index] and len(line[index]) > 12:
                        line[index] = line[index][:12] + '#'*(len(line[index][12:]) - 1) + line[index][-1:]
                if 'bank_card1' in headers:
                    index = headers.index('bank_card1')
                    if line[index] and len(line[index]) > 12:
                        line[index] = line[index][:12] + '#'*(len(line[index][12:]) - 1) + line[index][-1:]
                if 'email' in headers:
                    index = headers.index('email')
                    if line[index]:
                        pos = line[index].find('@')
                        if pos >= 0:
                            line[index] = '####' + line[index][pos:]
            writer.writerow(line)
        f.close()

    def write_to_txt(self, filename, headers, list_txt, crypt=False):
        f = open(filename, 'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        for line in list_txt:
            line_new = json.loads(line[0][0])
            try:
                if crypt:
                    if 'id' in line_new:
                        if line_new['id']:
                            line_new['id'] = line_new['id'][:-4]+'##'+line_new['id'][-2]+'#'
                    if 'name' in line_new:
                        line_new['name'] = '####'
                    if 'cell' in line_new:
                        if line_new['cell']:
                            line_new['cell'] = line_new['cell'][:-4] + '####'
                    if 'mobiles' in line_new:
                        if line_new['mobiles']:
                            line_new['mobiles'] = line_new['mobiles'][:-4] + '####'
                    if 'mobile' in line_new:
                        if line_new['mobile']:
                            line_new['mobile'] = line_new['mobile'][:-4] + '####'
                    if 'bank_card2' in line_new:
                        if line_new['bank_card2'] and len(line_new['bank_card2']) > 12:
                            line_new['bank_card2'] = line_new['bank_card2'][:12] + '#'*(len(line_new['bank_card2'][12:]) -1) + line_new['bank_card2'][-1:]
                    if 'bank_card1' in line_new:
                        if line_new['bank_card1'] and len(line_new.get('bank_card1')) > 12:
                            line_new['bank_card1'] = line_new['bank_card1'][:12] + '#'*(len(line_new['bank_card1'][12:]) -1) + line_new['bank_card1'][-1:]
                    if 'email' in line_new:
                        if line_new['email']:
                            pos = line_new['email'].find('@')
                            if pos >= 0:
                                line_new['email'] = '####' + line_new['email'][pos:]  
            except Exception, e:
                errlog.error(traceback.format_exc())
            f.write(json.dumps(line_new, ensure_ascii=False)+'\t\t')
            f.write(line[0][1]+'\t\t')
            f.write(json.dumps(line[1], ensure_ascii=False)+'\n')
        f.close()

class IceLD2(IceLD):
    '''new账户变动的ice接口'''
    def __init__(self, *args):
        super(IceLD2, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') +  "_" + str(random.randint(1000,9999))
        info = {'mobileid':'13439065818',
            'querymonth':'201507',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        now = time.strftime('%Y%m')
        error_date = [now+'01', now+'02', now+'03', now+'04', now+'05']
        for line in user_dict_list:
            if 'apply_date' in line.keys() and len(line['apply_date']) == 10:
                apply_date = line['apply_date'].strip().split('-')
                date = ''.join(apply_date)
            else:
                date = time.strftime('%Y%m%d')
            if date in error_date:
                date = date[:5] + str(int(date[5])-1) + date[6:]
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            mobile = line['mobiles'].strip()
            user_info = dict({'mobileid':mobile,
                              'querymonth':date,
                              'client_type':'100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        if len(info_list) >= 8500:
            info_times = len(info_list)/8500 + 1
            results_json = []
            for x in range(info_times):
                time.sleep(59)
                start = 8500 * x
                end = start + 8500
                send_info = info_list[start:end]
                pool = ThreadPool(20)
                result_json = pool.map(self.dataice.get_data, send_info)
                pool.close()
                pool.join()
                for item in result_json:
                    results_json.append(item)
        else:
            interface = Interface.objects.get(name=select)
            thread_num = interface.thread_num
            pool = ThreadPool(thread_num)
            results_json = pool.map(self.dataice.get_data, info_list)
            pool.close()
            pool.join()

        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, select):
        results = []
        ld_heads = NEW_LD_LIST
        for idx, data in enumerate(datas):
            result, ld_head = IceLD2.transform(data, select)

            if ld_head == LD_LIST_NEW:
                ld_heads = LD_LIST_NEW
            results.append(result)
        return results, ld_heads

    @staticmethod
    def transform(data, select):
        results = []
        orl_results = {}
        ld_heads = NEW_LD_LIST
        if select == 'ldtj':
            result_key = ['br_mobile_once', 'br_v1_mobile_6m', 'br_v1_mobile_18m', 'br_mobile_auth']
        elif select == 'ldv2':
            result_key = ['br_mobile_once', 'br_v2_mobile_6m', 'br_v2_mobile_18m', 'br_mobile_auth']
        else:
            result_key = ['br_mobile_once', 'br_mobile_6m', 'br_mobile_18m', 'br_mobile_auth']
        if not isinstance(data, dict):
            return DEFAULT_LD2, ld_heads
        if data["retcode"] != '0000' or data == None:
            results.append('0')
        else:
            results.append('1')
        for key in result_key:
            if key == 'br_mobile_once':             
                if 'br_mobile_once' in data.keys(): # 浦发 建行 招行 中行 工行 兴业 平安 招行信用卡 交行
                    data_once = data['br_mobile_once'][0]
                    data_once = data_once.split(',')
                    results.append(data_once[1])
                    card_times = data_once[0]
                    for x in range(len(card_times)):
                        results.append(card_times[x])
                    results.append(data_once[2])
                else:
                    for x in range(11):
                        results.append('')
            elif key in ('br_mobile_6m', 'br_v1_mobile_6m', 'br_v2_mobile_6m'):
                range_num = 11
                if 'br_mobile_6m' in data.keys():
                    result_data = data['br_mobile_6m']
                elif 'br_v1_mobile_6m' in data.keys():
                    result_data = data['br_v1_mobile_6m']
                elif 'br_v2_mobile_6m' in data.keys():
                    range_num = 17
                    ld_heads = LD_LIST_NEW
                    result_data = data['br_v2_mobile_6m']
                else:
                    for x in range(66):
                        results.append('')
                    continue                   
                for result in result_data:
                    if not isinstance(result, dict):
                        continue
                    result = result.values()
                    orl_results[result[1]] = result[0]
                if not orl_results:
                    continue
                for x in range(6):
                    x = x +1
                    if str(x) not in orl_results.keys():
                        result = ['','','','','','','','','','','']
                    else:
                        result = orl_results[str(x)]
                        result = re.split(',', result)
                    for cell in range(range_num):
                        try:
                            results.append(result[cell])
                        except Exception, e:
                            results.append('')
            elif key in ('br_mobile_18m', 'br_v1_mobile_18m', 'br_v2_mobile_18m'):
                range_num = 11
                if 'br_mobile_18m' in data.keys():
                    result_18 = data['br_mobile_18m']
                elif 'br_v1_mobile_18m' in data.keys():
                    result_18 = data['br_v1_mobile_18m']
                elif 'br_v2_mobile_18m' in data.keys():
                    range_num = 17
                    ld_heads = LD_LIST_NEW
                    result_18 = data['br_v2_mobile_18m']
                else:
                    for x in range(66):
                        results.append('')
                    continue
                orl_results_18 = {}
                for q in result_18 :
                    result = q.values()
                    orl_results_18[result[1]] = result[0]
                Q_18 = ['1', '4', '7', '10', '13', '16']
                for item in Q_18 :
                    if item in orl_results_18.keys():
                        data_one = orl_results_18[item]
                        data_one = data_one.split(',')
                        for x in range(range_num):
                            try:
                                results.append(data_one[x])
                            except Exception, e:
                                results.append('')
                    else:
                        for x in range(range_num):
                            results.append('')
            elif key == 'br_mobile_auth':            
                if 'br_mobile_auth' not  in data.keys():
                    return results, ld_heads
                data_auth = data['br_mobile_auth'][0]
                data_auth = data_auth.split(',')
                for x in [3,0,2,4,1]:
                    results.append(data_auth[x])
        return results, ld_heads

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, ld_heads = IceLD2.transforms(results, select)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields + ld_heads
        return OUT_CSV_FM_LD, results


class IceJZD(IceLD):
    '''航旅行为的ice接口'''
    def __init__(self, *args):
        super(IceJZD, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'pid':'431122198811121430',
            'passName': u'刘明宁',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'jz'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if 'apply_date' in line.keys():
                date = line['apply_date']
            else:
                date = time.strftime('%Y-%m-%d')
            if 'id' in line.keys():
                pid = line['id'].strip()
            else:
                pid = line['id_num'].strip()
            if 'name' in line.keys():
                name = line['name']
            else:
                name = ''
            user_info = dict({'pid':pid,
                                'passName': name,
                                'client_type': '100002',
                                'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt,results)

        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = ['code', 'date', 'at_arr_cty_total']
        for data in datas:
            result, header = IceJZD.transform(data)
            results.append(result)
            if header:
                header.sort(reverse=True)
                for head in header:
                    for x in head:
                        headers.append(str(x))
        headered = set(headers)
        headered = list(headered)
        try:
            headered.sort()
        except Exception, e:
            pass
        return results, headered

    @staticmethod
    def transform(data):
        results = {}
        header = []
        if not isinstance(data, dict):
            results.update({'code': 'time out'})
            return results, header
        if data["ErrorRes"]["Err_code"] != '200' or data == None:
            results.update({'code': data["ErrorRes"]["Err_code"]})
            return results, header
        else:
            results.update({'code': '200'})
        if 'detailInfo' not in data.keys():
            return results, header
        result_data = data['detailInfo']
        if result_data:
            results.update({'date': time.strftime('%Y%m')})
            if 'name' in result_data.keys() and result_data['name'] != 'liumingning':
                results.update({'at_name': result_data['name']})
            if 'ArrMostCityTotal' in result_data.keys():
                results.update({'at_arr_cty_total': result_data['ArrMostCityTotal']})
            else:
                results.update({'at_arr_cty_total': '0'})
            result_data = result_data['FlightInfo']
            if not result_data:
                return results, header
        else:
            return results, header
        for key in result_data.keys():
            if isinstance(result_data[key], list): # PSA_flightinfo
                for info in result_data[key]:
                    for item in info.keys(): # FlightDetail
                        if isinstance(info[item], dict):
                            for psa in info[item].keys(): # PSA_FlightDetail
                                if isinstance(info[item][psa], list):
                                    for data in info[item][psa]:  
                                        if isinstance(data, dict):
                                            head_ = []
                                            for head in ['TNum', 'FNum', 'BNum', 'YNum', 'DNum', 'ArrMostCity']:
                                                head = JZD_HEAD[head] + data['Quarter']
                                                head_.append(head)
                                            header.append(head_)
                                            for x in ['TNum', 'FNum', 'BNum', 'YNum', 'DNum', 'ArrMostCity']:
                                                results.update({JZD_HEAD[x] + data['Quarter']:data[x]})
                                elif isinstance(info[item][psa], dict):
                                    data = info[item][psa]
                                    head_ = []
                                    for head in ['TNum', 'FNum', 'BNum', 'YNum', 'DNum', 'ArrMostCity']:
                                        head = JZD_HEAD[head] + data['Quarter']
                                        head_.append(head)
                                    header.append(head_)
                                    for x in ['TNum', 'FNum', 'BNum', 'YNum', 'DNum', 'ArrMostCity']:
                                        results.update({JZD_HEAD[x] + data['Quarter']:data[x]})
            else:
                for item in result_data[key].keys(): # FlightDetail
                    if isinstance(result_data[key][item],dict):                    
                        for psa in result_data[key][item].keys(): # PSA_FlightDetail
                            if isinstance(result_data[key][item][psa], dict):
                                for datas in result_data[key][item].keys():
                                    if isinstance(result_data[key][item][datas], dict):
                                        data = result_data[key][item][datas]
                                        head_ = []
                                        for head in ['TNum', 'FNum', 'BNum', 'YNum', 'DNum', 'ArrMostCity']:
                                            head = JZD_HEAD[head] + data['Quarter']
                                            head_.append(head)
                                        header.append(head_)
                                        for x in ['TNum', 'FNum', 'BNum', 'YNum', 'DNum', 'ArrMostCity']:
                                            results.update({JZD_HEAD[x] + data['Quarter']:data[x]})
                            else:
                                for data in result_data[key][item][psa]:  
                                    if isinstance(data, dict):
                                        head_ = []
                                        for head in ['TNum', 'FNum', 'BNum', 'YNum', 'DNum', 'ArrMostCity']:
                                            head = JZD_HEAD[head] + data['Quarter']
                                            head_.append(head)
                                        header.append(head_)
                                        for x in ['TNum', 'FNum', 'BNum', 'YNum', 'DNum', 'ArrMostCity']:
                                            results.update({JZD_HEAD[x] + data['Quarter']:data[x]})
        return results, header

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            #outdata = [data[i] for i in self.filereader.fields_rel]
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceJZD.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields + ['at_name'] + headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('jzd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceZdy(IceJZD):
    '''dxy的ice接口'''
    def __init__(self, *args):
        super(IceZdy, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self,modal,select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'client_type': '100002',
            'swift_number': swift_number,
            'nameHash': "翟浩" ,                             
            'idNoHash': '321201199002280215',
            'mdn': '17712925582',
            }
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = copy.deepcopy(user_dict_list)
        for line in user_dict_list:
            if 'id' in line.keys():
                cardno = line['id'].strip()
            else:
                cardno = ''
            if 'name' in line.keys():
                name = line['name'].strip()
            else:
                name = ''
            mobile = line['cell'].strip()
            if mobile[:3] in ["133","153","177","180","181","189"]:
                swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
                line.update({'swift_number': swift_number})
                data_txt.append((json.dumps(line), select))
                user_info = {'nameHash':name,
                            'idNoHash': cardno, 
                            'mdn': mobile,
                            'client_type': '100002',
                            'swift_number': swift_number}
                query_info_list.append((user_info, select))
            else:
                self.user_dict_list.remove(line)
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        if len(info_list)==0:
            results = []
            list_txt = []
        else:
            interface = Interface.objects.get(name=select)
            thread_num = interface.thread_num
            pool = ThreadPool(thread_num)
            results_json = pool.map(self.dataice.get_data, info_list)
            pool.close()
            pool.join()
            results = []
            for i in results_json:
                if i!=None:
                    try:
                        result = json.loads(i)
                    except ValueError:
                        result = None
                else:result = None
                results.append(result)
            # results = [json.loads(i) if i!=None else None for i in results_json]
            list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []
        for data in datas:
            result = IceZdy.transform(data)
            results.append(result)
            headers = headers + result.keys()
        head_sort= ['code', 'status', 'message', 'time', 'value', 'idNoCheckResult', 'idTypeCheckResult', 'nameCheckResult', 'costTime', 'costTime']
        headers = list(set(headers))
        headers.sort(key = head_sort.index)
        return results, headers

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        try:
            if data and isinstance(data, dict):
                if 'data' in data.keys():
                    if data['data'][0][0] == 'value':
                        data.update({'value': data['data'][0][1]})
                        data.pop('data')
                    else:
                        for n in data['data']:
                            data.update({n[0]:n[1]})
                        data.pop('data')

                for key, value in data.items():
                    if isinstance(value, dict):
                        for result in value.keys():
                            results.update({result: value[result]})
                    else:
                        if key == 'trace':
                            continue
                        results.update({key: value})
            else:
                return {}
        except Exception, e:
            errlog.error('zdy tranform :'+traceback.format_exc())
        return results

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceZdy.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results


class IceYD(IceJZD):
    '''风影移动的ice接口'''
    def __init__(self, *args):
        super(IceYD, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self,modal,select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'client_type': '100002',
            'swift_number': swift_number,
            'mobile': '13839218138',
            }
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = copy.deepcopy(user_dict_list)
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            mobile = line['cell'].strip()
            if mobile[:3] in ["134","135","136","137","138","139","147","150","151","152","157","158","159","178","182","183","187","188","184"]:
                user_info = {'mobile': mobile,
                            'client_type': '100002',
                            'swift_number': swift_number}
                query_info_list.append((user_info, select))
                line.update({'swift_number': swift_number})
                data_txt.append((json.dumps(line), select))
            else:
                self.user_dict_list.remove(line)
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        if len(info_list) == 0:
            results = []
            list_txt = []
        else:
            interface = Interface.objects.get(name=select)
            thread_num = interface.thread_num
            pool = ThreadPool(thread_num)
            results_json = pool.map(self.dataice.get_data, info_list)
            pool.close()
            pool.join()
            results = []
            for i in results_json:
                if i!=None:
                    try:
                        result = json.loads(i)
                    except ValueError:
                        result = None
                else:result = None
                results.append(result)
            list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []
        for data in datas:
            result = IceYD.transform(data)
            results.append(result)
            headers = headers + result.keys()
        head_sort= ['code', 'status', 'result', 'msg', 'message', 'time', 'value', 'costTime', 'costTime', 'serialNo']
        headers = list(set(headers))
        headers.sort(key = head_sort.index)
        return results, headers

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        try:
            if data and isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        for result in value.keys():
                            results.update({result: value[result]})
                    else:
                        results.update({key: value})
            else:
                return {}
        except Exception, e:
            errlog.error('fy_yd tranform :'+traceback.format_exc())
        return results

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = self.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results


    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('zcx_sxzx write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceBlxxb(IceJZD):
    '''不良信息的ice接口'''
    def __init__(self, *args):
        super(IceBlxxb, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self,modal,select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'client_type': '100002',
            'swift_number': swift_number,
            'param': "廖辉才,452123197411091339" ,                             
            }
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            cardno = line['id'].strip()
            name = line['name'].strip()
            if not name:
                param = None
            elif len(cardno) != 15 and len(cardno) != 18:
                param = None
            elif not re.match('^((1[1-5])|(2[1-3])|(3[1-7])|(4[1-6])|(5[0-4])|(6[1-5])|71|(8[12])|91)\\d{4}((19\\d{2}(0[13-9]|1[012])(0[1-9]|[12]\\d|30))|(19\\d{2}(0[13578]|1[02])31)|(19\\d{2}02(0[1-9]|1\\d|2[0-8]))|(19([13579][26]|[2468][048]|0[48])0229))\\d{3}(\\d|X|x)?$', cardno) \
                    and not re.match('^[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}', cardno):
                param = None
            else:
                param = name + ',' + cardno
            user_info = {'param':param,
                        'client_type': '100002',
                        'swift_number': swift_number}
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        results = []
        for i in info_list:
            if i[0]['param']:
                i = self.dataice.get_data((i))
            else:
                i = None
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        header = []
        heads = []
        head_sort = ['caseType', 'caseSource', 'caseTime']
        for data in datas:
            result, head = IceBlxxb.transform(data)
            results.append(result)
            header = list(set(header + head))
        
        for i in range(1,100):
            list1 = []
            headed = []
            for j in header:
                if str(i) in j:
                    list1.append(j)

            for k in head_sort:
                if k+str(i) in list1:
                    headed.append(k+str(i))
            
            heads = heads + headed
        return results, heads

    @staticmethod
    def transform(data):
        results = {}
        try:
            if data and isinstance(data, dict):
                if 'costTime' in data.keys():
                    results.update({'costTime': data['costTime']})
                elif 'costTime' in data.keys():
                    results.update({'costTime': data['costTime']})
                if 'message' in data.keys() and data['message']:
                    results.update({'message_status': data['message']['status'], 'message_value': data['message']['value']})
                if 'priskChecks' in data.keys() and data['priskChecks']:
                    for one in data['priskChecks']:
                        if isinstance(one, dict):
                            results.update({'name1': one.get('@inputXm', ''), 'id1': one.get('@inputZjhm', '')})
                            if 'message' in one.keys():
                                results.update({'status': one['message'].get('status', ''), 'value': one['message'].get('value', '')})
                            for key in ['wybs', 'checkCode', 'checkMsg']:
                                if key  in one.keys():
                                    results.update({key: one[key].get('#text', '')})
                            if 'caseDetail' in one.keys() and one['caseDetail']:
                                if isinstance(one['caseDetail'], list):
                                    num = 0
                                    for every in one['caseDetail']:
                                        num = num + 1 
                                        results.update({'caseType'+str(num): every['caseType'].get('#text', ''), 'caseSource'+str(num): every['caseSource'].get('#text', ''), 'caseTime'+str(num): every['caseTime'].get('#text', '')})
                                if isinstance(one['caseDetail'], dict):
                                    results.update({'caseType1': one['caseDetail']['caseType'].get('#text', ''), 'caseSource1': one['caseDetail']['caseSource'].get('#text', ''), 'caseTime1': one['caseDetail']['caseTime'].get('#text', '')})

            elif data and isinstance(data, list):
                if isinstance(data[0], dict):
                    for key, value in data[0].items():
                        results.update({key: value})
            else:
                return {}, []
        except Exception, e:
            errlog.error('blxxb tranform :'+traceback.format_exc())
        return results, results.keys()

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceBlxxb.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  ['message_status', 'message_value', 'name1', 'id1', 'wybs', 'status', 'value', 'checkCode', 'checkMsg'] + headers + ['costTime']
        return OUT_CSV_FM_LD, results


class IceZCX(IceLD):
    '''法院执行人的ice接口'''
    def __init__(self, *args):
        super(IceZCX, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        reqTid = swift_number
        info = {'client_type': '100002',
            'swift_number': swift_number,
            'reqTid': reqTid,                             
            'name': u'郝震',
            'cid': '420107196904010056',
            'type': 1,
            }
        ret = self.dataice.get_data((info, 'zcx_sxzx'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            reqTid = swift_number
            if 'apply_date' in line.keys():
                date = line['apply_date']
            else:
                date = time.strftime('%Y-%m-%d')
            if 'other_var5' in line.keys():
                try:
                    type = int(line["other_var5"])
                except Exception, e:
                    type = 1
            else :
                type = 1
            if 'id' in line.keys():
                id = line['id'].strip()
            if type == 1:
                if 'name' in line.keys():
                    name = line['name'].strip()
                else :
                    name = ''
                user_info = {'name': name,
                            'cid': id,
                            'type': 1,
                            'reqTid': reqTid,
                            'client_type': '100002',
                            'swift_number': swift_number}
                query_info_list.append((user_info,'zcx_sxzx'))
            if type == 2:
                if 'biz_name' in line.keys():
                    name = line['biz_name']
                else:
                    name = ''
                user_info = {'name': name,
                            'type': 2,
                            'reqTid': reqTid,
                            'client_type': '100002',
                            'swift_number': swift_number}
                query_info_list.append((user_info,'zcx_sxzx'))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []
        headed_sort = ["resCode","resMsg","totalNum"]

        for data in datas:
            result, header = IceZCX.transform(data)
            results.append(result)
            if header:
                for i in header:
                    headers.append(i)

        head_sort = ["resCode","resMsg","totalNum",'name','cid','cidtype','datatime','datatype','datatypeid','leader','address','court','time','casenum','money','base','basecompany','obligation','lasttime','performance','concretesituation','breaktime','posttime','performedpart','unperformpart','statute','basic','basiccourt','data','costTime']
        headers = list(set(headers))
        for i in range(1,10):
            list1 = []
            headed = []
            for j in headers:
                if j[-1] == str(i):
                    list1.append(j)

            for k in head_sort:
                if k+str(i) in list1:
                    headed.append(k+str(i))

            headed_sort = headed_sort + headed
        headed_sort = headed_sort + ['data','costTime']
        for data in results:
            #'keys',data.keys()
            for key in data.keys():
                if key not in headed_sort:
                    data.pop(key)
        return results, headed_sort

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        if not isinstance(data, dict):
            results.update({'resCode': 'time out'})
            return results,headers
        resCode = data["resCode"]

        if resCode == '0000' :
            results.update({"resCode":data["resCode"],"resMsg":data["resMsg"],"totalNum":data["totalNum"],"costTime":data["costTime"]})
            if data["data"] == None :  
                results.update({"data":data["data"]})
            else:
                i = 1
                for line in data["data"]:
                    for num  in line["entity"]:
                        results.update({num+str(i):line["entity"][num]})
                    i = i + 1
        if resCode == "2001":
            results.update({"resCode":data["resCode"],"resMsg":data["resMsg"],"totalNum":data["totalNum"],"data":data["data"],"costTime":data["costTime"]})
        if  resCode == '1001' or resCode == '1002' or resCode == '1003' or resCode == '1013' or resCode == '9999' or resCode == '1011':
            results.update({"resCode":data["resCode"]})
        if  resCode == '1012':
            results.update({"resCode":data["resCode"],"resMsg":data["resMsg"],"totalNum":data["totalNum"],"data":data["data"],"costTime":data["costTime"]})
        for head in results.keys():
            headers.append(head)
            #headers.update({head:None})
        return results, headers

        

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceZCX.transforms(results)
        #111,results,222,headers
        results = self.linklist(results, fileid, fields_rel)
        #333,results
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('zcx_sxzx write csv wrong : '+ traceback.format_exc())
                continue
        f.close()



class IceHJ(IceLD):
    '''户籍的ice接口'''
    def __init__(self, *args):
        super(IceHJ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'client_type': '100002',
            'swift_number': swift_number,
            'identity_name': "张青" ,                             
            'identity_code': '500105199209250315',
            }
        ret = self.dataice.get_data((info, 'hjxxcx'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if 'date' in line.keys():
                date = line['apply_date'].strip()
            else:
                date = time.strftime('%Y-%m-%d')
            if 'id' in line.keys():
                identity_code = line['id'].strip()
            if 'name' in line.keys():
                identity_name = line['name'].strip()
            user_info = {'identity_name':identity_name,
                        'identity_code': identity_code, 
                        'client_type': '100002',
                        'swift_number': swift_number}
            query_info_list.append((user_info,'hjxxcx'))
            #query_info_list,'info'
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        #results,'results'
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []

        for data in datas:
            result, header = IceHJ.transform(data)
            results.append(result)
        headed_sort = ['status_code','status','identity_name','identity_code','formerName','nation','originPlace','sex','address','birthPlace','birthday','company','maritalStatus','edu']
        return results, headed_sort

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        if not isinstance(data, dict):
            results.update({'status_code': 'return error'})
            return results,headers
        if 'Error' in data.keys():
            results.update({'status_code': '参数错误'})
            return results,headers
        if not isinstance(data['api_status'], dict):
            results.update({'status_code': 'return error'})
            return results,headers
        code = data['api_status']["code"]
        status = data['api_status']['status']
        if code == '0000' :
            info = data['data']['info']
            status_code = code
            if 'identity_name' in info.keys():
                identity_name = info['identity_name']
            else:
                identity_name = ''
            if 'identity_code' in info.keys():
                identity_code = info['identity_code']
            else:
                identity_code = ''
            if 'residence' in info.keys():
                residence = info['residence']
                if 'formerName' in residence.keys():
                    formerName = residence['formerName']
                else:
                    formerName = ''
                if 'nation' in residence.keys():
                    nation = residence['nation']
                else:
                    nation = ''
                if  'originPlace' in residence.keys():
                    originPlace = residence["originPlace"]
                else:
                    originPlace = ''
                if  'sex' in residence.keys():
                    sex = residence["sex"]
                else:
                    sex = ''
                if  'address' in residence.keys():
                    address = residence["address"]
                else:
                    address = ''
                if  'birthPlace' in residence.keys():
                    birthPlace = residence["birthPlace"]
                else:
                    birthPlace = ''
                if  'birthday' in residence.keys(): 
                    birthday = residence["birthday"]
                else:
                    birthday = ''
                if  'company' in residence.keys(): 
                    company = residence["company"]
                else:
                    company = ''
                if  'maritalStatus' in residence.keys(): 
                    maritalStatus = residence["maritalStatus"]
                else:
                    maritalStatus = ''
                if  'edu' in residence.keys(): 
                    edu = residence["edu"]
                else:
                    edu = ''
            results.update({"status_code":status_code,"status":status,"identity_name": identity_name, "identity_code": identity_code, "formerName": formerName,
                "nation": nation, "originPlace": originPlace, "sex":sex, "address": address, "birthPlace": birthPlace, "birthday": birthday,
                "company": company, "maritalStatus": maritalStatus, "edu": edu})   
        if  code == "0001" or '0002' or '1000' or '1001' or '1003' or '1004' or '1005' or '2000':
            results.update({"status_code":code, "status":status})
        for head in results.keys():
            headers.append(head)
        return results, headers

        

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            #outdata = [data[i] for i in self.filereader.fields_rel]
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceHJ.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('zcx_sxzx write csv wrong : '+ traceback.format_exc())
                continue
        f.close()



class IceXL(IceLD):
    '''学历的ice接口'''
    def __init__(self, *args):
        super(IceXL, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'client_type': '100002',
            'swift_number': swift_number,
            'identity_name': "张正媛" ,                             
            'identity_code': '420111198403215022',
            }
        ret = self.dataice.get_data((info, 'xlxxcx'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if 'date' in line.keys():
                date = line['apply_date'].strip()
            else:
                date = time.strftime('%Y-%m-%d')
            if 'id' in line.keys():
                identity_code = line['id'].strip()
            if 'name' in line.keys():
                identity_name = line['name'].strip()
            user_info = {'identity_name':identity_name,
                        'identity_code': identity_code, 
                        'client_type': '100002',
                        'swift_number': swift_number}
            query_info_list.append((user_info,'xlxxcx'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt,results)
        #results,'results'
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []

        for data in datas:
            result, header = IceXL.transform(data)
            results.append(result)
            # if header:
            #     for i in header:
            #         headers.append(i)

        headed_sort = ['status_code','status','identity_name','identity_code','graduate','educationDegree','enrolDate','specialityName','graduateTime','studyResult','studyStyle','photo']
        return results, headed_sort

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        try:
            if not isinstance(data, dict):
                results.update({'status_code': 'return error'})
                return results,headers
            if 'Error' in data.keys():
                results.update({'status_code': '参数错误'})
                return results,headers
            if not isinstance(data['api_status'], dict):
                results.update({'status_code': 'return error'})
                return results,headers
            code = data['api_status']["code"]
            status = data['api_status']['status']
            if code == '0000' :
                info = data['data']['info']
                status_code = code
                if 'identity_name' in info.keys():
                    identity_name = info['identity_name']
                else:
                    identity_name = ''
                if 'identity_code' in info.keys():
                    identity_code = json.dumps(info['identity_code'],ensure_ascii=False).strip('"')
                else:
                    identity_code = ''
                if 'graduate' in info.keys():
                    graduate = info['graduate']
                else:
                    graduate = ''
                if 'educationDegree' in info.keys():
                    educationDegree = info['educationDegree']
                else:
                    educationDegree = ''
                if 'enrolDate' in info.keys():
                    enrolDate = info['enrolDate']
                else:
                    enrolDate = ''
                if  'specialityName' in info.keys():
                    specialityName = info["specialityName"]
                else:
                    specialityName = ''
                if  'graduateTime' in info.keys():
                    graduateTime = info["graduateTime"]
                else:
                    graduateTime = ''
                if  'studyResult' in info.keys():
                    studyResult = info["studyResult"]
                else:
                    studyResult = ''
                if  'studyStyle' in info.keys():
                    studyStyle = info["studyStyle"]
                else:
                    studyStyle = ''
                if  'photo' in info.keys(): 
                    photo = json.dumps(info["photo"],ensure_ascii=False)
                else:
                    photo = ''
                #identity_code,'codeid'
                results.update({"status_code":status_code,"status":status,"identity_name": identity_name, "identity_code": identity_code, "graduate": graduate,
                    "educationDegree": educationDegree, "enrolDate": enrolDate, "specialityName":specialityName, "graduateTime": graduateTime,
                    "studyResult": studyResult, "studyResult": studyResult, "studyStyle": studyStyle, "photo": photo})   
            if  code == "0001" or '0002' or '1000' or '1001' or '1003' or '1004' or '1005' or '2000':
                results.update({"status_code":code, "status":status})
            for head in results.keys():
                headers.append(head)
        except Exception, e:
            print traceback.format_exc()
        return results, headers

        

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceXL.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:

            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                #row,'row1111111'
                csvfile.writerow(row)
            except:
                errlog.error('xlxxzx write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceZSKJ(IceLD):
    '''身份证二要素'''
    def __init__(self, *args):
        super(IceZSKJ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'idCard': '372324198811125712',
            'name': '刘明宁',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  pc mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'idCard':line['id'],
                              'name': line['name'],
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'zskj_idjy'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []
        for data in datas:
            result, header = IceZSKJ.transform(data)
            results.append(result)
        headed_sort = ['RESULT','guid','costTime']
        return results, headed_sort

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        try:
            if data and isinstance(data, dict):
                if 'RESULT' in data.keys():
                    RESULT = data['RESULT']
                else:
                    RESULT = ''
                if 'guid' in data.keys():
                    guid = data['guid']
                else:
                    guid = ''
                if 'costTime' in data.keys():
                    costTime = data['costTime']
                else:
                    costTime = ''
                results.update({'RESULT': RESULT, 'guid': guid, 'costTime': costTime})   
        except Exception, e:
            errlog.error('liantong tranform :'+traceback.format_exc())
        return results, headers

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceZSKJ.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('ZSKJ write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceHJKJ(IceLD):
    '''银行卡三四要素'''
    def __init__(self, *args):
        super(IceHJKJ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'identityNumber': '372324198811125712',
            'name': '张桂鹏',
            "phonenumber": '13414466643',
            'bankNo': '522401198411056219',
            'client_type':'100002',
            'interfaceflag':'1004',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  pc mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if 'cell' in line.keys():
                cell = line['cell']
            else:
                cell = ''
            user_info = dict({'identityNumber':line['id'],
                              'name': line['name'],
                              'phonenumber': cell,
                              'bankNo': line['bank_card1'],
                              'interfaceflag': line['other_var5'],
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'hjkj_bcjq'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []
        for data in datas:
            result, header = IceHJKJ.transform(data)
            results.append(result)
        headed_sort = ["result", "errMsg", "description", "costTime"]
        return results, headed_sort

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        try:
            if data and isinstance(data, dict):
                if 'result' in data.keys():
                    result = data['result']
                else:
                    result = ''
                if 'errMsg' in data.keys():
                    errMsg = data['errMsg']
                else:
                    errMsg = ''
                if 'description' in data.keys():
                    description = data['description']
                else:
                    description = ''
                if 'costTime' in data.keys():
                    costTime = data['costTime']
                else:
                    costTime = ''
                results.update({'result': result, 'errMsg': errMsg, 'description': description, "costTime": costTime})   
        except Exception, e:
            errlog.error('hjkj tranform :'+traceback.format_exc())
        return results, headers

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceHJKJ.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('HJKJ write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceLT(IceLD):
    '''联通的ice接口'''
    def __init__(self, *args):
        super(IceLT, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self,modal,select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        if select == "fy_dxyz":
            cell = "17703452114"
        elif select == "fy_ltyz":
            cell = '18513950766'
        else:
            cell = '13488198375'
        info = {'client_type': '100002',
            'swift_number': swift_number,
            'name': "何磊" ,                             
            'cardno': '140402198201310411',
            'mobile': cell,
            }
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = copy.deepcopy(user_dict_list)
        for line in user_dict_list:
            if 'date' in line.keys():
                date = line['apply_date'].strip()
            else:
                date = time.strftime('%Y-%m-%d')
            cardno = line['id'].strip()
            name = line['name'].strip()
            mobile = line['cell'].strip()
            if select == 'fy_ydyz':
                if mobile[:3] in ["134","135","136","137","138","139","147","150","151","152","157","158","159","178","182","183","187","188","184"]:
                    print 'yd'
                    swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
                    user_info = {'name':name,
                                'cardno': cardno, 
                                'mobile': mobile,
                                'client_type': '100002',
                                'swift_number': swift_number}
                    query_info_list.append((user_info, select))
                    line.update({'swift_number': swift_number})
                    data_txt.append((json.dumps(line), select))
                else:
                    self.user_dict_list.remove(line)
            elif select == 'fy_dxyz':
                if mobile[:3] in ["133","153","177","180","181","189"]:
                    print 'dx'
                    swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
                    user_info = {'name':name,
                                'cardno': cardno, 
                                'mobile': mobile,
                                'client_type': '100002',
                                'swift_number': swift_number}
                    query_info_list.append((user_info, select))
                    line.update({'swift_number': swift_number})
                    data_txt.append((json.dumps(line), select))
                else:
                    self.user_dict_list.remove(line)
            else:
                if mobile[:3] in ["130","131","132","155","156","185","186","145","176"]:
                    print 'lt'
                    swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
                    user_info = {'name':name,
                                'cardno': cardno, 
                                'mobile': mobile,
                                'client_type': '100002',
                                'swift_number': swift_number}
                    query_info_list.append((user_info, select))
                    line.update({'swift_number': swift_number})
                    data_txt.append((json.dumps(line), select))
                else:
                    self.user_dict_list.remove(line)
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        if len(info_list) == 0:
            results=[]
            list_txt=[]
        else:
            interface = Interface.objects.get(name=select)
            thread_num = interface.thread_num
            pool = ThreadPool(thread_num)
            results_json = pool.map(self.dataice.get_data, info_list)
            pool.close()
            pool.join()
            results = []
            for i in results_json:
                if i!=None:
                    try:
                        result = json.loads(i)
                    except ValueError:
                        result = None
                else:result = None
                results.append(result)
            # results = [json.loads(i) if i!=None else None for i in results_json]
            list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []

        for data in datas:
            result, header = IceLT.transform(data)
            results.append(result)
        headed_sort = ['Error','result','costTime']
        return results, headed_sort

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        try:
            if data and isinstance(data, dict):
                if 'Error' in data.keys():
                    error = data['Error']
                else:
                    error = ''
                if 'result' in data.keys():
                    result = data['result']
                else:
                    result = ''
                if 'costTime' in data.keys():
                    costTime = data['costTime']
                else:
                    costTime = ''
                results.update({'Error': error, 'result': result, 'costTime': costTime})   
                for head in results.keys():
                    headers.append(head)
            else:
                return {'result': ''},headers
        except Exception, e:
            errlog.error('liantong tranform :'+traceback.format_exc())
        return results, headers

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        print len(self.user_dict_list)
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceLT.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:

            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('fy_ltyz write csv wrong : '+ traceback.format_exc())
                continue
        f.close()

class IceDN(IceLD):
    '''道隆的ice接口'''
    def __init__(self, *args):
        super(IceDN, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        if 'dn_ftl' == select :
            info = {'client_type': '100002',
                'swift_number': swift_number,
                'mdn': "18911081356" ,                             
                'type': 'clear',
                'month': '201511',
                }
            ret = self.dataice.get_data((info, 'dn_ftl'))
        if  'dn_tl' == select:
            info = {'client_type': '100002',
                'swift_number': swift_number,
                'mdn': "18911081356" ,                             
                'type': 'clear',
                }
            ret = self.dataice.get_data((info, 'dn_tl'))
        if  'dn_tb' == select:
            info = {'client_type': '100002',
                'swift_number': swift_number,
                'mdn': "18911081356" ,                             
                'type': 'clear',
                }
            ret = self.dataice.get_data((info, 'dn_tb'))
        if  'dn_state' == select:
            info = {'client_type': '100002',
                'swift_number': swift_number,
                'mdn': "18911081356" ,                             
                'type': 'clear',
                }
            ret = self.dataice.get_data((info, 'dn_state'))
        if  'dn_balance' == select:
            info = {'client_type': '100002',
                'swift_number': swift_number,
                'mdn': "18911081356" ,                             
                'type': 'clear',
                'month': '201511',
                }
            ret = self.dataice.get_data((info, 'dn_balance'))
        if  'dn_mcip' == select:
            info = {'client_type': '100002',
                'swift_number': swift_number,
                'mdn': "18911081356" ,                             
                'type': 'clear',
                'month': '201511',
                'timeFlag':1
                }
            ret = self.dataice.get_data((info, 'dn_mcip'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if 'apply_date' in line.keys():
                date = line['apply_date'].strip().split('-')
                month = ''.join(date)
            else:
                month = time.strftime('%Y%m')
            if 'cell' in line.keys():
                mdn = line['cell'].strip()
            if 'type' in line.keys():
                mdntype = line['type'].strip()
            else:
                mdntype = 'clear'
            if 'other_var5' in line.keys():
                try:
                    timeFlag = int(line['other_var5'])
                except Exception, e:
                    timeFlag = 3
            else:
                timeFlag = 3
            user_info = {'month': month,
                        'timeFlag':timeFlag,
                        'mdn': mdn,
                        'type': mdntype,
                        'client_type': '100002',
                        'swift_number': swift_number}
            query_info_list.append((user_info,select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        headers = []
        for data in datas:
            result, header = IceDN.transform(data)
            results.append(result)
        headed_sort = ["code","message","time","data","style","costTime"]
        return results, headed_sort

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        code = ''
        message = ''
        time = ''
        mydata = ''
        costTime = ''
        if not isinstance(data, dict):
            results.update({'ServerError': 'return error'})
            return results,headers
        if u'code' in data.keys():
            code = data['code']
        if u'message' in data.keys():
            message = data['message']
        if u'time' in data.keys():
            time = data['time']
        if u'data' in data.keys():
            if data['data']:
                try:
                    mydata = json.loads(data['data'])['value']
                except Exception, e:
                    print traceback.format_exc()
                    mydata = ''
            else:
                mydata = ''
        if u'style' in data.keys():
            style = data['style']
        else:
            style = ''
        if u'costTime' in data.keys():
            costTime = data['costTime']
        results.update({'code': code, 'message': message, 'time': time, 'data':mydata, 'style': style, 'costTime': costTime})   
        for head in results.keys():
            headers.append(head)
        return results, headers

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceDN.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:

            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('fy_ltyz write csv wrong : '+ traceback.format_exc())
                continue
        f.close()



class IceBCJQ(IceLD):
    ''' 银行卡鉴权的接口'''
    def __init__(self, *args):
        super(IceBCJQ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'checkCode': '100047',
            'factors': '6222600910073402958|||18511092889|||||',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'bcjq'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  bcjq mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        try:
            info_list = []
            data_txt = []
            user_data = self.filereader.read_user_data(fields)
            user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
            self.user_dict_list = user_dict_list
            factors = ''
            for line in user_dict_list:
                swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
                line.update({'swift_number': swift_number})
                data_txt.append((json.dumps(line), select))
                bank_card = ''
                if 'bank_card1' in line.keys():
                    bank_card = line['bank_card1'].strip()
                if 'bank_card2' in line.keys():
                    bank_card = line['bank_card2'].strip()
                if 'bcjq_card_name' in modal:
                    factors = bank_card + '|' + line['name'].strip() + '|||||||'
                    user_info = dict({'chedata_txtckCode': '100046',
                                      'factors': factors,
                                      'client_type': '100002',
                                      'swift_numb1311er': swift_number})
                elif 'bcjq_card_cell' in modal:
                    factors = bank_card + '|||' + line['cell'].strip() + '|||||'
                    user_info = dict({'checkCode': '100047',
                                      'factors': factors,
                                      'client_type': '100002',
                                      'swift_number': swift_number})
                elif 'bcjq_card_name_id' in modal:
                    factors = bank_card + '|' + line['name'] + '|' + line['id'].strip() + '||||||'
                    user_info = dict({'checkCode': '100056',
                                      'factors': factors,
                                      'client_type': '100002',
                                      'swift_number': swift_number})
                elif 'bcjq_name_id_cell' in modal:
                    factors = bank_card + '|' + line['name'].strip() + '|' + line['id'].strip() + '|' + line['cell'].strip() + '|||||'
                    user_info = dict({'checkCode': '100060',
                                      'factors': factors,
                                      'client_type': '100002',
                                      'swift_number': swift_number})
                info_list.append((user_info,'bcjq'))
            return info_list, data_txt
        except  OperationalError:
            return  False, ''

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceBCJQ.transform(data, outdata[idx])
            results.append(result)
        return results

    @staticmethod
    def transform(data, outdata):
        result = []
        if isinstance(data, dict):
            for key in ('respCode', 'respDesc'):
                if key in data.keys():
                    result.append(data[key])
            if 'costTime' in data.keys():
                result.append(data['costTime'])
        return result

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results = IceBCJQ.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        heads = []
        head_dict = {'bcjq_card_name': ['flag_bc_name', 'bc_name'], 'bcjq_card_cell': ['flag_bc_cell', 'bc_cell'], 'bcjq_card_name_id': ['flag_bc_name_id', 'bc_name_id'], 'bcjq_name_id_cell': ['flag_bc_name_id_cell', 'bc_name_id_cell']}
        for key, value in head_dict.items():
            if key in modal:
                heads = heads + value
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + heads + ['time',]
        return OUT_CSV_FM_RL, results

    def write_to_txt(self, filename, headers, list_txt, crypt=False):
        f = open(filename, 'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        for line in list_txt:
            line_new = json.loads(line[0][0])
            if crypt:
                if 'id' in line_new:
                    if line_new['id']:
                        line_new['id'] = line_new['id'][:-4]+'##'+line_new['id'][-2]+'#'
                if 'name' in line_new:
                    line_new['name'] = '####'
                if 'cell' in line_new:
                    if line_new['cell']:
                        line_new['cell'] = line_new['cell'][:-4] + '####'
                if 'mobiles' in line_new:
                    if line_new['mobiles']:
                        line_new['mobiles'] = line_new['mobiles'][:-4] + '####'
                if 'mobile' in line_new:
                    if line_new['mobile']:
                        line_new['mobile'] = line_new['mobile'][:-4] + '####'
                if 'bank_card2' in line_new:
                    if line_new['bank_card2'] and len(line_new['bank_card2']) > 12:
                        line_new['bank_card2'] = line_new['bank_card2'][:12] + '#'*(len(line_new['bank_card2'][12:]) -1) + line_new['bank_card2'][-1:]
                if 'bank_card1' in line_new:
                    if line_new['bank_card1'] and len(line_new.get('bank_card1')) > 12:
                        line_new['bank_card1'] = line_new['bank_card1'][:12] + '#'*(len(line_new['bank_card1'][12:]) -1) + line_new['bank_card1'][-1:]
                if 'email' in line_new:
                    if line_new['email']:
                        pos = line_new['email'].find('@')
                        if pos >= 0:
                            line_new['email'] = '####' + line_new['email'][pos:]                
            f.write(json.dumps(line_new, ensure_ascii=False)+'\t\t')
            f.write(line[0][0][1]+'\t\t')
            f.write(json.dumps(line[0][1], ensure_ascii=False))
            f.write(json.dumps(line[1], ensure_ascii=False)+'\n')
        f.close()



class IceSZDJ(IceLD):
    '''月度收支等级的ice接口'''
    def __init__(self, *args):
        super(IceSZDJ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'client_type': '100002',
            'swift_number': swift_number,
            'mobileid': "18301916695" ,                             
            'querymonth': '201605',
            }

        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        nowmonth = time.strftime('%Y%m')
        now = time.strftime('%Y%m%d')
        error_date = [nowmonth+'01', nowmonth+'02', nowmonth+'03', nowmonth+'04', nowmonth+'05']
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if 'cell' in line.keys():
                mobileid = line['cell'].strip()    
            if 'apply_date' in line.keys() and len(line['apply_date']) == 10:
                apply_date = line['apply_date'].strip().split('-')
                date = ''.join(apply_date)
            else:
                date = time.strftime('%Y%m%d')
            if date in error_date and now in error_date:
                date = date[:5] + str(int(date[5])-1)
            date = date[:6]
            user_info = {'mobileid':mobileid,
                        'querymonth': date, 
                        'client_type': '100002',
                        'swift_number': swift_number}
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt,results)
        #results,'results'
        return results, list_txt

    @staticmethod
    def transforms(datas):
        results = []
        for data in datas:
            result, header = IceSZDJ.transform(data)
            results.append(result)
        headed_sort = ['flag_accountChangeMonth', 'ac_regionno', 'bank_pf_ind', 'bank_js_ind', 'bank_zs_ind', 'bank_zg_ind', 'bank_gs_ind', 'bank_xy_ind', 'bank_pa_ind', 'bank_zsx_ind', 'bank_jt_ind', 'card_index', 'ac_m1_debit_balance', 'ac_m1_debit_out', 'ac_m1_debit_out_num', 'ac_m1_debit_invest', 'ac_m1_debit_repay', 'ac_m1_debit_in', 'ac_m1_debit_in_num', 'ac_m1_credit_out', 'ac_m1_credit_out_num', 'ac_m1_credit_cash', 'ac_m1_credit_in', 'ac_m1_credit_in_num', 'ac_m1_credit_def', 'ac_m1_loan', 'ac_m1_credit_status', 'ac_m1_cons', 'ac_m1_max_in', 'ac_m2_debit_balance', 'ac_m2_debit_out', 'ac_m2_debit_out_num', 'ac_m2_debit_invest', 'ac_m2_debit_repay', 'ac_m2_debit_in', 'ac_m2_debit_in_num', 'ac_m2_credit_out', 'ac_m2_credit_out_num', 'ac_m2_credit_cash', 'ac_m2_credit_in', 'ac_m2_credit_in_num', 'ac_m2_credit_def', 'ac_m2_loan', 'ac_m2_credit_status', 'ac_m2_cons', 'ac_m2_max_in', 'ac_m3_debit_balance', 'ac_m3_debit_out', 'ac_m3_debit_out_num', 'ac_m3_debit_invest', 'ac_m3_debit_repay', 'ac_m3_debit_in', 'ac_m3_debit_in_num', 'ac_m3_credit_out', 'ac_m3_credit_out_num', 'ac_m3_credit_cash', 'ac_m3_credit_in', 'ac_m3_credit_in_num', 'ac_m3_credit_def', 'ac_m3_loan', 'ac_m3_credit_status', 'ac_m3_cons', 'ac_m3_max_in', 'ac_m4_debit_balance', 'ac_m4_debit_out', 'ac_m4_debit_out_num', 'ac_m4_debit_invest', 'ac_m4_debit_repay', 'ac_m4_debit_in', 'ac_m4_debit_in_num', 'ac_m4_credit_out', 'ac_m4_credit_out_num', 'ac_m4_credit_cash', 'ac_m4_credit_in', 'ac_m4_credit_in_num', 'ac_m4_credit_def', 'ac_m4_loan', 'ac_m4_credit_status', 'ac_m4_cons', 'ac_m4_max_in', 'ac_m5_debit_balance', 'ac_m5_debit_out', 'ac_m5_debit_out_num', 'ac_m5_debit_invest', 'ac_m5_debit_repay', 'ac_m5_debit_in', 'ac_m5_debit_in_num', 'ac_m5_credit_out', 'ac_m5_credit_out_num', 'ac_m5_credit_cash', 'ac_m5_credit_in', 'ac_m5_credit_in_num', 'ac_m5_credit_def', 'ac_m5_loan', 'ac_m5_credit_status', 'ac_m5_cons', 'ac_m5_max_in', 'ac_m6_debit_balance', 'ac_m6_debit_out', 'ac_m6_debit_out_num', 'ac_m6_debit_invest', 'ac_m6_debit_repay', 'ac_m6_debit_in', 'ac_m6_debit_in_num', 'ac_m6_credit_out', 'ac_m6_credit_out_num', 'ac_m6_credit_cash', 'ac_m6_credit_in', 'ac_m6_credit_in_num', 'ac_m6_credit_def', 'ac_m6_loan', 'ac_m6_credit_status', 'ac_m6_cons', 'ac_m6_max_in', 'ac_m1m3_debit_balance', 'ac_m1m3_debit_out', 'ac_m1m3_debit_out_num', 'ac_m1m3_debit_invest', 'ac_m1m3_debit_repay', 'ac_m1m3_debit_in', 'ac_m1m3_debit_in_num', 'ac_m1m3_credit_out', 'ac_m1m3_credit_out_num', 'ac_m1m3_credit_cash', 'ac_m1m3_credit_in', 'ac_m1m3_credit_in_num', 'ac_m1m3_credit_def', 'ac_m1m3_loan', 'ac_m1m3_credit_status', 'ac_m1m3_cons', 'ac_m1m3_max_in', 'ac_m4m6_debit_balance', 'ac_m4m6_debit_out', 'ac_m4m6_debit_out_num', 'ac_m4m6_debit_invest', 'ac_m4m6_debit_repay', 'ac_m4m6_debit_in', 'ac_m4m6_debit_in_num', 'ac_m4m6_credit_out', 'ac_m4m6_credit_out_num', 'ac_m4m6_credit_cash', 'ac_m4m6_credit_in', 'ac_m4m6_credit_in_num', 'ac_m4m6_credit_def', 'ac_m4m6_loan', 'ac_m4m6_credit_status', 'ac_m4m6_cons', 'ac_m4m6_max_in', 'ac_m7m9_debit_balance', 'ac_m7m9_debit_out', 'ac_m7m9_debit_out_num', 'ac_m7m9_debit_invest', 'ac_m7m9_debit_repay', 'ac_m7m9_debit_in', 'ac_m7m9_debit_in_num', 'ac_m7m9_credit_out', 'ac_m7m9_credit_out_num', 'ac_m7m9_credit_cash', 'ac_m7m9_credit_in', 'ac_m7m9_credit_in_num', 'ac_m7m9_credit_def', 'ac_m7m9_loan', 'ac_m7m9_credit_status', 'ac_m7m9_cons', 'ac_m7m9_max_in', 'ac_m10m12_debit_balance', 'ac_m10m12_debit_out', 'ac_m10m12_debit_out_num', 'ac_m10m12_debit_invest', 'ac_m10m12_debit_repay', 'ac_m10m12_debit_in', 'ac_m10m12_debit_in_num', 'ac_m10m12_credit_out', 'ac_m10m12_credit_out_num', 'ac_m10m12_credit_cash', 'ac_m10m12_credit_in', 'ac_m10m12_credit_in_num', 'ac_m10m12_credit_def', 'ac_m10m12_loan', 'ac_m10m12_credit_status', 'ac_m10m12_cons', 'ac_m10m12_max_in', 'ac_m13m15_debit_balance', 'ac_m13m15_debit_out', 'ac_m13m15_debit_out_num', 'ac_m13m15_debit_invest', 'ac_m13m15_debit_repay', 'ac_m13m15_debit_in', 'ac_m13m15_debit_in_num', 'ac_m13m15_credit_out', 'ac_m13m15_credit_out_num', 'ac_m13m15_credit_cash', 'ac_m13m15_credit_in', 'ac_m13m15_credit_in_num', 'ac_m13m15_credit_def', 'ac_m13m15_loan', 'ac_m13m15_credit_status', 'ac_m13m15_cons', 'ac_m13m15_max_in', 'ac_m16m18_debit_balance', 'ac_m16m18_debit_out', 'ac_m16m18_debit_out_num', 'ac_m16m18_debit_invest', 'ac_m16m18_debit_repay', 'ac_m16m18_debit_in', 'ac_m16m18_debit_in_num', 'ac_m16m18_credit_out', 'ac_m16m18_credit_out_num', 'ac_m16m18_credit_cash', 'ac_m16m18_credit_in', 'ac_m16m18_credit_in_num', 'ac_m16m18_credit_def', 'ac_m16m18_loan', 'ac_m16m18_credit_status', 'ac_m16m18_cons', 'ac_m16m18_max_in',  'hf_acc_date',  'hf_auth_date', 'hf_bal_sign', 'hf_balance', 'hf_user_status']
        return results, headed_sort

    @staticmethod
    def transform(data):
        results = {}
        headers = []
        try:
            if not isinstance(data, dict):
                results.update({'ServerError': 'return error'})
                return results,headers
            retcode = data['retcode']
            if retcode != '0000':
                results.update({'flag_accountChangeMonth': '0'})
            else:
                results.update({"flag_accountChangeMonth":'1'})
                if 'br_v2_1_mobile_6m' in data.keys():
                    for data_6m in data['br_v2_1_mobile_6m']:
                        if data_6m["@id"] == "1":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m1_debit_balance":text[0],"ac_m1_debit_out":text[1],"ac_m1_debit_out_num":text[2],"ac_m1_debit_invest":text[3],
                                "ac_m1_debit_repay":text[4],"ac_m1_debit_in":text[5],"ac_m1_debit_in_num":text[6],"ac_m1_credit_out":text[7],
                                "ac_m1_credit_out_num":text[8],"ac_m1_credit_cash":text[9],"ac_m1_credit_in":text[10],"ac_m1_credit_in_num":text[11],
                                "ac_m1_credit_def":text[12],"ac_m1_loan":text[13],"ac_m1_credit_status":text[14],"ac_m1_cons":text[15],"ac_m1_max_in":text[16]})
                        
                        if data_6m["@id"] == "2":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m2_debit_balance":text[0],"ac_m2_debit_out":text[1],"ac_m2_debit_out_num":text[2],"ac_m2_debit_invest":text[3],
                                "ac_m2_debit_repay":text[4],"ac_m2_debit_in":text[5],"ac_m2_debit_in_num":text[6],"ac_m2_credit_out":text[7],
                                "ac_m2_credit_out_num":text[8],"ac_m2_credit_cash":text[9],"ac_m2_credit_in":text[10],"ac_m2_credit_in_num":text[11],
                                "ac_m2_credit_def":text[12],"ac_m2_loan":text[13],"ac_m2_credit_status":text[14],"ac_m2_cons":text[15],"ac_m2_max_in":text[16]})

                        if data_6m["@id"] == "3":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m3_debit_balance":text[0],"ac_m3_debit_out":text[1],"ac_m3_debit_out_num":text[2],"ac_m3_debit_invest":text[3],
                                "ac_m3_debit_repay":text[4],"ac_m3_debit_in":text[5],"ac_m3_debit_in_num":text[6],"ac_m3_credit_out":text[7],
                                "ac_m3_credit_out_num":text[8],"ac_m3_credit_cash":text[9],"ac_m3_credit_in":text[10],"ac_m3_credit_in_num":text[11],
                                "ac_m3_credit_def":text[12],"ac_m3_loan":text[13],"ac_m3_credit_status":text[14],"ac_m3_cons":text[15],"ac_m3_max_in":text[16]})

                        if data_6m["@id"] == "4":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m4_debit_balance":text[0],"ac_m4_debit_out":text[1],"ac_m4_debit_out_num":text[2],"ac_m4_debit_invest":text[3],
                                "ac_m4_debit_repay":text[4],"ac_m4_debit_in":text[5],"ac_m4_debit_in_num":text[6],"ac_m4_credit_out":text[7],
                                "ac_m4_credit_out_num":text[8],"ac_m4_credit_cash":text[9],"ac_m4_credit_in":text[10],"ac_m4_credit_in_num":text[11],
                                "ac_m4_credit_def":text[12],"ac_m4_loan":text[13],"ac_m4_credit_status":text[14],"ac_m4_cons":text[15],"ac_m4_max_in":text[16]})

                        if data_6m["@id"] == "5":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m5_debit_balance":text[0],"ac_m5_debit_out":text[1],"ac_m5_debit_out_num":text[2],"ac_m5_debit_invest":text[3],
                                "ac_m5_debit_repay":text[4],"ac_m5_debit_in":text[5],"ac_m5_debit_in_num":text[6],"ac_m5_credit_out":text[7],
                                "ac_m5_credit_out_num":text[8],"ac_m5_credit_cash":text[9],"ac_m5_credit_in":text[10],"ac_m5_credit_in_num":text[11],
                                "ac_m5_credit_def":text[12],"ac_m5_loan":text[13],"ac_m5_credit_status":text[14],"ac_m5_cons":text[15],"ac_m5_max_in":text[16]})

                        if data_6m["@id"] == "6":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m6_debit_balance":text[0],"ac_m6_debit_out":text[1],"ac_m6_debit_out_num":text[2],"ac_m6_debit_invest":text[3],
                                "ac_m6_debit_repay":text[4],"ac_m6_debit_in":text[5],"ac_m6_debit_in_num":text[6],"ac_m6_credit_out":text[7],
                                "ac_m6_credit_out_num":text[8],"ac_m6_credit_cash":text[9],"ac_m6_credit_in":text[10],"ac_m6_credit_in_num":text[11],
                                "ac_m6_credit_def":text[12],"ac_m6_loan":text[13],"ac_m6_credit_status":text[14],"ac_m6_cons":text[15],"ac_m6_max_in":text[16]})


                if 'br_v2_1_mobile_18m' in data.keys():
                    for data_6m in data['br_v2_1_mobile_18m']:
                        if data_6m["@id"] == "1":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m1m3_debit_balance":text[0],"ac_m1m3_debit_out":text[1],"ac_m1m3_debit_out_num":text[2],"ac_m1m3_debit_invest":text[3],
                                "ac_m1m3_debit_repay":text[4],"ac_m1m3_debit_in":text[5],"ac_m1m3_debit_in_num":text[6],"ac_m1m3_credit_out":text[7],
                                "ac_m1m3_credit_out_num":text[8],"ac_m1m3_credit_cash":text[9],"ac_m1m3_credit_in":text[10],"ac_m1m3_credit_in_num":text[11],
                                "ac_m1m3_credit_def":text[12],"ac_m1m3_loan":text[13],"ac_m1m3_credit_status":text[14],"ac_m1m3_cons":text[15],"ac_m1m3_max_in":text[16]})
                        if data_6m["@id"] == "4":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m4m6_debit_balance":text[0],"ac_m4m6_debit_out":text[1],"ac_m4m6_debit_out_num":text[2],"ac_m4m6_debit_invest":text[3],
                                "ac_m4m6_debit_repay":text[4],"ac_m4m6_debit_in":text[5],"ac_m4m6_debit_in_num":text[6],"ac_m4m6_credit_out":text[7],
                                "ac_m4m6_credit_out_num":text[8],"ac_m4m6_credit_cash":text[9],"ac_m4m6_credit_in":text[10],"ac_m4m6_credit_in_num":text[11],
                                "ac_m4m6_credit_def":text[12],"ac_m4m6_loan":text[13],"ac_m4m6_credit_status":text[14],"ac_m4m6_cons":text[15],"ac_m4m6_max_in":text[16]})
                        if data_6m["@id"] == "7":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m7m9_debit_balance":text[0],"ac_m7m9_debit_out":text[1],"ac_m7m9_debit_out_num":text[2],"ac_m7m9_debit_invest":text[3],
                                "ac_m7m9_debit_repay":text[4],"ac_m7m9_debit_in":text[5],"ac_m7m9_debit_in_num":text[6],"ac_m7m9_credit_out":text[7],
                                "ac_m7m9_credit_out_num":text[8],"ac_m7m9_credit_cash":text[9],"ac_m7m9_credit_in":text[10],"ac_m7m9_credit_in_num":text[11],
                                "ac_m7m9_credit_def":text[12],"ac_m7m9_loan":text[13],"ac_m7m9_credit_status":text[14],"ac_m7m9_cons":text[15],"ac_m7m9_max_in":text[16]})
                        if data_6m["@id"] == "10":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m10m12_debit_balance":text[0],"ac_m10m12_debit_out":text[1],"ac_m10m12_debit_out_num":text[2],"ac_m10m12_debit_invest":text[3],
                                "ac_m10m12_debit_repay":text[4],"ac_m10m12_debit_in":text[5],"ac_m10m12_debit_in_num":text[6],"ac_m10m12_credit_out":text[7],
                                "ac_m10m12_credit_out_num":text[8],"ac_m10m12_credit_cash":text[9],"ac_m10m12_credit_in":text[10],"ac_m10m12_credit_in_num":text[11],
                                "ac_m10m12_credit_def":text[12],"ac_m10m12_loan":text[13],"ac_m10m12_credit_status":text[14],"ac_m10m12_cons":text[15],"ac_m10m12_max_in":text[16]})
                        if data_6m["@id"] == "13":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m13m15_debit_balance":text[0],"ac_m13m15_debit_out":text[1],"ac_m13m15_debit_out_num":text[2],"ac_m13m15_debit_invest":text[3],
                                "ac_m13m15_debit_repay":text[4],"ac_m13m15_debit_in":text[5],"ac_m13m15_debit_in_num":text[6],"ac_m13m15_credit_out":text[7],
                                "ac_m13m15_credit_out_num":text[8],"ac_m13m15_credit_cash":text[9],"ac_m13m15_credit_in":text[10],"ac_m13m15_credit_in_num":text[11],
                                "ac_m13m15_credit_def":text[12],"ac_m13m15_loan":text[13],"ac_m13m15_credit_status":text[14],"ac_m13m15_cons":text[15],"ac_m13m15_max_in":text[16]})
                        if data_6m["@id"] == "16":
                            text = data_6m["#text"].split(',')
                            results.update({"ac_m16m18_debit_balance":text[0],"ac_m16m18_debit_out":text[1],"ac_m16m18_debit_out_num":text[2],"ac_m16m18_debit_invest":text[3],
                                "ac_m16m18_debit_repay":text[4],"ac_m16m18_debit_in":text[5],"ac_m16m18_debit_in_num":text[6],"ac_m16m18_credit_out":text[7],
                                "ac_m16m18_credit_out_num":text[8],"ac_m16m18_credit_cash":text[9],"ac_m16m18_credit_in":text[10],"ac_m16m18_credit_in_num":text[11],
                                "ac_m16m18_credit_def":text[12],"ac_m16m18_loan":text[13],"ac_m16m18_credit_status":text[14],"ac_m16m18_cons":text[15],"ac_m16m18_max_in":text[16]})


                if "br_mobile_once" in data.keys():
                    once = data['br_mobile_once'][0].split(',')
                    results.update({'bank_pf_ind':once[0][0],'bank_js_ind':once[0][1],'bank_zs_ind':once[0][2],'bank_zg_ind':once[0][3],'bank_gs_ind':once[0][4],
                        'bank_xy_ind':once[0][5],'bank_pa_ind':once[0][6],'bank_zsx_ind':once[0][7],'bank_jt_ind':once[0][8],'ac_regionno':once[1],'card_index':once[2]})        
                if 'br_mobile_auth' in data.keys():
                    auth = data["br_mobile_auth"][0].split(',')
                    results.update({'hf_acc_date':auth[0], 'hf_auth_date':auth[1], 'hf_bal_sign':auth[2], 'hf_balance':auth[3], 'hf_user_status':auth[4]})
            for head in results.keys():
                headers.append(head)
        except Exception, e:
            print traceback.format_exc()
        return results, headers

        

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        results, headers = IceSZDJ.transforms(results)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields +  headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:

            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('szdj write csv wrong : '+ traceback.format_exc())
                continue
        f.close()



# class IceLOSS(IceLD):
#     ''' LOSS的接口'''
#     def __init__(self, *args):
#         super(IceLOSS, self).__init__(*args)
#         self.apicode = args[1]

#     def ice_init(self):
#         #self.dataice = Loss()
#         self.loss = Loss()
#         self.es = Es()
#         self.neo = Neo()
#         try:
#             self.loss.initialize()
#             self.es.initialize()
#             self.neo.initialize()
#         except Exception, e:
#             errlog.error('ice error is :'+traceback.format_exc())
#             errlog.error('in the  ice init ,there is out of runtime')
#             return False
#         return True

#     def check_ice(self, modal, select):
#         swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
#         appkey = 'S1007'
#         qq = '599276452'
#         cell_md5 = KV(k="cell_md5",v="470072b34e5c7edb6543b5f78835f1ad")
#         mail_md5 = KV(k="mail_md5",v="6e5dbd5fd3bebf9ff968e820c69811a0")
#         id_md5  = KV(k="id_md5",v="5b34fa1b39cc0046cc98b25fea1aaa75")
#         dic = {
#             "max_depth": "1",
#             "max_count": "10",
#             "cur_date": "0",         
#             "neo_cluster": "nc1",   
#             "cache_status": "1",    
#             "match": {
#                     "cell": [
#                         "15313369932" 
#                     ],
#                     "id": [
#                         "211103199402042736" 
#                     ],
#                     "mail": [
#                         "" 
#                     ],
#                     "qq": [
#                         "599276452"
#                     ],
#                     "weibo": [
#                         ""
#                     ]
#                 }
#             }
#         jsonString = json.dumps(dic)
#         try:
#             ret1 = self.loss.findQunNumByQQNum(qq)
#             ret2 = self.es.getAddrData([id_md5,cell_md5,mail_md5])
#             ret3 = self.neo.searchNodes(jsonString, appkey)
#         except Exception, e:
#             ret = False
#         else:
#             ret = True
#         return ret

#     def destroy(self):
#         self.loss.destroy()
#         self.es.destroy()
#         self.neo.destroy()

#     def generate_query_infos(self, select, fields, fields_rel, modal):
#         try:
#             info_list_1 = []
#             info_list_2 = []
#             info_list_qq = []
#             info_list_phone = []
#             query_info_list = []
#             data_txt = []
#             user_data = self.filereader.read_user_data(fields)
#             user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
#             self.user_dict_list = user_dict_list
#             m = hashlib.md5()
#             for line in user_dict_list:
#                 user_info2 = []
#                 data_txt.append((json.dumps(line),'loss'))
#                 if 'id' in line.keys():
#                     idCard = line["id"]
#                     m.update(line['id'])
#                     id_num = m.hexdigest()
#                     id_md5 = KV(k="id_md5",v=id_num)
#                 else :
#                     idCard = None
#                     id_md5 = None
#                 if 'cell' in line.keys():
#                     cell = line['cell']
#                     m.update(line['cell'])
#                     cell_num = m.hexdigest()
#                     cell_md5 = KV(k="cell_md5",v=cell_num)
#                     info_list_phone.append(cell)
#                 else:
#                     cell = None
#                     cell_md5 = None
#                     info_list_phone.append('')
#                 if 'email' in line.keys():
#                     email = line['email']
#                     m.update(line['email'])
#                     mail_num = m.hexdigest()
#                     mail_md5 = KV(k='mail_md5',v=mail_num)
#                 else:
#                     email = None
#                     mail_md5 = None
#                 if 'qq' in line.keys():
#                     qq = line['qq']
#                     info_list_qq.append(qq)
#                 else:
#                     qq = None
#                     info_list_qq.append('')
#                 if 'weibo' in line.keys():
#                     weibo = line['weibo']
#                 else:
#                     weibo = None
#                 dic = {
#                     "max_depth": "1",
#                     "max_count": "10",
#                     "cur_date": "0",         
#                     "neo_cluster": "nc1",   
#                     "cache_status": "1",    
#                     "match": {
#                         "cell": [
#                             cell 
#                         ],
#                         "id": [
#                             idCard 
#                         ],
#                         "mail": [
#                             email 
#                         ],
#                         "qq": [
#                             qq
#                         ],
#                         "weibo": [
#                             weibo
#                         ]
#                     }
#                 }
#                 user_info_1 = json.dumps(dic)
#                 info_list_1.append(user_info_1)
#                 if id_md5:
#                     user_info2.append(id_md5)
#                 if cell_md5:
#                     user_info2.append(cell_md5)
#                 if mail_md5:
#                     user_info2.append(mail_md5)
#                 info_list_2.append(user_info2)
#             query_info_list.append(info_list_1)    #info_loss_list
#             query_info_list.append(info_list_2)    #info_es_list
#             query_info_list.append(info_list_qq)
#             query_info_list.append(info_list_phone)
#             query_info_list.append(modal[1])        #select_modal
#             return query_info_list,data_txt
#         except Exception, e:
#             print traceback.format_exc()

#     def query_ice_data(self, info_list, data_txt, select): 
#         results = []
#         def infunc(info):
#             appkey = 'S1007'
#             return self.neo.searchNodes(info, appkey)             
#         interface = Interface.objects.get(name=select)
#         thread_num = interface.thread_num
#         pool1 = ThreadPool(thread_num)
#         pool2 = ThreadPool(thread_num)
#         pool3 = ThreadPool(thread_num)
#         pool4 = ThreadPool(thread_num)
#         info_list_neo = info_list[0]
#         info_list_es = info_list[1]
#         info_list_qq = info_list[2]
#         info_list_phone = info_list[3]
#         results_neo = pool2.map(infunc, info_list_neo)
#         results_es = pool1.map(self.es.getAddrData, info_list_es)
#         results_qq = pool3.map(self.loss.findQunNumByQQNum, info_list_qq)
#         results_phone = pool4.map(self.loss.findAllPhoneByPhone, info_list_phone)
#         pool1.close()
#         pool1.join()
#         pool2.close()
#         pool2.join()
#         pool3.close()
#         pool3.join()
#         pool4.close()
#         pool4.join()
#         list_txt = zip(data_txt, results_neo, results_es, results_qq, results_phone)
#         results.append(results_neo)
#         results.append(results_es)
#         results.append(results_qq)
#         results.append(results_phone)
#         return results, list_txt
        
#     def process_result(self, results, fileid, fields, fields_rel, modal, select):
#         final_results = []
#         heads = []
#         head_dict = {'loss_data': ['realname', 'sex', 'birth'], 'loss_mark': ['realname', 'phone', 'mail', 'weibo', 'qq'], 'loss_collect': ['realname', 'id_number','phone', 'contacts', 'mail', 'weibo', 'qq', 'qq_group', 'address', 'tel_number']}
#         for key, value in head_dict.items():
#             if key in modal:
#                 heads = heads + value
#         OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + heads 
#         results_neo = results[0]
#         results_es = results[1]
#         results_qq = results[2]
#         results_phone = results[3]
#         one_loss = {}
#         one_es = {}
#         one_qun = {}
#         one_contacts = {}
#         i,j,k,q = 0,0,0,0
#         for neo in results_neo:
#             res_neo = json.loads(neo.data)
#             cell_list = ''
#             mail_list = ''
#             qq_list = ''
#             weibo_list = ''
#             id_list = ''
#             sex = ''
#             birth = ''
#             if res_neo:
#                 for res in res_neo:
#                     one = json.loads(res)
#                     for key in one['list']:
#                         if key.startswith('id'):
#                             id_list = id_list + key.split('->')[1] + ','
#                         if key.startswith('mail'):
#                             mail_list = mail_list + key.split('->')[1] + ','
#                         if key.startswith('cell'):
#                             cell_list = cell_list + key.split('->')[1] + ','
#                         if key.startswith('qq'):
#                             qq_list = qq_list + key.split('->')[1] + ','
#                         if key.startswith('weibo'):
#                             weibo_list = weibo_list + key.split('->')[1] + ','
#             if id_list:
#                 id_num = id_list.split(',')[0]
#                 if len(id_num) == 15:
#                     nian = id_num[6:8]
#                     yue = id_num[8:10]
#                     ri = id_num[10:12]
#                     birth = nian+'-'+yue+'-'+ri
#                     sex_num = id_num[-1]
#                     if sex_num in ['1','3','5','7','9']:
#                         sex = '男'
#                     elif sex_num in ['0','2','4','6','8']:
#                         sex = '女'
#                     else:
#                         sex = ''
#                 if len(id_num) == 18:
#                     nian = id_num[6:10]
#                     yue = id_num[10:12]
#                     ri = id_num[12:14]
#                     birth = nian+'-'+yue+'-'+ri
#                     sex_num = id_num[16]
#                     if sex_num in ['1','3','5','7','9']:
#                         sex = '男'
#                     elif sex_num in ['0','2','4','6','8']:
#                         sex = '女'
#                     else:
#                         sex = ''
#             id_list = id_list.rstrip(',')
#             weibo_list = weibo_list.rstrip(',')
#             qq_list = qq_list.rstrip(',')
#             mail_list = mail_list.rstrip(',')
#             cell_list = cell_list.rstrip(',')
#             one_loss.update({i:{'phone':cell_list, 'mail':mail_list,'weibo':weibo_list ,'qq': qq_list, 'id_number':id_list, 'sex':sex, 'birth':birth}})
#             i = i + 1
#         for es in results_es:
#             address = ''
#             realname = ''
#             tel_number = ''
#             if es:
#                 for es_data in es:
#                     es_dict = json.loads(es_data)
#                     if 'addr' in es_dict.keys():
#                         address = es_dict['addr']
#                     if 'realname' in es_dict.keys():
#                         realname = ','.join(es_dict['realname'])
#                     if 'phone' in es_dict.keys():
#                         tel_number = ','.join(es_dict['phone'])
#             one_es.update({j:{'address':address, 'realname':realname, 'tel_number':tel_number}})
#             j = j + 1
#         for qun in results_qq:
#             qq_group = ''
#             if qun:
#                 qq_group = ','.join(qun)
#             one_qun.update({k:{'qq_group':qq_group}})
#             k = k + 1
#         for con in results_phone:
#             contacts = ''
#             if con:
#                 contacts = ','.join(con)
#             one_contacts.update({q:{'contacts':contacts}})
#             q = q + 1
#         for num in one_contacts.keys():
#             one_result = one_loss[num]
#             one_result.update(one_es[num])
#             one_result.update(one_qun[num])
#             one_result.update(one_contacts[num])
#             for k in one_result.keys():
#                 if k not in heads:
#                     one_result.pop(k)
#             final_results.append(one_result)
#         loss_results = self.linklist(final_results, fileid, fields_rel)   
#         return OUT_CSV_FM_RL, loss_results            

#     def linklist(self, results, fileid, fields_rel):
#         ret_list = []
#         offset = self.filereader.startline + 1
#         for idx, data in enumerate(self.user_dict_list):
#             openid = 'br%06d%07d' % (fileid, idx+offset)
#             #outdata = [data[i] for i in self.filereader.fields_rel]
#             ret = dict(data.items() + results[idx].items())
#             ret.update({'openid': openid})
#             ret_list.append(ret)
#         return ret_list

#     def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
#         f = open(filename,'wb')
#         f.write(u'\ufeff'.encode('utf-8'))
#         csvfile = csv.DictWriter(f,headers, delimiter=',')
#         csvfile.writeheader()
#         for row in lines:
#             try:
#                 if crypt:
#                     line_keys = row.keys()
#                     if 'id' in headers:
#                         if 'id' in line_keys:
#                             try:
#                                 row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
#                             except:row['id'] = ''
#                     if 'name' in headers:
#                         row['name'] = '####'
#                     if 'cell' in headers:
#                         if 'cell' in line_keys:
#                             row['cell'] = row['cell'][:-4]+'####'
#                     if 'ac_mobile_id' in headers:
#                         if 'ac_mobile_id' in line_keys:
#                             row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
#                     if 'bank_card2' in headers:
#                         if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
#                             row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
#                     if 'bank_card1' in headers:
#                         if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
#                             row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
#                     if 'email' in headers:
#                         if 'email' in line_keys:
#                             pos = row['email'].find('@')
#                             if pos >= 0:
#                                 row['email'] = '####' + row['email'][pos:]
#                 if 'querymonth' in row.keys():
#                     user_date = row.pop('querymonth')
#                     row.update({'user_date': user_date})
#                 if 'mobiles' in row.keys():
#                     row.pop('mobiles')
#                 csvfile.writerow(row)
#             except:
#                 errlog.error('zcx_sxzx write csv wrong : '+ traceback.format_exc())
#                 continue
#         f.close()

#     def write_to_txt(self, filename, headers, list_txt, crypt=False):
#         f = open(filename, 'wb')
#         for line in list_txt:
#             line_new = json.loads(line[0][0])
#             if crypt:
#                 if 'id' in line_new:
#                     if line_new['id']:
#                         line_new['id'] = line_new['id'][:-4]+'##'+line_new['id'][-2]+'#'
#                 if 'name' in line_new:
#                     line_new['name'] = '####'
#                 if 'cell' in line_new:
#                     if line_new['cell']:
#                         line_new['cell'] = line_new['cell'][:-4] + '####'
#                 if 'mobiles' in line_new:
#                     if line_new['mobiles']:
#                         line_new['mobiles'] = line_new['mobiles'][:-4] + '####'
#                 if 'mobile' in line_new:
#                     if line_new['mobile']:
#                         line_new['mobile'] = line_new['mobile'][:-4] + '####'
#                 if 'bank_card2' in line_new:
#                     if line_new['bank_card2'] and len(line_new['bank_card2']) > 12:
#                         line_new['bank_card2'] = line_new['bank_card2'][:12] + '#'*(len(line_new['bank_card2'][12:]) -1) + line_new['bank_card2'][-1:]
#                 if 'bank_card1' in line_new:
#                     if line_new['bank_card1'] and len(line_new.get('bank_card1')) > 12:
#                         line_new['bank_card1'] = line_new['bank_card1'][:12] + '#'*(len(line_new['bank_card1'][12:]) -1) + line_new['bank_card1'][-1:]
#                 if 'email' in line_new:
#                     if line_new['email']:
#                         pos = line_new['email'].find('@')
#                         if pos >= 0:
#                             line_new['email'] = '####' + line_new['email'][pos:]    

#             f.write(u'\ufeff'.encode('utf-8'))
#             f.write(json.dumps(line_new)+'\t\t')
#             f.write(line[0][1]+'\t\t')
#             f.write(str(line[1:-1])+'\t')
#             last = json.dumps(line[-1],ensure_ascii=False)
#             last = last.replace('\\','')
#             f.write(last+'\n')
#         f.close()
        



class IceBCHX(IceLD):
    '''支付画像的接口'''
    def __init__(self, *args):
        super(IceBCHX, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'card': '6214680160380935',
            'name': '李良彗',
            'index': 'S0343,S0346,S0307',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'bchx'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  new PayConsumption  mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            bank_card = ''
            index = ''
            if 'bank_card1' in line.keys():
                bank_card = line['bank_card1'].strip()
            if 'bank_card2' in line.keys():
                bank_card = line['bank_card2'].strip()
            if 'other_var5' in line.keys():
                index_list = line['other_var5'].split('|')
                index = ','.join(index_list)
            user_info = dict({'card':bank_card,
                              'name': line['name'],
                              'client_type': '100002',
                              "index": index,
                              'swift_number': swift_number})
            query_info_list.append((user_info,'bchx'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
 
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        headers = []
        for idx, data in enumerate(datas):
            result, header = IceBCHX.transform(data, outdata[idx])
            results.append(result)
            if header:
                #header.sort(reverse=True)
                for head in header:
                    headers.append(head)
        headered = set(headers)
        headered = list(headered)
        try:
            headered.sort(key = BCHX_FIEL_LIST.index)
        except Exception, e:
            pass
        return results, headered

    @staticmethod
    def transform(data, outdata):
        result = {}
        heads = []
        keys = BCHX_INDEX.keys()
        if isinstance(data, dict):
            if 'data' in data.keys():
                if 'validate' in data['data'].keys():
                    heads.append('flag_pf')
                    result.update({'flag_pf': data['data']['validate']})
                if 'result' in data['data'].keys():
                    if 'active' in data['data']['result'].keys():
                        heads.append('pf_cardactive')
                        result.update({'pf_cardactive': data['data']['result']['active']})
                    if 'quota' in data['data']['result'].keys():
                        index_result = data['data']['result']['quota']
                        for key in index_result.keys():
                            if key in keys:
                                heads.append(BCHX_INDEX[key])
                                result.update({BCHX_INDEX[key]: index_result[key].replace(';', '|')})
        return result, heads

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            #outdata = [data[i] for i in self.filereader.fields_rel]
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, headers = IceBCHX.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_LD = ['openid', 'swift_number'] + fields + headers
        return OUT_CSV_FM_LD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('bchx write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceIDJY(IceLD):
    '''身份证认证的接口'''
    def __init__(self, *args):
        super(IceIDJY, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'idnum': '372324198811125712',
            'name': '刘明宁',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'idjy'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  pc mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'idnum':line['id'],
                              'name': line['name'],
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'idjy'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()

        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceIDJY.transform(data, outdata[idx])
            results.append(result)
        return results

    @staticmethod
    def transform(data, outdata):
        result = []
        if isinstance(data, dict):
            if 'costTime' in data.keys():
                result.append(data['costTime'])
            if 'resCode' in data.keys():
                result.append(data['resCode'])
            else:
                result.append('0')
            if 'data' in data.keys() and isinstance(data['data'], dict):
                if 'result' in data['data'].keys():
                    result.append(data['data']['result'])
                if 'message' in data['data'].keys():
                    result.append(data['data']['message'])
        return result

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results = IceIDJY.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + ['costTime', 'flag_id_auth', 'id_auth_result', 'id_auth_message']
        return OUT_CSV_FM_RL, results

class IceDD(IceLD):
    '''综合运营商数据'''
    def __init__(self, *args):
        super(IceDD, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'idnumber': '372324198811125712',
            'credit': '',
            'fields': 'A1001,C1001,C1002,D1001,D1002',
            'tel': '18511092889',
            'name': '刘明宁',
            'client_type':'100002',
            'swift_number': swift_number}
        ret= self.dataice.get_data((info, 'dd'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  dd mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = copy.deepcopy(user_dict_list)
        for line in user_dict_list:
            
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            cardId = ''
            for key in  ("bank_card1", 'bank_card2', 'ttt'):
                if key in line.keys() and len(line[key]) > 11:
                    try:
                        int(line[key])
                        cardId = line[key]
                        break
                    except Exception, e:
                        pass
            index = line['other_var5'].replace('|', ',')
            if 'id' in line.keys():
                id_num = line['id']
            else:
                id_num = ''
            if 'cell' in line.keys():
                cell = line['cell']
            else:
                cell = ''
            if 'name' in line.keys():
                name = line['name']
            else:
                name = ''
            if cell[:3] in ["134","135","136","137","138","139","147","150","151","152","157","158","159","178","182","183","187","188","184"]:
                self.user_dict_list.remove(line)
                continue
            if index in ["D1001", "D1002", "D1001,D1002"]:
                if cell[:3] not in ["130","131","132","155","156","185","186","145","176","133","153","177","180","181","189"]:
                    self.user_dict_list.remove(line)
                    continue
            if index == "F1003":
                if cell[:3] not in ["133","153","177","180","181","189"]:
                    self.user_dict_list.remove(line)
                    continue
            user_info = dict({'idnumber': id_num,
                              'name': name,
                              'credit': cardId,
                              'tel': cell,
                              'fields': index,
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'dd'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        if len(info_list)==0:
            results = []
            list_txt = []
        else:
            interface = Interface.objects.get(name=select)
            thread_num = interface.thread_num
            pool = ThreadPool(thread_num)
            results_json = pool.map(self.dataice.get_data, info_list)
            pool.close()
            pool.join()

            results = []
            for i in results_json:
                if i!=None:
                    try:
                        result = json.loads(i)
                    except ValueError:
                        result = None
                else:result = None
                results.append(result)
            list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        for idx, data in enumerate(datas):
            result = IceDD.transform(data, outdata[idx])
            heads = heads + result.keys()
            results.append(result)
        head = list(set(heads))
        head.sort()
        return results, head

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            if 'costTime' in data.keys():
                result.update({'costTime': data['costTime']})
            if 'result' in data.keys():
                result.update({'result': data['result']})
            if 'data' in data.keys():
                if isinstance(data['data'], dict):
                    for key, item in data['data'].items():
                        item = str(item)
                        result.update({key: item.replace(',', '|').replace('，', '|').replace(';', '|')})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceDD.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_DD = ['openid', 'swift_number'] + fields + heads
        return OUT_CSV_FM_DD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):# 不要忘了写
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    line_keys = row.keys()
                    if 'id' in headers:
                        if 'id' in line_keys:
                            try:
                                row['id'] = row['id'][:-4] + '##' + row['id'][-2] + '#'
                            except:row['id'] = ''
                    if 'name' in headers:
                        row['name'] = '####'
                    if 'cell' in headers:
                        if 'cell' in line_keys:
                            row['cell'] = row['cell'][:-4]+'####'
                    if 'ac_mobile_id' in headers:
                        if 'ac_mobile_id' in line_keys:
                            row['ac_mobile_id'] = row['ac_mobile_id'][:-4]+'####'
                    if 'bank_card2' in headers:
                        if 'bank_card2' in line_keys and len(row['bank_card2']) > 12:
                            row['bank_card2'] = row['bank_card2'][:12] + '#'*(len(row['bank_card2'][12:]) - 1) + row['bank_card2'][-1:]
                    if 'bank_card1' in headers:
                        if 'bank_card1' in line_keys and len(row['bank_card1']) > 12:
                            row['bank_card1'] = row['bank_card1'][:12] + '#'*(len(row['bank_card1'][12:]) - 1) + row['bank_card1'][-1:]
                    if 'email' in headers:
                        if 'email' in line_keys:
                            pos = row['email'].find('@')
                            if pos >= 0:
                                row['email'] = '####' + row['email'][pos:]
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()




class IcePC(IceLD):
    '''支付消费的ice接口'''
    def __init__(self, *args):
        super(IcePC, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'cardId': '6214830112707772',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'shbc'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  pc mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            cardId = ''
            for key in  ("bank_card1", 'bank_card2', 'ttt'):
                if key in line.keys() and len(line[key]) > 11:
                    try:
                        int(line[key])
                        cardId = line[key]
                        break
                    except Exception, e:
                        pass
            if not cardId:
                continue
            user_info = dict({'cardId':cardId,
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'shbc'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()

        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt, results)
        return results, list_txt


    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(outdata):
            cardId = ''
            for key in  ("bank_card1", 'bank_card2', 'ttt'):
                line = data
                if key in line.keys() and len(line[key]) > 11:
                    try:
                        int(line[key])
                        cardId = line[key]
                        break
                    except Exception, e:
                        pass
            if cardId:
                result = IcePC.transform(datas[idx], data)
            else:
                datas.insert(idx, '')
                result = IcePC.transform('', data)
            results.append(result)
        return results


    @staticmethod
    def transform(data, outdata):
        if not data:
            return ['0']
        results = []
        if not isinstance(data, dict):
            return results
        if data["code"] != '00' or data == None:
            results.append('0')
            return results
        else:
            results.append('1')
        if 'PayConsumption' not in data.keys():
            return results
        result_data = data['PayConsumption']
        if 'apply_date' in outdata.keys() and outdata['apply_date'][4:5] == '-':
            month = outdata['apply_date'][:4] + outdata['apply_date'][5:7]
        else:
            month  = time.strftime('%Y%m')
        # 先多减一个月的
        if month[-2:] == '01':
            num = str(int(month[3])-1)
            month = month[:3] + num + '13'
        if month[-2:] == '10':
            month = month[:4] + '09'
        else:
            month = month[:5] + str(int(month[5])-1)
        # 按月份依次匹配表头
        for num in range(18): 
            if month[-2:] == '01':
                num_status = str(int(month[3])-1)
                month = month[:3] + num_status + '13'
            if month[-2:] == '10':
                month = month[:4] + '09'
            else:
                month = month[:5] + str(int(month[5])-1) 
            if num == 0:
                results.append(month)
            if month in result_data.keys():
                items = result_data[month]
            else:
                items = {1: '', 2: '', 3: '', 4: '', 5: '', 6: '', 7: '', 8: '', 9: '', 10: '', 11: ''}
            if isinstance(items, dict):             
                for item in ['pay', 'number', 'first_pay_mcc', 'first_number_mcc', 'second_pay_mcc', 'second_number_mcc', 'third_pay_mcc', 'third_number_mcc', 'max_number_city', 'night_pay', 'night_number']:
                    if item in items.keys():
                        item = items[item]
                        if isinstance(item, unicode):
                            item = item.replace('\N', 'null')   
                    else:
                        item = ''
                    results.append(item)
        len_data = 0
        for result in results[2:]:
            if result:
                len_data =+ 1
        if len_data:
            return results
        else:
            results[0] = '0'
            return results[:2]

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results = IcePC.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_PC = ['openid', 'swift_number'] + fields + PC_FIELD_LIST
        return OUT_CSV_FM_PC, results


class IcePC2(IceLD):
    '''支付消费的ice接口'''
    def __init__(self, *args):
        super(IcePC2, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info2 = {'cardno': '6214830112707772',
            'client_type':'100002',
            'swift_number': swift_number}
        ret2 = self.dataice.get_data((info2, 'shbcty'))
        if ret2:
            try:
                ret2 = json.loads(ret2)
            except Exception, e:
                errlog.error('here  pc2 mapping :'+ traceback.format_exc())
            else: 
                ret2 = True
        return ret2

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list2 = []
        data_txt =[] 
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            cardId = ''
            for key in  ("bank_card1", 'bank_card2', 'ttt'):
                if key in line.keys() and len(line[key]) > 11:
                    try:
                        int(line[key])
                        cardId = line[key]
                        break
                    except Exception, e:
                        pass
            if not cardId:
                continue
            user_info2 = dict({'cardno':cardId,
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list2.append((user_info2, 'shbcty'))
        return query_info_list2, data_txt

    def get_data(self, info):
        try:
            time.sleep(0.1)
            result = self.dac_server.getdata(json.dumps(info[0]), info[1])
        except:
            result = None


    def query_ice_data(self, info_list2, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json2 = pool.map(self.get_data, info_list2)
        pool.close()
        pool.join()

        results2 = []
        for i in results_json2:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results2.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt, results2)
        return results2, list_txt

    @staticmethod
    def transforms(datas2, outdata):
        results = []
        for idx, data in enumerate(outdata):
            cardId = ''
            for key in  ("bank_card1", 'bank_card2', 'ttt'):
                line = data
                if key in line.keys() and len(line[key]) > 11:
                    try:
                        int(line[key])
                        cardId = line[key]
                        break
                    except Exception, e:
                        pass
            if cardId:
                result2 = IcePC2.transform2(datas2[idx], data)
            else:
                datas2.insert(idx, '')
                result2 = IcePC2.transform2('', data)
            results.append(result2)
        return results

    @staticmethod
    def transform2(data, outdata):
        if not data:
            return ['0']
        results = []
        result = {}
        if isinstance(data, dict):
            if 'error_code' in data.keys() and data['error_code'] == 0:
                results.append('1')
            else:
                results.append('0')
            for key in data.keys():
                if key == 'data':
                    result = data[key]
        if not data:
            return results
        if not result:
            return results
        if 'apply_date' in outdata.keys() and outdata['apply_date'][4:5] == '-':
            month = outdata['apply_date'][:4] + outdata['apply_date'][5:7]
        else:
            month  = time.strftime('%Y%m')
        if month[-2:] == '01':
            num = str(int(month[3])-1)
            month = month[:3] + num + '13'
        if month[-2:] == '10':
            month = month[:4] + '09'
        else:
            month = month[:5] + str(int(month[5])-1)
        results.append(month)
        if result and isinstance(result, list):
            result = result[0]
            for key in PC2_SORT:
                item = result[key].replace('"null"', 'null')
                results.append(item)
        return results

    def process_result(self, results2, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results = IcePC2.transforms(results2, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_PC = ['openid', 'swift_number'] + fields + PC2_FIELD_LIST
        return OUT_CSV_FM_PC, results



class IceMMD(IceLD):
    '''么么贷的ice接口'''
    def __init__(self, *args):
        super(IceMMD, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'access_token':'38c175ebacada398bba219ca3c813aec',
           'idNo':'431122198811121430',
           'name':u'徐斌',
           'purpose':u'P2P借贷',
           'client_type':'100002',
           'swift_number':swift_number }
        ret = self.dataice.get_data((info, 'mmd'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        info_list = []
        data_txt = []
        lines = self.filereader.read_user_data(fields)
        lines = self.filereader.tansform_user_data_mmd(lines, fields, fields_rel)
        self.user_dict_list = lines
        for line in lines:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            name = line['name'].strip()
            idNo = line['idNo'].strip()
            user_info = dict({'access_token':'38c175ebacada398bba219ca3c813aec',
                      'name': name,
                      'idNo': idNo,
                      'purpose':'P2P借贷',
                      'client_type':'100002',
                      'swift_number':swift_number})
            info_list.append((user_info,'mmd'))
        return info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()

        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        # results = [json.loads(i) if i!=None else None for i in results_json]
        list_txt = zip(data_txt, results)
        return results, list_txt

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        lines = []
        #fields = self.filereader.fields
        OUT_CSV_FM_MMD = ['openid', 'swift_number'] + fields + ['bad_credit', 'fake_application', 'court_blacklist']
        offset = self.filereader.startline + 1
        for index, item in enumerate(results):
            openid = 'br%06d%07d' % (fileid, index+offset)
            user_dict = self.user_dict_list[index]
            outdata = [user_dict[i] for i in fields_rel]
            bad_credit = ''
            fake_application = ''
            court_blacklist = ''
            if item != None and item.get('errorCode', 1) == 0:
                content = item['content']
                risktype = content['riskType']
                if content['isBlacklist'] == 'Y':
                    bad_credit = '1' if risktype==u'资信不良' else '0'
                    fake_application = '1' if risktype==u'伪冒申请' else '0'
                    court_blacklist = '1' if risktype==u'法院不良' else '0'
                else:
                    bad_credit = '0'
                    fake_application = '0'
                    court_blacklist = '0'
            result = [openid] + outdata + [bad_credit, fake_application, court_blacklist]
            lines.append(result)
        return OUT_CSV_FM_MMD, lines


class IceQYTZ(IceLD):
    '''企业投资的接口'''
    def __init__(self, *args):
        super(IceQYTZ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'keyword': '百融至信(北京)征信有限公司',
            'client_type':'100002',
            'skip':'1',
            'pagesize':'1',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'qytz'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  qytz mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if 'reg_num' in line.keys():
                key_word = line['reg_num']
            if 'biz_name' in line.keys():
                key_word = line['biz_name']
            user_info = dict({'keyword': key_word,
                              'skip':'1',
                              'pagesize':'1',
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'qytz'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()

        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt, results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        max_num = 1
        for idx, data in enumerate(datas):
            result = IceQYTZ.transform(data, outdata[idx])
            heads = heads + result.keys()
            results.append(result)
            if 'num' in result.keys():
                if int(result['num']) > max_num:
                    max_num = result['num']
        head = list(set(heads))
        head_sort = ['resCode', 'message', 'orderNo', 'total', 'num']
        for num in  range(max_num):
            for item in ('name', 'id', 'start_date', 'oper_name'):
                item_num = item + str(num + 1)
                head_sort.append(item_num)
        head.sort(key = head_sort.index)
        return results, head

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            for key in ('resCode', 'orderNo', 'message'):
                if key in data.keys():
                    result.update({key: data[key]})
            if 'data' in data.keys() and isinstance(data['data'], dict):
                for key in ('total', 'num'):
                    result.update({key: data['data'][key]})
                    if isinstance(data['data']['items'], list):
                        for num in range(int(data['data']['num'])):
                            for item in ('name', 'id', 'start_date', 'oper_name'):
                                item_num = item + str(num + 1)
                                result.update({item_num: data['data']['items'][num][item]})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceQYTZ.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_DD = ['openid', 'swift_number'] + fields + heads
        return OUT_CSV_FM_DD, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceDWTZ(IceLD):
    '''个人投资的接口'''
    def __init__(self, *args):
        super(IceDWTZ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'key': '512531196407046379',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'dwtz'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  dwtz mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'key':line['id'].strip(),
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'dwtz'))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()

        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        head = []
        head_final = ["ORDERLIST_KEY","ORDERLIST_FINISHTIME","ORDERLIST_STATUS"]
        punishbreak_sort = ["PUNISHBREAK_CASECODE","PUNISHBREAK_INAMECLEAN","PUNISHBREAK_TYPE","PUNISHBREAK_SEXYCLEAN","PUNISHBREAK_CARDNUM","PUNISHBREAK_YSFZD"
            ,"PUNISHBREAK_BUSINESSENTITY","PUNISHBREAK_REGDATECLEAN","PUNISHBREAK_PUBLISHDATECLEAN","PUNISHBREAK_COURTNAME","PUNISHBREAK_AREANAMECLEAN"
            ,"PUNISHBREAK_GISTID","PUNISHBREAK_GISTUNIT","PUNISHBREAK_DUTY","PUNISHBREAK_DISRUPTTYPENAME","PUNISHBREAK_PERFORMANCE","PUNISHBREAK_PERFORMEDPART"
            ,"PUNISHBREAK_UNPERFORMPART"]
        punished_sort = ["PUNISHED_INAMECLEAN","PUNISHED_REGDATECLEAN","PUNISHED_COURTNAME","PUNISHED_EXECMONEY"]
        pyposfr_sort = ["RYPOSFR_RYNAME","RYPOSFR_ENTNAME","RYPOSFR_REGNO","RYPOSFR_ENTTYPE","RYPOSFR_REGCAP","RYPOSFR_REGCAPCUR","RYPOSFR_ENTSTATUS"]
        pypossha_sort = ["RYPOSSHA_RYNAME","RYPOSSHA_ENTNAME","RYPOSSHA_REGNO","RYPOSSHA_ENTTYPE","RYPOSSHA_REGCAP","RYPOSSHA_REGCAPCUR","RYPOSSHA_SUBCONAM","RYPOSSHA_CURRENCY","RYPOSSHA_CONFORM","RYPOSSHA_FUNDEDRATIO","RYPOSSHA_ENTSTATUS"]
        pyposper_sort = ["RYPOSPER_RYNAME","RYPOSPER_ENTNAME","RYPOSPER_REGNO","RYPOSPER_ENTTYPE","RYPOSPER_REGCAP","RYPOSPER_REGCAPCUR","RYPOSPER_ENTSTATUS","RYPOSPER_POSITION"]
        personcaseinfo_sort = ["PERSONCASEINFO_NAME","PERSONCASEINFO_CERNO","PERSONCASEINFO_CASETIME","PERSONCASEINFO_CASEREASON","PERSONCASEINFO_CASEVAL","PERSONCASEINFO_CASETYPE","PERSONCASEINFO_EXESORT","PERSONCASEINFO_CASERESULT"
            ,"PERSONCASEINFO_PENDECNO","PERSONCASEINFO_PENDECISSDATE","PERSONCASEINFO_PENAUTH","PERSONCASEINFO_ILLEGFACT","PERSONCASEINFO_PENBASIS","PERSONCASEINFO_PENTYPE","PERSONCASEINFO_PENRESULT"
            ,"PERSONCASEINFO_PENAM","PERSONCASEINFO_PENEXEST"]
        head_sort = punishbreak_sort + punished_sort + pyposfr_sort + pypossha_sort + pyposper_sort + personcaseinfo_sort
        for idx, data in enumerate(datas):
            result = IceDWTZ.transform(data, outdata[idx])
            results.append(result)
        for res in results:
            head = head + res.keys()
        heads = list(set(head))

        head1 = []
        head2 = []
        head3 = []
        head4 = []
        head5 = []
        head6 = []

        for i in range(1, 100):
            list1 = []
            
            for j in heads:
                if str(i) in j:
                    list1.append(j)

            for q in head_sort:
                if q+str(i) in list1:
                    head1.append(q+str(i))

        head_final = head_final + head1 + ['orderNo', 'costTime']
        return results, head_final

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            if 'orderNo' in data.keys():
                result.update({'orderNo': data['orderNo']})
            result.update({'costTime': data['costTime']})
            if 'ORDERLIST' in data.keys() and data['ORDERLIST']:
                result.update({'ORDERLIST_KEY': data['ORDERLIST'][0]['KEY'], 'ORDERLIST_FINISHTIME': data['ORDERLIST'][0]['FINISHTIME'], 'ORDERLIST_STATUS': data['ORDERLIST'][0]['STATUS']})
            if 'PUNISHBREAK' in data.keys() and data['PUNISHBREAK']:
                num = 1
                for d in data['PUNISHBREAK']:
                    if not d['BUSINESSENTITY']:
                        result.update({"PUNISHBREAK_CASECODE"+str(num): d['CASECODE'],"PUNISHBREAK_INAMECLEAN"+str(num): d['INAMECLEAN']
                            ,"PUNISHBREAK_TYPE"+str(num): d['TYPE'],"PUNISHBREAK_SEXYCLEAN"+str(num): d['SEXYCLEAN'],"PUNISHBREAK_CARDNUM"+str(num): d['CARDNUM']
                            ,"PUNISHBREAK_YSFZD"+str(num): d['YSFZD'],"PUNISHBREAK_BUSINESSENTITY"+str(num): d['BUSINESSENTITY']
                            ,"PUNISHBREAK_REGDATECLEAN"+str(num): d['REGDATECLEAN'],"PUNISHBREAK_PUBLISHDATECLEAN"+str(num): d['PUBLISHDATECLEAN']
                            ,"PUNISHBREAK_COURTNAME"+str(num): d['COURTNAME'],"PUNISHBREAK_AREANAMECLEAN"+str(num): d['AREANAMECLEAN']
                            ,"PUNISHBREAK_GISTID"+str(num): d['GISTID'],"PUNISHBREAK_GISTUNIT"+str(num): d['GISTUNIT']
                            ,"PUNISHBREAK_DUTY"+str(num): d['DUTY'],"PUNISHBREAK_DISRUPTTYPENAME"+str(num): d['DISRUPTTYPENAME']
                            ,"PUNISHBREAK_PERFORMANCE"+str(num): d['PERFORMANCE'],"PUNISHBREAK_PERFORMEDPART"+str(num): d['PERFORMEDPART']
                            ,"PUNISHBREAK_UNPERFORMPART"+str(num): d['UNPERFORMPART']})
                    else:
                        result.update({"PUNISHBREAK_CASECODE"+str(num): d['CASECODE'],"PUNISHBREAK_INAMECLEAN"+str(num): d['INAMECLEAN']
                            ,"PUNISHBREAK_TYPE"+str(num): d['TYPE'],"PUNISHBREAK_SEXYCLEAN"+str(num): d['SEXYCLEAN'],"PUNISHBREAK_CARDNUM"+str(num): d['CARDNUM']
                            ,"PUNISHBREAK_YSFZD"+str(num): d['YSFZD'],"PUNISHBREAK_BUSINESSENTITY"+str(num): ''
                            ,"PUNISHBREAK_REGDATECLEAN"+str(num): d['REGDATECLEAN'],"PUNISHBREAK_PUBLISHDATECLEAN"+str(num): d['PUBLISHDATECLEAN']
                            ,"PUNISHBREAK_COURTNAME"+str(num): d['COURTNAME'],"PUNISHBREAK_AREANAMECLEAN"+str(num): d['AREANAMECLEAN']
                            ,"PUNISHBREAK_GISTID"+str(num): d['GISTID'],"PUNISHBREAK_GISTUNIT"+str(num): d['GISTUNIT']
                            ,"PUNISHBREAK_DUTY"+str(num): d['DUTY'],"PUNISHBREAK_DISRUPTTYPENAME"+str(num): d['DISRUPTTYPENAME']
                            ,"PUNISHBREAK_PERFORMANCE"+str(num): d['PERFORMANCE'],"PUNISHBREAK_PERFORMEDPART"+str(num): d['PERFORMEDPART']
                            ,"PUNISHBREAK_UNPERFORMPART"+str(num): d['UNPERFORMPART']})
                    num = num + 1
            if "PUNISHED" in data.keys() and data['PUNISHED']:
                num = 1
                for d in data['PUNISHED']:
                    result.update({"PUNISHED_INAMECLEAN"+str(num):d['INAMECLEAN'],"PUNISHED_REGDATECLEAN"+str(num):d['REGDATECLEAN']
                        ,"PUNISHED_COURTNAME"+str(num):d['COURTNAME'],"PUNISHED_EXECMONEY"+str(num):d['EXECMONEY']})
                    num = num + 1
            if "RYPOSFR" in data.keys() and data['RYPOSFR']:
                num = 1
                for d in data['RYPOSFR']:
                    if not d['REGCAPCUR']:
                        result.update({"RYPOSFR_RYNAME"+str(num):d['RYNAME'],"RYPOSFR_ENTNAME"+str(num):d['ENTNAME']
                            ,"RYPOSFR_REGNO"+str(num):d['REGNO'],"RYPOSFR_ENTTYPE"+str(num):d['ENTTYPE'],"RYPOSFR_REGCAP"+str(num):d['REGCAP']
                            ,"RYPOSFR_REGCAPCUR"+str(num):d['REGCAPCUR'],"RYPOSFR_ENTSTATUS"+str(num):d['ENTSTATUS']})
                    else:
                        result.update({"RYPOSFR_RYNAME"+str(num):d['RYNAME'],"RYPOSFR_ENTNAME"+str(num):d['ENTNAME']
                            ,"RYPOSFR_REGNO"+str(num):d['REGNO'],"RYPOSFR_ENTTYPE"+str(num):d['ENTTYPE'],"RYPOSFR_REGCAP"+str(num):d['REGCAP']
                            ,"RYPOSFR_REGCAPCUR"+str(num):'',"RYPOSFR_ENTSTATUS"+str(num):d['ENTSTATUS']})
                    num = num + 1
            if "RYPOSSHA" in data.keys() and data['RYPOSSHA']:
                num = 1
                for d in data['RYPOSSHA']:
                    if not d['REGCAPCUR']:
                        result.update({"RYPOSSHA_RYNAME"+str(num): d['RYNAME'],"RYPOSSHA_ENTNAME"+str(num): d['ENTNAME']
                            ,"RYPOSSHA_REGNO"+str(num): d['REGNO'],"RYPOSSHA_ENTTYPE"+str(num): d['ENTTYPE']
                            ,"RYPOSSHA_REGCAP"+str(num): d['REGCAP'],"RYPOSSHA_REGCAPCUR"+str(num): d['REGCAPCUR']
                            ,"RYPOSSHA_SUBCONAM"+str(num): d['SUBCONAM'],"RYPOSSHA_CURRENCY"+str(num): d['CURRENCY']
                            ,"RYPOSSHA_CONFORM"+str(num): d['CONFORM'],"RYPOSSHA_FUNDEDRATIO"+str(num): d['FUNDEDRATIO']
                            ,"RYPOSSHA_ENTSTATUS"+str(num): d['ENTSTATUS']})
                    else:
                        result.update({"RYPOSSHA_RYNAME"+str(num): d['RYNAME'],"RYPOSSHA_ENTNAME"+str(num): d['ENTNAME']
                            ,"RYPOSSHA_REGNO"+str(num): d['REGNO'],"RYPOSSHA_ENTTYPE"+str(num): d['ENTTYPE']
                            ,"RYPOSSHA_REGCAP"+str(num): d['REGCAP'],"RYPOSSHA_REGCAPCUR"+str(num): ''
                            ,"RYPOSSHA_SUBCONAM"+str(num): d['SUBCONAM'],"RYPOSSHA_CURRENCY"+str(num): d['CURRENCY']
                            ,"RYPOSSHA_CONFORM"+str(num): d['CONFORM'],"RYPOSSHA_FUNDEDRATIO"+str(num): d['FUNDEDRATIO']
                            ,"RYPOSSHA_ENTSTATUS"+str(num): d['ENTSTATUS']})
                    num = num + 1
            if "RYPOSPER" in data.keys() and data['RYPOSPER']:
                num = 1
                for d in data['RYPOSPER']:
                    if not d['REGCAPCUR']:
                        if not d['POSITION']:
                            result.update({"RYPOSPER_RYNAME"+str(num): d['RYNAME'],"RYPOSPER_ENTNAME"+str(num): d['ENTNAME']
                                ,"RYPOSPER_REGNO"+str(num): d['REGNO'],"RYPOSPER_ENTTYPE"+str(num): d['ENTTYPE']
                                ,"RYPOSPER_REGCAP"+str(num): d['REGCAP'],"RYPOSPER_REGCAPCUR"+str(num): d['REGCAPCUR']
                                ,"RYPOSPER_ENTSTATUS"+str(num): d['ENTSTATUS'],"RYPOSPER_POSITION"+str(num): d['POSITION']})
                        else:
                            result.update({"RYPOSPER_RYNAME"+str(num): d['RYNAME'],"RYPOSPER_ENTNAME"+str(num): d['ENTNAME']
                                ,"RYPOSPER_REGNO"+str(num): d['REGNO'],"RYPOSPER_ENTTYPE"+str(num): d['ENTTYPE']
                                ,"RYPOSPER_REGCAP"+str(num): d['REGCAP'],"RYPOSPER_REGCAPCUR"+str(num): d['REGCAPCUR']
                                ,"RYPOSPER_ENTSTATUS"+str(num): d['ENTSTATUS'],"RYPOSPER_POSITION"+str(num): ''})
                    else:
                        if not d['POSITION']:
                            result.update({"RYPOSPER_RYNAME"+str(num): d['RYNAME'],"RYPOSPER_ENTNAME"+str(num): d['ENTNAME']
                                ,"RYPOSPER_REGNO"+str(num): d['REGNO'],"RYPOSPER_ENTTYPE"+str(num): d['ENTTYPE']
                                ,"RYPOSPER_REGCAP"+str(num): d['REGCAP'],"RYPOSPER_REGCAPCUR"+str(num): ''
                                ,"RYPOSPER_ENTSTATUS"+str(num): d['ENTSTATUS'],"RYPOSPER_POSITION"+str(num): d['POSITION']})
                        else:
                            result.update({"RYPOSPER_RYNAME"+str(num): d['RYNAME'],"RYPOSPER_ENTNAME"+str(num): d['ENTNAME']
                                ,"RYPOSPER_REGNO"+str(num): d['REGNO'],"RYPOSPER_ENTTYPE"+str(num): d['ENTTYPE']
                                ,"RYPOSPER_REGCAP"+str(num): d['REGCAP'],"RYPOSPER_REGCAPCUR"+str(num): ''
                                ,"RYPOSPER_ENTSTATUS"+str(num): d['ENTSTATUS'],"RYPOSPER_POSITION"+str(num): ''})
                    num = num + 1
            if "PERSONCASEINFO" in data.keys() and data['PERSONCASEINFO']:
                num = 1
                for d in data['PERSONCASEINFO']:
                    if not d['CASETYPE']:
                        result.update({"PERSONCASEINFO_NAME"+str(num): d['NAME'],"PERSONCASEINFO_CERNO"+str(num): d['CERNO']
                            ,"PERSONCASEINFO_CASETIME"+str(num): d['CASETIME'],"PERSONCASEINFO_CASEREASON"+str(num): d['CASEREASON']
                            ,"PERSONCASEINFO_CASEVAL"+str(num): d['CASEVAL'],"PERSONCASEINFO_CASETYPE"+str(num): d['CASETYPE']
                            ,"PERSONCASEINFO_EXESORT"+str(num): d['EXESORT'],"PERSONCASEINFO_CASERESULT"+str(num): d['CASERESULT']
                            ,"PERSONCASEINFO_PENDECNO"+str(num): d['PENDECNO'],"PERSONCASEINFO_PENDECISSDATE"+str(num): d['PENDECISSDATE']
                            ,"PERSONCASEINFO_PENAUTH"+str(num): d['PENAUTH'],"PERSONCASEINFO_ILLEGFACT"+str(num): d['ILLEGFACT']
                            ,"PERSONCASEINFO_PENBASIS"+str(num): d['PENBASIS'],"PERSONCASEINFO_PENTYPE"+str(num): d['PENTYPE']
                            ,"PERSONCASEINFO_PENRESULT"+str(num): d['PENRESULT'],"PERSONCASEINFO_PENAM"+str(num): d['PENAM']
                            ,"PERSONCASEINFO_PENEXEST"+str(num): d['PENEXEST']})
                    else:
                        result.update({"PERSONCASEINFO_NAME"+str(num): d['NAME'],"PERSONCASEINFO_CERNO"+str(num): d['CERNO']
                            ,"PERSONCASEINFO_CASETIME"+str(num): d['CASETIME'],"PERSONCASEINFO_CASEREASON"+str(num): d['CASEREASON']
                            ,"PERSONCASEINFO_CASEVAL"+str(num): d['CASEVAL'],"PERSONCASEINFO_CASETYPE"+str(num): ''
                            ,"PERSONCASEINFO_EXESORT"+str(num): d['EXESORT'],"PERSONCASEINFO_CASERESULT"+str(num): d['CASERESULT']
                            ,"PERSONCASEINFO_PENDECNO"+str(num): d['PENDECNO'],"PERSONCASEINFO_PENDECISSDATE"+str(num): d['PENDECISSDATE']
                            ,"PERSONCASEINFO_PENAUTH"+str(num): d['PENAUTH'],"PERSONCASEINFO_ILLEGFACT"+str(num): d['ILLEGFACT']
                            ,"PERSONCASEINFO_PENBASIS"+str(num): d['PENBASIS'],"PERSONCASEINFO_PENTYPE"+str(num): d['PENTYPE']
                            ,"PERSONCASEINFO_PENRESULT"+str(num): d['PENRESULT'],"PERSONCASEINFO_PENAM"+str(num): d['PENAM']
                            ,"PERSONCASEINFO_PENEXEST"+str(num): d['PENEXEST']})
                    num = num + 1
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceDWTZ.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        out_csv = ['openid', 'swift_number'] + fields + heads
        return out_csv, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error(' write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceQYJB(IceDWTZ):
    '''企业基本信息的接口'''
    def __init__(self, *args):
        super(IceQYJB, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'regNo': '110108013162411',
            'orgNO': '李良彗',
            'rentName': '李良彗',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'qyjb'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  qyjb mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret


    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt =[] 
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list

        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'client_type': '100002',
                              'swift_number': swift_number})
            if 'reg_num' in line.keys():
                user_info.update({'regNo': line['reg_num']})
            if 'org_num' in line.keys():
                user_info.update({'orgNO': line['org_num']})
            if 'biz_name' in line.keys():
                user_info.update({'entName': line['biz_name']})
            query_info_list.append((user_info,'qyjb'))
        return query_info_list, data_txt


    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        for idx, data in enumerate(datas):
            result = IceQYJB.transform(data, outdata[idx])
            results.append(result)
            heads = heads + result.keys()
        head = list(set(heads))
        head.sort(key = QYJB_CSV_HEAD.index)
        return results, head

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            for key in ('resCode', 'resMsg', 'orderNo', 'message'):
                if key in data.keys():
                    result.update({key: data[key]})
            if 'data' in data.keys() and data['data']:
                for key ,value in data['data'].items():
                    if key in QYJB_CSV_HEAD:
                        result.update({key: value})
        return result

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceQYJB.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        out_csv = ['openid', 'swift_number'] + fields + heads
        return out_csv, results


class IceCLWZ(IceDWTZ):
    '''车辆违章的接口'''
    def __init__(self, *args):
        super(IceCLWZ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'carnumber': '京GZV279',
            'carcode': 'LHGGD173282503334',
            'cardrivenumber': '5510664',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, 'clwz'))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  clwz mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list

        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'carnumber': line['vehicle_id'],
                              'carcode': line['car_code'],
                              'cardrivenumber': line['driver_number'],
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info,'clwz'))
        return query_info_list, data_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        max_time = 1
        for idx, data in enumerate(datas):
            result, time = IceCLWZ.transform(data, outdata[idx])
            results.append(result)
            heads = heads + result.keys()
            if max_time < time:
                max_time = time
        head = list(set(heads))
        head_sort = ['Success', 'ErrorCode', 'ErrMessage', 'HasDate', 'LastSearchTime', 'Other', 'Records', 'orderNo']
        for time in range(max_time):
            for one in CLWZ_CSV_HEAD:
                head_sort.append(one + str(time + 1))
        head.sort(key = head_sort.index)
        return results, head

    @staticmethod
    def transform(data, outdata):
        result = {}
        time = 0
        if isinstance(data, dict):
            for key in ('ErrorCode', 'Other', 'Success', 'orderNo', 'ErrMessage', 'LastSearchTime'):
                if key in data.keys():
                    result.update({key: data[key]})
            if 'Records' in data.keys() and data['Records']:
                for one in data['Records']:
                    time += 1
                    for key in one.keys():
                        if key in CLWZ_CSV_HEAD:
                            result.update({key + str(time): one[key]})
        return result, time

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceCLWZ.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        out_csv = ['openid', 'swift_number'] + fields + heads
        return out_csv, results


class IceQCCDW(IceLD):
    '''qcc 企业对外投资'''
    def __init__(self, *args):
        super(IceQCCDW, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'keyword': '百融（北京）金融信息服务股份有限公司',
            'pageSize': '10',
            'pageIndex': '1',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceQCC mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'keyword':line['biz_name'],
                              'pageSize': '10',
                              'pageIndex': '1',
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        for idx, data in enumerate(datas):
            result = IceQCCDW.transform(data, outdata[idx])
            head = result.keys()
            heads = heads + head
            head_final = list(set(heads))
            results.append(result)
        return results, head_final

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            if 'costTime' in data.keys():
                result.update({"Status":data['Status'],"costTime":data['costTime']})
            if 'Result' in data.keys(): 
                if data['Result']:
                    length = len(data['Result'])
                    max_range = range(1,length+1)
                    items = zip(max_range, data['Result'])
                    for item in items:
                        x = str(item[0])
                        for key in item[1]:
                            new_key = key+x
                            result.update({new_key: item[1][key]})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceQCCDW.transforms(results, outdata)
        head_sort = ['KeyNo','Name','No','BelongOrg','OperName','StartDate','EndDate','Status','Province','UpdatedDate','CreditCode','RegistCapi','EconKind','Address','Scope']
        head = []
        head_final = []
        for every in heads:
            if 'KeyNo' in every:
                head.append(every)
        max_num = len(head)  
        for num in range(1,max_num+1):
            head_num = []
            head_num_sort = []
            for every in heads:
                if str(num) in every:
                    head_num.append(every)
            for sort in head_sort:
                if sort+str(num) in head_num:
                    head_num_sort.append(sort+str(num))
            head_final = head_final + head_num_sort
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + ['Status'] +head_final + ['costTime']
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceQCCDWTP(IceLD):
    '''qcc 企业对外投资图谱'''
    def __init__(self, *args):
        super(IceQCCDWTP, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'keyNo': '9cce0780ab7644008b73bc2120479d31',
            'upstreamCount': '1',
            'downstreamCount': '1',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceQCCDWTP mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'keyNo':line['other_var5'],
                              'upstreamCount': '1',
                              'downstreamCount': '1',
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        for idx, data in enumerate(datas):
            result = IceQCCDWTP.transform(data, outdata[idx])
            head = result.keys()
            heads = heads + head
            head_final = list(set(heads))
            results.append(result)
        return results, head_final

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            if 'costTime' in data.keys():
                result.update({"Status":data['Status'],"costTime":data['costTime']})
            if 'Result' in data.keys(): 
                if data['Result']:
                    if 'Nodes' in data['Result'].keys():
                        if data['Result']['Nodes']:
                            length = len(data['Result']['Nodes'])
                            max_range = range(1,length+1)
                            items = zip(max_range, data['Result']['Nodes'])
                            for item in items:
                                x = str(item[0])
                                for key in item[1]:
                                    new_key = key+x
                                    result.update({new_key: item[1][key]})
                    if 'Links' in data['Result'].keys():
                        if data['Result']['Links']:
                            length = len(data['Result']['Links'])
                            max_range = range(1, length+1)
                            items = zip(max_range, data['Result']['Links'])
                            for item in items:
                                x = str(item[0])
                                for key in item[1]:
                                    new_key = key+x
                                    result.update({new_key: item[1][key]})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceQCCDWTP.transforms(results, outdata)
        head_sort = ['Target', 'Source', 'KeyNo', 'Name', 'Category', 'ShortName']
        head1 = []
        head2 = []
        head_final = []
        for every in heads:
            if 'KeyNo' in every:
                head1.append(every)
            if 'Target' in every:
                head2.append(every)
        head1_len = len(head1)
        head2_len = len(head2)
        max_num = max(head1_len, head2_len) 
        for num in range(1,max_num+1):
            head_num = []
            head_num_sort = []
            for every in heads:
                if str(num) in every:
                    head_num.append(every)
            for sort in head_sort:
                if sort+str(num) in head_num:
                    head_num_sort.append(sort+str(num))
            head_final = head_final + head_num_sort
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + ['Status'] + head_final + ['costTime']
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceQCCGD(IceLD):
    '''qcc 企业对外投资图谱'''
    def __init__(self, *args):
        super(IceQCCGD, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'searchKey': '马化腾,马云,雷军',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceQCCGD mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'searchKey':line['other_var5'],
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        for idx, data in enumerate(datas):
            result = IceQCCGD.transform(data, outdata[idx])
            head = result.keys()
            heads = heads + head
            head_final = list(set(heads))
            results.append(result)
        return results, head_final

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            if 'costTime' in data.keys():
                result.update({"Status":data['Status'],"costTime":data['costTime']})
            if 'Result' in data.keys(): 
                if data['Result']:
                    if 'Nodes' in data['Result'].keys():
                        if data['Result']['Nodes']:
                            length = len(data['Result']['Nodes'])
                            max_range = range(1,length+1)
                            items = zip(max_range, data['Result']['Nodes'])
                            for item in items:
                                x = str(item[0])
                                for key in item[1]:
                                    new_key = key+x
                                    result.update({new_key: item[1][key]})
                    if 'Links' in data['Result'].keys():
                        if data['Result']['Links']:
                            length = len(data['Result']['Links'])
                            max_range = range(1, length+1)
                            items = zip(max_range, data['Result']['Links'])
                            for item in items:
                                x = str(item[0])
                                for key in item[1]:
                                    new_key = key+x
                                    if key == 'Relation':
                                        vaelues = ''
                                        for value in item[1][key]:
                                            vaelues = vaelues + value + ','
                                        vaelues = vaelues.strip(',')
                                        result.update({new_key: vaelues})
                                    else:
                                        result.update({new_key: item[1][key]})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceQCCGD.transforms(results, outdata)
        head_sort = ['Target', 'Source', 'Relation', 'KeyNo', 'Name', 'Category', 'ShortName']
        head1 = []
        head2 = []
        head_final = []
        for every in heads:
            if 'KeyNo' in every:
                head1.append(every)
            if 'Target' in every:
                head2.append(every)
        head1_len = len(head1)
        head2_len = len(head2)
        max_num = max(head1_len, head2_len) 
        for num in range(1,max_num+1):
            head_num = []
            head_num_sort = []
            for every in heads:
                if str(num) in every:
                    head_num.append(every)
            for sort in head_sort:
                if sort+str(num) in head_num:
                    head_num_sort.append(sort+str(num))
            head_final = head_final + head_num_sort
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + ['Status'] + head_final + ['costTime']
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceQCCSZ(IceLD):
    '''qcc 企业对外投资图谱'''
    def __init__(self, *args):
        super(IceQCCSZ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'keyNo': '9cce0780ab7644008b73bc2120479d31',
            'upstreamCount': '1',
            'downstreamCount': '1',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceQCCSZ mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'keyNo':line['other_var5'],
                              'upstreamCount': '1',
                              'downstreamCount': '1',
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        for idx, data in enumerate(datas):
            result = IceQCCSZ.transform(data, outdata[idx])
            head = result.keys()
            heads = heads + head
            head_final = list(set(heads))
            results.append(result)
        return results, head_final

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            if 'costTime' in data.keys():
                result.update({"Status":data['Status'],"costTime":data['costTime']})
            if 'Result' in data.keys(): 
                if data['Result']:
                    if 'Node' in data['Result'].keys():
                        if data['Result']['Node']:
                            result.update({"KeyNo":data['Result']['Node']['KeyNo'],
                                            "Name":data['Result']['Node']['Name'],
                                            "Category":data['Result']['Node']['Category'],
                                            "ShortName":data['Result']['Node']['ShortName'],
                                            "Count":data['Result']['Node']['Count']})
                        if 'Children' in data['Result']['Node']:
                            if data['Result']['Node']['Children']:
                                length = len(data['Result']['Node']['Children'])
                                max_range = range(1, length+1)
                                items = zip(max_range, data['Result']['Node']['Children'])
                                for item in items:
                                    x = str(item[0])
                                    for key in item[1]:
                                        new_key = 'Children.'+key+x
                                        result.update({new_key: item[1][key]})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, heads = IceQCCSZ.transforms(results, outdata)
        head_sort = ['Children.Name','Children.KeyNo','Children.Category','Children.ShortName','Children.Count']
        head1 = []
        head_final = []
        for every in heads:
            if 'Children.Name' in every:
                head1.append(every)
        max_num = len(head1)
        for num in range(1,max_num+1):
            head_num = []
            head_num_sort = []
            for every in heads:
                if str(num) in every:
                    head_num.append(every)
            for sort in head_sort:
                if sort+str(num) in head_num:
                    head_num_sort.append(sort+str(num))
            head_final = head_final + head_num_sort
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + ['Status','KeyNo','Name','Category','ShortName','Count'] + head_final + ['costTime']
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceLWCP(IceLD):
    '''lw 车牌号身份证验证（海纳）,车辆状态查询（海纳）'''
    def __init__(self, *args):
        super(IceLWCP, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'hphm': '京NEX030',
            'hpzl': '小汽车',
            'sfzh': '110108197003206826',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceLWCP mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if select == 'lw_clztcx':
                user_info = dict({'hphm':line['vehicle_id'],
                                  'hpzl': line['type_vehicle_id'],
                                  'client_type': '100002',
                                  'swift_number': swift_number})
            if select == 'lw_cphsfzyz':
                user_info = dict({'hphm':line['vehicle_id'],
                                  'hpzl': line['type_vehicle_id'],
                                  'sfzh': line['id'],
                                  'client_type': '100002',
                                  'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceLWCP.transform(data, outdata[idx])
            results.append(result)
        return results

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            if 'costTime' in data.keys():
                result.update({"costTime":data['costTime']})
            if 'data' in data.keys():
                if isinstance(data['data'], dict):
                    for key in data['data'].keys():
                        result.update({key: data['data'][key]})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results = IceLWCP.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        if select == 'lw_clztcx':
            heads = ['result', 'hpzl', 'hphm', 'zt**', 'error', 'costTime']
        if select == 'lw_cphsfzyz':
            heads = ['sfzh', 'result', 'hpzl', 'hphm', 'error', 'costTime']
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + heads
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceHVGV(IceLD):
    '''zhx_航旅高舱飞行标签（海纳）, zhx_航旅旅客价值评分（海纳）'''
    def __init__(self, *args):
        super(IceHVGV, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'codes': '[{key:\"zhx_hlxw\",code:\"G57448646\"}]',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceHVGV mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            codes = '[{key:\"zhx_hlxw\",code:\"G57448646\"}]'.split('"')
            if select == 'zhx_hvgjfxbq':
                codes[-2] = line['passport_number']
            else:
                codes[-2] = line['id']
            tran_codes = '"'.join(codes)
            user_info = dict({'codes': tran_codes,
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceHVGV.transform(data, outdata[idx])
            results.append(result)
        return results

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "result":data['result']})
            if 'datas' in data.keys():
                if isinstance(data['datas'], dict):
                    if 'score' in data['datas'].keys():
                        result.update({'score': data['datas']['score']})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results = IceHVGV.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + ['score', 'result', 'costTime']
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceYLZCXW(IceLD):
    '''ylzc_支付消费行为偏好（海纳）'''
    def __init__(self, *args):
        super(IceYLZCXW, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'param': '6217002000033015894',
            'yearmonth': '201606',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceYLZCXW mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'param': line['bank_card1'],
                              'yearmonth': ''.join(line['apply_date'].split('-'))[0:6],
                              'client_type': '100002',
                              'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceYLZCXW.transform(data, outdata[idx])
            results.append(result)
        return results

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "error_code":data['error_code']})
            if 'data' in data.keys():
                if isinstance(data['data'], list):
                    if data['data'][0]:
                        for key in data['data'][0].keys():
                            if data['data'][0][key] == "\"null\"":
                                result.update({key: ""})
                            else:
                                result.update({key: data['data'][0][key]})
            if 'account_no' in result.keys():
                result.pop('account_no')
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results = IceYLZCXW.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        head = ['error_code', 'yearmonth', 'dc_flag', 'cst_score', 'cot_score', 'cot_cluster', 'cnt_score'
        , 'cna_score', 'chv_score', 'dsi_score', 'dsi_cluster', 'rsk_score', 'rsk_cluster', 'wlp_score'
        , 'crb_score', 'crb_cluster', 'cnp_score', 'summary_score', 'RFM_1_var1', 'RFM_1_var2', 'DAY_1_var1'
        , 'LOC_1_var1', 'MON_3_var1', 'RFM_3_var1', 'RFM_3_var2', 'RFM_3_var3', 'RFM_3_var4', 'RFM_3_var5'
        , 'MCC_3_var1', 'MON_6_var1', 'RFM_6_var1', 'RFM_6_var2', 'RFM_6_var3', 'RFM_6_var4', 'RFM_6_var5'
        , 'MCC_6_var1', 'FLAG_6_var1', 'FLAG_6_var3', 'LOC_6_var11', 'FLAG_6_var4', 'FLAG_6_var6', 'RFM_6_var6'
        , 'FLAG_6_var8', 'MON_12_var1', 'RFM_12_var1', 'RFM_12_var2', 'RFM_12_var3', 'RFM_12_var4', 'RFM_12_var5'
        , 'RFM_12_var6', 'RFM_12_var20', 'RFM_12_var21', 'RFM_12_var22', 'RFM_12_var23', 'RFM_12_var24'
        , 'RFM_12_var25', 'RFM_12_var26', 'RFM_12_var27', 'RFM_12_var29', 'RFM_12_var30', 'RFM_12_var39'
        , 'RFM_12_var40', 'RFM_12_var44', 'RFM_12_var45', 'RFM_12_var47', 'RFM_12_var48', 'RFM_12_var50'
        , 'RFM_12_var54', 'yearmonth', 'total_amt', 'total_cnt', 'mcc_amt_1', 'mcc_amt_2', 'mcc_amt_3', 'mcc_cnt_1'
        , 'mcc_cnt_2', 'mcc_cnt_3', 'trans_place', 'time_00_05_amt', 'time_00_05_cnt', 'costTime']
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceSHSB(IceLD):
    ''', 社保'''
    def __init__(self, *args):
        super(IceSHSB, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'identity_code': '32038219870819101X',
            'identity_name': u'石楠',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceSHSB mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'identity_code': line['id'],
                            'identity_name': line['name'],
                            'client_type': '100002',
                            'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        headers = []
        headed_sort = ['code', 'description', 'serial_no', 'status']
        for idx, data in enumerate(datas):
            result, heads = IceSHSB.transform(data, outdata[idx])
            results.append(result)
            for i in heads:
                headers.append(i)
            headers = list(set(headers))
        head_sort = ["companyName", "depositStatus", "updateTime"]

        for i in range(1,10):
            list1 = []
            headed = []
            for j in headers:
                if j[-1] == str(i):
                    list1.append(j)

            for k in head_sort:
                if k+str(i) in list1:
                    headed.append(k+str(i))

            headed_sort = headed_sort + headed
        headed_sort = headed_sort + ['result','costTime']
        for data in results:
            for key in data.keys():
                if key not in headed_sort:
                    data.pop(key)
        return results, headed_sort

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "code":data["api_status"]["code"]
                , "description":data["api_status"]["description"], "serial_no":data["api_status"]["serial_no"]
                , "status":data["api_status"]["status"]})
            if 'data' in data.keys():
                if data['data']['result'] == "match":
                    result.update({"result":data['data']['result']})
                    num = 1
                    for every in data["data"]["info"]["recordlist"]:
                        result.update({"companyName"+str(num): every["companyName"]
                            , "depositStatus"+str(num): every["depositStatus"]
                            , "updateTime"+str(num): every["updateTime"]})    
                        num = num + 1
        return result, result.keys()

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, head = IceSHSB.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceHJXX(IceLD):
    '''xb_户籍信息（海纳）'''
    def __init__(self, *args):
        super(IceHJXX, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'identity_code': '211224199311137913',
            'identity_name': u'王强',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceHJXX mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'identity_code': line['id'],
                            'identity_name': line['name'],
                            'client_type': '100002',
                            'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        headed_sort = ['code', 'description', 'serial_no', 'status']
        for idx, data in enumerate(datas):
            result = IceHJXX.transform(data, outdata[idx])
            results.append(result)
        head = ["code","description","serial_no","status","address","birthPlace","birthday","company"
            ,"edu","formerName","maritalStatus","nation","originPlace","sex","result","costTime"]
        for data in results:
            for key in data.keys():
                if key not in head:
                    data.pop(key)
        return results, head

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "code":data["api_status"]["code"]
                , "description":data["api_status"]["description"], "serial_no":data["api_status"]["serial_no"]
                , "status":data["api_status"]["status"]})
            if 'data' in data.keys():
                if data['data']['result'] == "match":
                    result.update({"result": data['data']['result'], "address": data['data']['info']["residence"]['address']
                        , "birthPlace": data['data']['info']["residence"]['birthPlace'], "birthday": data['data']['info']["residence"]['birthday']
                        , "company": data['data']['info']["residence"]['company'], "edu": data['data']['info']["residence"]['edu']
                        , "formerName": data['data']['info']["residence"]['formerName'], "maritalStatus": data['data']['info']["residence"]['maritalStatus']
                        , "nation": data['data']['info']["residence"]['nation'], "originPlace": data['data']['info']["residence"]['originPlace']
                        , "sex": data['data']['info']["residence"]['sex']})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, head = IceHJXX.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceRJH(IceLD):
    '''联通收支等级'''
    def __init__(self, *args):
        super(IceRJH, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'mobile': '18513112048',
            'dataRange': '4',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceRJH mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'mobile': line['cell'],
                            #'dataRange': '4',
                            'client_type': '100002',
                            'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceRJH.transform(data, outdata[idx])
            results.append(result)
        head = ['code', 'last1_p_dom', 'last1_p_doc', 'last1_p_dnom', 'last1_p_dnoc', 'last1_p_dcm', 'last1_p_dcc'
            , 'last1_p_dlrm', 'last1_p_dlrc', 'last1_p_docm', 'last1_p_docc', 'last1_p_dsom', 'last1_p_dsoc', 'last1_p_dcrm'
            , 'last1_p_dcrc', 'last1_p_dim', 'last1_p_dic', 'last1_p_com', 'last1_p_coc', 'last1_p_cnom', 'last1_p_cnoc'
            , 'last1_p_ccm', 'last1_p_ccc', 'last1_p_cocm', 'last1_p_cocc', 'last1_p_csom', 'last1_p_csoc', 'last1_p_ccrm'
            , 'last1_p_ccrc', 'last1_p_clm', 'last1_p_clc', 'last1_p_cisf', 'last1_p_cissc', 'last1_p_cisbs', 'last1_c_db'
            , 'last1_c_dbn', 'last1_c_dc', 'last1_c_ctc', 'last1_c_cbn', 'last1_c_cc', 'last1_i_dim', 'last1_i_dic', 'last1_i_dsim'
            , 'last1_i_dsic', 'last1_i_bm', 'last1_i_crm', 'last1_i_crc', 'last3_p_dom', 'last3_p_doc', 'last3_p_dnom'
            , 'last3_p_dnoc', 'last3_p_dcm', 'last3_p_dcc', 'last3_p_dlrm', 'last3_p_dlrc', 'last3_p_docm', 'last3_p_docc'
            , 'last3_p_dsom', 'last3_p_dsoc', 'last3_p_dcrm', 'last3_p_dcrc', 'last3_p_dim', 'last3_p_dic', 'last3_p_com'
            , 'last3_p_coc', 'last3_p_cnom', 'last3_p_cnoc', 'last3_p_ccm', 'last3_p_ccc', 'last3_p_cocm', 'last3_p_cocc'
            , 'last3_p_csom', 'last3_p_csoc', 'last3_p_ccrm', 'last3_p_ccrc', 'last3_p_clm', 'last3_p_clc', 'last3_p_cisf'
            , 'last3_p_cissc', 'last3_p_cisbs', 'last3_c_db', 'last3_c_dbn', 'last3_c_dc', 'last3_c_ctc', 'last3_c_cbn'
            , 'last3_c_cc', 'last3_i_dim', 'last3_i_dic', 'last3_i_dsim', 'last3_i_dsic', 'last3_i_bm', 'last3_i_crm'
            , 'last3_i_crc', 'last6_p_dom', 'last6_p_doc', 'last6_p_dnom', 'last6_p_dnoc', 'last6_p_dcm', 'last6_p_dcc'
            , 'last6_p_dlrm', 'last6_p_dlrc', 'last6_p_docm', 'last6_p_docc', 'last6_p_dsom', 'last6_p_dsoc', 'last6_p_dcrm'
            , 'last6_p_dcrc', 'last6_p_dim', 'last6_p_dic', 'last6_p_com', 'last6_p_coc', 'last6_p_cnom', 'last6_p_cnoc'
            , 'last6_p_ccm', 'last6_p_ccc', 'last6_p_cocm', 'last6_p_cocc', 'last6_p_csom', 'last6_p_csoc', 'last6_p_ccrm'
            , 'last6_p_ccrc', 'last6_p_clm', 'last6_p_clc', 'last6_p_cisf', 'last6_p_cissc', 'last6_p_cisbs', 'last6_c_db'
            , 'last6_c_dbn', 'last6_c_dc', 'last6_c_ctc', 'last6_c_cbn', 'last6_c_cc', 'last6_i_dim', 'last6_i_dic'
            , 'last6_i_dsim', 'last6_i_dsic', 'last6_i_bm', 'last6_i_crm', 'last6_i_crc', 'message', 'costTime']
        return results, head

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "code":data["code"], "message":data["message"]})
            if 'data' in data.keys() and data['data']:
                for key1 in data['data']:
                    if key1 == 'last_1':
                        if 'p' in data['data']['last_1'].keys():
                            for key2,val in data['data']['last_1']['p'].items():
                                result.update({'last1_'+key2: val})
                        if 'c' in data['data']['last_1'].keys():
                            for key2,val in data['data']['last_1']['c'].items():
                                result.update({'last1_'+key2: val})
                        if 'i' in data['data']['last_1'].keys():
                            for key2,val in data['data']['last_1']['i'].items():
                                result.update({'last1_'+key2: val})
                    if key1 == 'last_3':
                        if 'p' in data['data']['last_3'].keys():
                            for key2,val in data['data']['last_3']['p'].items():
                                result.update({'last3_'+key2: val})
                        if 'c' in data['data']['last_3'].keys():
                            for key2,val in data['data']['last_3']['c'].items():
                                result.update({'last3_'+key2: val})
                        if 'i' in data['data']['last_3'].keys():
                            for key2,val in data['data']['last_3']['i'].items():
                                result.update({'last3_'+key2: val})
                    if key1 == 'last_6':
                        if 'p' in data['data']['last_6'].keys():
                            for key2,val in data['data']['last_6']['p'].items():
                                result.update({'last6_'+key2: val})
                        if 'c' in data['data']['last_6'].keys():
                            for key2,val in data['data']['last_6']['c'].items():
                                result.update({'last6_'+key2: val})
                        if 'i' in data['data']['last_6'].keys():
                            for key2,val in data['data']['last_6']['i'].items():
                                result.update({'last6_'+key2: val})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, head = IceRJH.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceSYSFZ(IceLD):
    '''sy_身份证二要素验证（海纳）'''
    def __init__(self, *args):
        super(IceSYSFZ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'idCard': '211224199311137913',
            'name': u'王强',
            'client_type':'100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceSYSFZ mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'idCard': line['id'],
                            'name': line['name'],
                            'client_type': '100002',
                            'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceSYSFZ.transform(data, outdata[idx])
            results.append(result)
        head = ["msg", "birthday", "gender", "photo_base64", "region", "result", "costTime"]
        return results, head

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "msg":data["msg"]})
            if 'result' in data.keys() and data["result"]:
                result.update({"result": data['result']['result'], "gender": data['result']['gender']})
                if data['result']['result'] == "1":
                    result.update({"birthday": data['result']['birthday'], "photo_base64": data['result']['photo_base64'], "region": data['result']['region']})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, head = IceSYSFZ.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceQYMHCX(IceLD):
    '''企业关键字模糊查询（海纳）'''
    def __init__(self, *args):
        super(IceQYMHCX, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'client_type':'100002',
            'swift_number': swift_number,
            'keyword': '（百融）'}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceQYMHCX mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'keyword': line['other_var5'],
                            'client_type': '100002',
                            'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        for idx, data in enumerate(datas):
            result = IceQYMHCX.transform(data, outdata[idx])
            results.append(result)
            for key in result.keys():
                heads.append(key)
            heads = list(set(heads))

        head_sort = ["KeyNo_", "Name_","OperName_","StartDate_","Status_","No_"]
        headed_sort = []
        for i in range(1,11):
            list1 = []
            headed = []
            for j in heads:
                if str(i) in j:
                    list1.append(j)

            print list1, 'list1'

            for k in head_sort:
                if k+str(i) in list1:
                    headed.append(k+str(i))

            headed_sort = headed_sort + headed
        headed_sort = ['Sys_Status', 'Message'] + headed_sort + ['costTime']
        return results, headed_sort

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "Sys_Status":data["Status"], "Message":data["Message"]})
            if 'Result' in data.keys() and data["Result"]:
                num = 1
                for val in data['Result']:
                    result.update({"KeyNo_"+str(num): val['KeyNo'], "Name_"+str(num): val['Name'], "OperName_"+str(num): val['OperName'], "StartDate_"+str(num): val['StartDate'], "Status_"+str(num): val['Status'], "No_"+str(num): val['No']})
                    num = num + 1
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, head = IceQYMHCX.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceQCCDWTZ(IceLD):
    '''企业关键字模糊查询（海纳）'''
    def __init__(self, *args):
        super(IceQCCDWTZ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'client_type':'100002',
            'swift_number': swift_number,
            'idNum': '512531196407046379'}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceQCCDWTZ mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'idNum': line['id'],
                            'client_type': '100002',
                            'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        heads = []
        for idx, data in enumerate(datas):
            result = IceQCCDWTZ.transform(data, outdata[idx])
            results.append(result)
            for key in result.keys():
                heads.append(key)
            heads = list(set(heads))

        head_sort = ['PB_CaseCode', 'PB_Name', 'PB_Type', 'PB_Sex', 'PB_Age', 'PB_CardNum', 'PB_Ysfzd', 'PB_BusinessEntity'
            , 'PB_RegDateClean', 'PB_PublishDateClean', 'PB_CourtName', 'PB_AreaNameClean', 'PB_GistId', 'PB_GistUnit'
            , 'PB_Duty', 'PB_DisruptTypeName', 'PB_Performance', 'PB_PerformedPart', 'PB_UnperformPart', 'PB_FocusNumber'
            , 'P_Name', 'P_RegDateClean', 'P_CourtName', 'P_ExecMoney', 'P_CaseNo', 'P_Sex', 'P_Age', 'P_CardNum'
            , 'P_IdentityDeparture', 'P_Province', 'P_FocusNumber', 'P_CaseStatus', 'RPS_RyName', 'RPS_EntName'
            , 'RPS_RegNo', 'RPS_EntType', 'RPS_RegCap', 'RPS_RegCapCur', 'RPS_EntStatus', 'RPS_SubConAmt', 'RPS_Currency'
            , 'RPP_RyName', 'RPP_EntName', 'RPP_RegNo', 'RPP_EntType', 'RPP_RegCap', 'RPP_RegCapCur', 'RPP_EntStatus'
            , 'RPP_Position', 'RPF_RyName', 'RPF_EntName', 'RPF_RegNo', 'RPF_EntType', 'RPF_RegCap', 'RPF_RegCapCur', 'RPF_EntStatus']
        headed_sort = []
        for i in range(1,11):
            list1 = []
            headed = []
            for j in heads:
                if str(i) in j:
                    list1.append(j)

            for k in head_sort:
                if k+str(i) in list1:
                    headed.append(k+str(i))

            headed_sort = headed_sort + headed
        headed_sort = ['Api_Status', 'Message'] + headed_sort + ['costTime']
        return results, headed_sort

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "Api_Status":data["Status"], "Message":data["Message"]})
            if 'Result' in data.keys() and data["Result"]:
                for i in data['Result']:
                    if i == 'PunishBreakInfoList' and data['Result'][i]:
                        num = 1
                        for j in data['Result'][i]:
                            for k,v in j.items():
                                result.update({'PB_'+k+str(num):v})
                            num = num + 1
                    if i == 'PunishedInfoList' and data['Result'][i]:
                        num = 1
                        for j in data['Result'][i]:
                            for k,v in j.items():
                                result.update({'P_'+k+str(num):v})
                            num = num + 1
                    if i == 'RyPosShaInfoList' and data['Result'][i]:
                        num = 1
                        for j in data['Result'][i]:
                            for k,v in j.items():
                                result.update({'RPS_'+k+str(num):v})
                            result.pop('RPS_ConForm'+str(num))
                            result.pop('RPS_FundedRatio'+str(num))
                            num = num + 1
                    if i == 'RyPosPerInfoList' and data['Result'][i]:
                        num = 1
                        for j in data['Result'][i]:
                            for k,v in j.items():
                                result.update({'RPP_'+k+str(num):v})
                            num = num + 1
                    if i == 'RyPosFrInfoList' and data['Result'][i]:
                        num = 1
                        for j in data['Result'][i]:
                            for k,v in j.items():
                                result.update({'RPF_'+k+str(num):v})
                            num = num + 1
        print result.keys(),'result.keys'
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, head = IceQCCDWTZ.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                for key in row.keys():
                    if key not in headers:
                        row.pop(key)
                csvfile.writerow(row)
            except:
                errlog.error('IceQCCDWTZ write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceXZ(IceLD):
    '''sy_身份证二要素验证（海纳）'''
    def __init__(self, *args):
        super(IceXZ, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'phone': '15123934043',
            'client_type': '100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceXZ mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            if select in ['xz_sjzwzt', 'xz_sjzwsc']:
                user_info = dict({'phone': line['cell'].strip(),
                                'client_type': '100002',
                                'swift_number': swift_number})
            else:
                user_info = dict({'phone': line['cell'].strip(),
                                'idcard': line['id'],
                                'name': line['name'],
                                'client_type': '100002',
                                'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceXZ.transform(data, outdata[idx])
            results.append(result)
        return results

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "msg":data["errorMsg"], "code":data['code']})
            if 'data' in data.keys() and data["data"]:
                if 'type' in data['data']:
                    result.update({"type":data['data']['type']})
                if 'inTimes' in data['data']:
                    result.update({"period":data['data']['inTimes']})
                if 'compareResult' in data['data']:
                    result.update({"result":data['data']['compareResult']})
                if 'mdnState' in data['data']:
                    result.update({"state":data['data']['mdnState']})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results= IceXZ.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)

        if select == 'xz_sjzwzt':
            head = ['code', 'msg', 'type', 'state', 'costTime']
        elif select == 'xz_sjzwsc':
            head = ['code', 'msg', 'type', 'period', 'costTime']
        else:
            head = ['code', 'msg', 'type', 'result', 'costTime']
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()



class IceBLXXD(IceLD):
    '''sy_身份证二要素验证（海纳）'''
    def __init__(self, *args):
        super(IceBLXXD, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'param': '易方炜,452122199411250013',
            'client_type': '100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceBLXXD mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            # if line['name'].strip() and line['id'].strip():
            user_info = dict({'param': line['name'].strip()+','+line['id'].strip(),
                            'client_type': '100002',
                            'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        header = []
        heads = []
        head_sort = ['caseType', 'caseSource', 'caseTime']
        for data in datas:
            result, head = IceBLXXD.transform(data)
            results.append(result)
            header = list(set(header + head))
        
        for i in range(1,100):
            list1 = []
            headed = []
            for j in header:
                if str(i) in j:
                    list1.append(j)

            for k in head_sort:
                if k+str(i) in list1:
                    headed.append(k+str(i))
            
            heads = heads + headed
        return results, heads

    @staticmethod
    def transform(data):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "message_status":data["message"]["status"], "message_value":data['message']["value"]})
            if "#text" in data["badInfoDs"][0]["wybs"]:
                result.update({"wybs": data["badInfoDs"][0]["wybs"]["#text"]})
            else:
                result.update({"wybs": ''})
            if "#text" in data["badInfoDs"][0]["code"]:
                result.update({"status": data["badInfoDs"][0]["code"]["#text"]})
            else:
                result.update({"status": ''})
            if "#text" in data["badInfoDs"][0]["message"]:
                result.update({"value": data["badInfoDs"][0]["message"]["#text"]})
            else:
                result.update({"value": ''})
            if "#text" in data["badInfoDs"][0]["checkCode"]:
                result.update({"checkCode": data["badInfoDs"][0]["checkCode"]["#text"]})
            else:
                result.update({"checkCode": ''})
            if "#text" in data["badInfoDs"][0]["checkMsg"]:
                result.update({"checkMsg": data["badInfoDs"][0]["checkMsg"]["#text"]})
            else:
                result.update({"checkMsg": ''})
            if data["badInfoDs"][0]["item"]:
                if isinstance(data["badInfoDs"][0]["item"], list):
                    num = 1
                    for val in data["badInfoDs"][0]["item"]:
                        if len(val["caseType"]) == 2:
                            result.update({"caseType"+str(num): val["caseType"]["#text"]})
                        else:
                            result.update({"caseType"+str(num): ''})
                        if len(val["caseTime"]) == 2:
                            result.update({"caseTime"+str(num): val["caseTime"]["#text"]})
                        else:
                            result.update({"caseTime"+str(num): ''})
                        if len(val["caseSource"]) == 2:
                            result.update({"caseSource"+str(num): val['caseSource']["#text"]})
                        else:
                            result.update({'caseSource'+str(num): ''})
                        num = num + 1
                if isinstance(data["badInfoDs"][0]["item"], dict):
                    if len(data["badInfoDs"][0]["item"]["caseType"]) == 2:
                        result.update({"caseType1": data["badInfoDs"][0]["item"]["caseType"]["#text"]})
                    else:
                        result.update({"caseType1": ''})
                    if len(data["badInfoDs"][0]["item"]["caseTime"]) == 2:
                        result.update({"caseTime1": data["badInfoDs"][0]["item"]["caseTime"]["#text"]})
                    else:
                        result.update({"caseTime1": ''})
                    if len(data["badInfoDs"][0]["item"]["caseSource"]) == 2:
                        result.update({"caseSource1": data["badInfoDs"][0]["item"]['caseSource']["#text"]})
                    else:
                        result.update({"caseSource1": ""})

                    
        if isinstance(data, list):
            result.update({"message_status":data[0]["status"], "message_value":data[0]["value"]})
        return result, result.keys()

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results, head = IceBLXXD.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)

        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + ["message_status", "message_value", "wybs", "status", "value", "checkCode"\
            , "checkMsg"] + head + ["costTime"]
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceZYHL(IceLD):
    '''sy_身份证二要素验证（海纳）'''
    def __init__(self, *args):
        super(IceZYHL, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'phone': '15123934043',
            'queryid':'0000000100000',
            'client_type': '100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select[:-1]))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceZYHL mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select[:-1]))
            if select == "zyhl_ydsj1":
                user_info = dict({'phone': line['cell'].strip(),
                                'queryid': '0000000000001',
                                'client_type': '100002',
                                'swift_number': swift_number})
            elif select == "zyhl_ydsj2":
                user_info = dict({'phone': line['cell'].strip(),
                                'queryid': '0000000100000',
                                'client_type': '100002',
                                'swift_number': swift_number})
            else:
                user_info = dict({'phone': line['cell'].strip(),
                                'queryid': '0000010000000',
                                'client_type': '100002',
                                'swift_number': swift_number})
            query_info_list.append((user_info, select[:-1]))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata, select):
        results = []
        for idx, data in enumerate(datas):
            result = IceZYHL.transform(data, outdata[idx], select)
            results.append(result)
        return results

    @staticmethod
    def transform(data, outdata, select):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime']})
            if 'ServResult' in data.keys():
                if select == 'zyhl_ydsj1':
                    for obj in data['ServResult']:
                        if obj['Name'] == 'OnNetState':
                            result.update({'value': obj['AttrList']['Value'], 'isvalid': obj['AttrList']['IsValid']})
                elif select == 'zyhl_ydsj2':
                    for obj in data['ServResult']:
                        if obj['Name'] == 'ARPU':
                            result.update({'value': obj['AttrList']['Value'], 'isvalid': obj['AttrList']['IsValid']})
                else:
                    for obj in data['ServResult']:
                        if obj['Name'] == 'OnNetTime':
                            result.update({'value': obj['AttrList']['Value'], 'isvalid': obj['AttrList']['IsValid']})

        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results= IceZYHL.transforms(results, outdata, select)
        results = self.linklist(results, fileid, fields_rel)
        head = ['value', 'isvalid', 'costTime']
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()


class IceFY(IceLD):
    '''sy_身份证二要素验证（海纳）'''
    def __init__(self, *args):
        super(IceFY, self).__init__(*args)
        self.apicode = args[1]

    def check_ice(self, modal, select):
        swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
        info = {'mobile': '15123934043',
            'name': '唐宁助',
            'client_type': '100002',
            'swift_number': swift_number}
        ret = self.dataice.get_data((info, select))
        if ret:
            try:
                ret = json.loads(ret)
            except ValueError:
                errlog.error('here  IceFY mapping :'+ traceback.format_exc())
                ret = False
            else:ret = True
        return ret

    def generate_query_infos(self, select, fields, fields_rel, modal):
        query_info_list = []
        query_info_list2 = []
        data_txt = []
        user_data = self.filereader.read_user_data(fields)
        user_dict_list = self.filereader.tansform_user_data(user_data, fields, fields_rel)
        self.user_dict_list = user_dict_list
        for line in user_dict_list:
            swift_number = self.apicode + "_" + time.strftime('%Y%m%d%H%M%S') + "_" + str(random.randint(1000,9999))
            line.update({'swift_number': swift_number})
            data_txt.append((json.dumps(line), select))
            user_info = dict({'mobile': line['cell'].strip(),
                        'name': line['name'].strip(),
                        'client_type': '100002',
                        'swift_number': swift_number})
            query_info_list.append((user_info, select))
        return query_info_list, data_txt

    def query_ice_data(self, info_list, data_txt, select):
        interface = Interface.objects.get(name=select)
        thread_num = interface.thread_num
        pool = ThreadPool(thread_num)
        results_json = pool.map(self.dataice.get_data, info_list)
        pool.close()
        pool.join()
        results = []
        for i in results_json:
            if i!=None:
                try:
                    result = json.loads(i)
                except ValueError:
                    result = None
            else:result = None
            results.append(result)
        list_txt = zip(data_txt,results)
        return results, list_txt

    @staticmethod
    def transforms(datas, outdata):
        results = []
        for idx, data in enumerate(datas):
            result = IceFY.transform(data, outdata[idx])
            results.append(result)
        return results

    @staticmethod
    def transform(data, outdata):
        result = {}
        if isinstance(data, dict):
            result.update({"costTime":data['costTime'], "msg":data["msg"], "result":data['result']})
        return result

    def linklist(self, results, fileid, fields_rel):
        ret_list = []
        offset = self.filereader.startline + 1
        for idx, data in enumerate(self.user_dict_list):
            openid = 'br%06d%07d' % (fileid, idx+offset)
            ret = dict(data.items() + results[idx].items())
            ret.update({'openid': openid})
            ret_list.append(ret)
        return ret_list

    def process_result(self, results, fileid, fields, fields_rel, modal, select):
        outdata = self.user_dict_list
        results= IceFY.transforms(results, outdata)
        results = self.linklist(results, fileid, fields_rel)
        head = ['msg', 'result', 'costTime']
        OUT_CSV_FM_RL = ['openid', 'swift_number'] + fields + head
        return OUT_CSV_FM_RL, results

    def write_to_csv(self, filename, headers, lines, crypt=False):
        f = open(filename,'wb')
        f.write(u'\ufeff'.encode('utf-8'))
        csvfile = csv.DictWriter(f,headers, delimiter=',')
        csvfile.writeheader()
        for row in lines:
            try:
                if crypt:
                    row = util.crypt_row(row,headers)
                if 'querymonth' in row.keys():
                    user_date = row.pop('querymonth')
                    row.update({'user_date': user_date})
                if 'mobiles' in row.keys():
                    row.pop('mobiles')
                csvfile.writerow(row)
            except:
                errlog.error('dd write csv wrong : '+ traceback.format_exc())
                continue
        f.close()









CLWZ_CSV_HEAD = ['Time',
'Location',
'Reason',
'count',
'status',
'department',
'Degree',
'Code',
'Archive',
'Telephone',
'Excutelocation',
'Excutedepartment',
'Category',
'Latefine',
'Punishmentaccording',
'Illegalentry',
'Locationid',
'LocationName',
'DataSourceID',
'RecordType',
'Poundage',
'CanProcess',
'SecondaryUniqueCode',
'UniqueCode',
'DegreePoundage',
'CanprocessMsg',
'Other']


QYJB_CSV_HEAD =['resCode',
'resMsg',
'orderNo',
'entName',
'frName',
'regNo',
'regCap',
'regCapCur',
'esDate',
'opFrom',
'opTo',
'entType',
'entStatus',
'canDate',
'revDate',
'dom',
'abuItem',
'cbuItem',
'opScope',
'opScoAndForm',
'regOrg',
'anCheYear',
'anCheDate',
'industryPhyCode',
'orgNo',
'administrativeDivisionCode',
'phone',
'postalCode',
'staffNum',
'authorityName',
'authorityCode',
'orgNoStartDate',
'orgNoEndDate',
'result',
'industryCoCode',
'message']


PERSONCASEINFO = ['PERSONCASEINFO_NAME',
'PERSONCASEINFO_CERNO',
'PERSONCASEINFO_CASETIME',
'PERSONCASEINFO_CASEREASON',
'PERSONCASEINFO_CASEVAL',
'PERSONCASEINFO_CASETYPE',
'PERSONCASEINFO_EXESORT',
'PERSONCASEINFO_CASERESULT',
'PERSONCASEINFO_PENDECNO',
'PERSONCASEINFO_PENDECISSDATE',
'PERSONCASEINFO_PENAUTH',
'PERSONCASEINFO_ILLEGFACT',
'PERSONCASEINFO_PENBASIS',
'PERSONCASEINFO_PENTYPE',
'PERSONCASEINFO_PENRESULT',
'PERSONCASEINFO_PENAM',
'PERSONCASEINFO_PENEXEST']


RYPOSPER = ['RYPOSPER_RYNAME',
'RYPOSPER_ENTNAME',
'RYPOSPER_REGNO',
'RYPOSPER_ENTTYPE',
'RYPOSPER_REGCAP',
'RYPOSPER_REGCAPCUR',
'RYPOSPER_ENTSTATUS',
'RYPOSPER_POSITION']


RYPOSSHA = ['RYPOSSHA_RYNAME',
'RYPOSSHA_ENTNAME',
'RYPOSSHA_REGNO',
'RYPOSSHA_ENTTYPE',
'RYPOSSHA_REGCAP',
'RYPOSSHA_REGCAPCUR',
'RYPOSSHA_SUBCONAM',
'RYPOSSHA_CURRENCY',
'RYPOSSHA_CONFORM',
'RYPOSSHA_FUNDEDRATIO',
'RYPOSSHA_ENTSTATUS']


RYPOSFR = ['RYPOSFR_RYNAME',
'RYPOSFR_ENTNAME',
'RYPOSFR_REGNO',
'RYPOSFR_ENTTYPE',
'RYPOSFR_REGCAP',
'RYPOSFR_REGCAPCUR',
'RYPOSFR_ENTSTATUS']


RL_FIELD_LIST = ['flag_facial_recognition',
'facial_recognition_id',
'facial_recognition_name',
'facial_recognition_result',
'facial_recognition_similarity']


QY_FILE_LIST_ID = ['per_id',
'per_status',
'per_idtype',
'per_finishtime',
'per_name']

QY_FILE_LIST_NAME = ['ent_name',
'ent_nametype',
'ent_status',
'ent_finishtime',
'bas_ent',
'bas_legrep',
'bas_regno',
'bas_oriregno',
'bas_regcap',
'bas_reccap',
'bas_regcapcur',
'bas_esdate',
'bas_opfrom',
'bas_opto',
'bas_enttype',
'bas_entstatus',
'bas_chadate',
'bas_candate',
'bas_revdate',
'bas_addr',
'bas_abuitem',
'bas_cbuitem',
'bas_opscope',
'bas_opscoandform',
'bas_regorg',
'bas_ancheyear',
'bas_anchedate',
'bas_indphycode',
'bas_indphyname',
'bas_indcocode',
'bas_indconame']


BCHX_FIEL_LIST = ['flag_pf',
'pf_cardactive',
'pf_pos_m12_paylist',
'pf_pos_m12_numlist',
'pf_m3_pay_citylist',
'pf_m3_num_citylist',
'pf_bank_m6_tran_num',
'pf_bank_m6_tran_amt',
'pf_bank_m6_in_amt',
'pf_bank_m6_in_num',
'pf_bank_m12_cash_amtlist',
'pf_bank_m12_cash_numlist',
'pf_bank_m6_bigtran_amt',
'pf_bank_m6_bigtran_num',
'pf_bank_m6_midtran_amt',
'pf_bank_m6_midtran_num',
'pf_bank_m6_bigin_amt',
'pf_m6_tran_bigin_pct',
'pf_m6_cash_bigin_pct',
'pf_m6_pos_bigin_pct',
'pf_pos_m12_top5amt_list',
'pf_m12_bigamt_bizlist',
'pf_m12_mcc_paylist',
'pf_m12_mcc_numlist',
'pf_m12_echannel_list']


JZD_FIEL_LIST = ['code',
'id',
'date',
'at_name',
'at_arr_cty_total',
'at_num_2016Q3',
'at_first_2016Q3',
'at_business_2016Q3',
'at_economy_2016Q3',
'at_dom_2016Q3',
'at_arr_cty_2016Q3',
'at_num_2016Q2',
'at_first_2016Q2',
'at_business_2016Q2',
'at_economy_2016Q2',
'at_dom_2016Q2',
'at_arr_cty_2016Q2',
'at_num_2016Q1',
'at_first_2016Q1',
'at_business_2016Q1',
'at_economy_2016Q1',
'at_dom_2016Q1',
'at_arr_cty_2016Q1',
'at_num_2015Q4',
'at_first_2015Q4',
'at_business_2015Q4',
'at_economy_2015Q4',
'at_dom_2015Q4',
'at_arr_cty_2015Q4',
'at_num_2015Q3',
'at_first_2015Q3',
'at_business_2015Q3',
'at_economy_2015Q3',
'at_dom_2015Q3',
'at_arr_cty_2015Q3',
'at_num_2015Q2',
'at_first_2015Q2',
'at_business_2015Q2',
'at_economy_2015Q2',
'at_dom_2015Q2',
'at_arr_cty_2015Q2',
'at_num_2015Q1',
'at_first_2015Q1',
'at_business_2015Q1',
'at_economy_2015Q1',
'at_dom_2015Q1',
'at_arr_cty_2015Q1',
'at_num_2014Q4',
'at_first_2014Q4',
'at_business_2014Q4',
'at_economy_2014Q4',
'at_dom_2014Q4',
'at_arr_cty_2014Q4',
'at_num_2014Q3',
'at_first_2014Q3',
'at_business_2014Q3',
'at_economy_2014Q3',
'at_dom_2014Q3',
'at_arr_cty_2014Q3',
'at_num_2014Q2',
'at_first_2014Q2',
'at_business_2014Q2',
'at_economy_2014Q2',
'at_dom_2014Q2',
'at_arr_cty_2014Q2',
'at_num_2014Q1',
'at_first_2014Q1',
'at_business_2014Q1',
'at_economy_2014Q1',
'at_dom_2014Q1',
'at_arr_cty_2014Q1',
'at_num_2013Q4',
'at_first_2013Q4',
'at_business_2013Q4',
'at_economy_2013Q4',
'at_dom_2013Q4',
'at_arr_cty_2013Q4',
'at_num_2013Q3',
'at_first_2013Q3',
'at_business_2013Q3',
'at_economy_2013Q3',
'at_dom_2013Q3',
'at_arr_cty_2013Q3',
'at_num_2013Q2',
'at_first_2013Q2',
'at_business_2013Q2',
'at_economy_2013Q2',
'at_dom_2013Q2',
'at_arr_cty_2013Q2',
'at_num_2013Q1',
'at_first_2013Q1',
'at_business_2013Q1',
'at_economy_2013Q1',
'at_dom_2013Q1',
'at_arr_cty_2013Q1',
'at_num_2012Q4',
'at_first_2012Q4',
'at_business_2012Q4',
'at_economy_2012Q4',
'at_dom_2012Q4',
'at_arr_cty_2012Q4']


SRC_FIELD_LIST = ['regionno',
                'mobileid',
                'bank_pf_ind',
                'bank_zs_ind',
                'bank_gs_ind',
                'bank_js_ind',
                'bank_pa_ind',
                'bank_zsx_ind',
                'card_cnt',
                'deposit_outgo_m16_m18',
                'deposit_outgo_m13_m15',
                'deposit_outgo_m10_m12',
                'deposit_outgo_m7_m9',
                'deposit_outgo_m4_m6',
                'deposit_outgo_m1_m3',
                'deposit_income_m16_m18',
                'deposit_income_m13_m15',
                'deposit_income_m10_m12',
                'deposit_income_m7_m9',
                'deposit_income_m4_m6',
                'deposit_income_m1_m3',
                'deposit_repay_m16_m18',
                'deposit_repay_m13_m15',
                'deposit_repay_m10_m12',
                'deposit_repay_m7_m9',
                'deposit_repay_m4_m6',
                'deposit_repay_m1_m3',
                'deposit_invest_m16_m18',
                'deposit_invest_m13_m15',
                'deposit_invest_m10_m12',
                'deposit_invest_m7_m9',
                'deposit_invest_m4_m6',
                'deposit_invest_m1_m3',
                'credit_outgo_m16_m18',
                'credit_outgo_m13_m15',
                'credit_outgo_m10_m12',
                'credit_outgo_m7_m9',
                'credit_outgo_m4_m6',
                'credit_outgo_m1_m3',
                'credit_cash_out_m16_m18',
                'credit_cash_out_m13_m15',
                'credit_cash_out_m10_m12',
                'credit_cash_out_m7_m9',
                'credit_cash_out_m4_m6',
                'credit_cash_out_m1_m3',
                'credit_income_m16_m18',
                'credit_income_m13_m15',
                'credit_income_m10_m12',
                'credit_income_m7_m9',
                'credit_income_m4_m6',
                'credit_income_m1_m3',
                'balance_m16_m18',
                'balance_m13_m15',
                'balance_m10_m12',
                'balance_m7_m9',
                'balance_m4_m6',
                'balance_m1_m3',
                'bill_if_pay_all_m16_m18',
                'bill_if_pay_all_m13_m15',
                'bill_if_pay_all_m10_m12',
                'bill_if_pay_all_m7_m9',
                'bill_if_pay_all_m4_m6',
                'bill_if_pay_all_m1_m3',
                'credit_card_status_m16_m18',
                'credit_card_status_m13_m15',
                'credit_card_status_m10_m12',
                'credit_card_status_m7_m9',
                'credit_card_status_m4_m6',
                'credit_card_status_m1_m3',
                'loan_amt_m16_m18',
                'loan_amt_m13_m15',
                'loan_amt_m10_m12',
                'loan_amt_m7_m9',
                'loan_amt_m4_m6',
                'loan_amt_m1_m3',
                'if_pay_ontime_m16_m18',
                'if_pay_ontime_m13_m15',
                'if_pay_ontime_m10_m12',
                'if_pay_ontime_m7_m9',
                'if_pay_ontime_m4_m6',
                'if_pay_ontime_m1_m3',
                'hf_balance',
                'hf_acc_date',
                'hf_bal_sign',
                'hf_user_status',
                'hf_auth_date']


LD_LIST_NEW = ['flag_accountChange',
'ac_regionno',
# 'mobile',
'bank_pf_ind',
'bank_js_ind',
'bank_zs_ind',
'bank_zg_ind',
'bank_gs_ind',
'bank_xy_ind',
'bank_pa_ind',
'bank_zsx_ind',
'bank_jt_ind',
'card_index',
'ac_m1_debit_balance',
'ac_m1_debit_out',
'ac_m1_debit_out_num',
'ac_m1_debit_invest',
'ac_m1_debit_repay',
'ac_m1_debit_in',
'ac_m1_debit_in_num',
'ac_m1_credit_out',
'ac_m1_credit_out_num',
'ac_m1_credit_cash',
'ac_m1_credit_in',
'ac_m1_credit_in_num',
'ac_m1_credit_def',
'ac_m1_loan',
'ac_m1_credit_status',
'ac_m1_cons',
'ac_m1_max_in',
'ac_m2_debit_balance',
'ac_m2_debit_out',
'ac_m2_debit_out_num',
'ac_m2_debit_invest',
'ac_m2_debit_repay',
'ac_m2_debit_in',
'ac_m2_debit_in_num',
'ac_m2_credit_out',
'ac_m2_credit_out_num',
'ac_m2_credit_cash',
'ac_m2_credit_in',
'ac_m2_credit_in_num',
'ac_m2_credit_def',
'ac_m2_loan',
'ac_m2_credit_status',
'ac_m2_cons',
'ac_m2_max_in',
'ac_m3_debit_balance',
'ac_m3_debit_out',
'ac_m3_debit_out_num',
'ac_m3_debit_invest',
'ac_m3_debit_repay',
'ac_m3_debit_in',
'ac_m3_debit_in_num',
'ac_m3_credit_out',
'ac_m3_credit_out_num',
'ac_m3_credit_cash',
'ac_m3_credit_in',
'ac_m3_credit_in_num',
'ac_m3_credit_def',
'ac_m3_loan',
'ac_m3_credit_status',
'ac_m3_cons',
'ac_m3_max_in',
'ac_m4_debit_balance',
'ac_m4_debit_out',
'ac_m4_debit_out_num',
'ac_m4_debit_invest',
'ac_m4_debit_repay',
'ac_m4_debit_in',
'ac_m4_debit_in_num',
'ac_m4_credit_out',
'ac_m4_credit_out_num',
'ac_m4_credit_cash',
'ac_m4_credit_in',
'ac_m4_credit_in_num',
'ac_m4_credit_def',
'ac_m4_loan',
'ac_m4_credit_status',
'ac_m4_cons',
'ac_m4_max_in',
'ac_m5_debit_balance',
'ac_m5_debit_out',
'ac_m5_debit_out_num',
'ac_m5_debit_invest',
'ac_m5_debit_repay',
'ac_m5_debit_in',
'ac_m5_debit_in_num',
'ac_m5_credit_out',
'ac_m5_credit_out_num',
'ac_m5_credit_cash',
'ac_m5_credit_in',
'ac_m5_credit_in_num',
'ac_m5_credit_def',
'ac_m5_loan',
'ac_m5_credit_status',
'ac_m5_cons',
'ac_m5_max_in',
'ac_m6_debit_balance',
'ac_m6_debit_out',
'ac_m6_debit_out_num',
'ac_m6_debit_invest',
'ac_m6_debit_repay',
'ac_m6_debit_in',
'ac_m6_debit_in_num',
'ac_m6_credit_out',
'ac_m6_credit_out_num',
'ac_m6_credit_cash',
'ac_m6_credit_in',
'ac_m6_credit_in_num',
'ac_m6_credit_def',
'ac_m6_loan',
'ac_m6_credit_status',
'ac_m6_cons',
'ac_m6_max_in',
'ac_m1m3_debit_balance',
'ac_m1m3_debit_out',
'ac_m1m3_debit_out_num',
'ac_m1m3_debit_invest',
'ac_m1m3_debit_repay',
'ac_m1m3_debit_in',
'ac_m1m3_debit_in_num',
'ac_m1m3_credit_out',
'ac_m1m3_credit_out_num',
'ac_m1m3_credit_cash',
'ac_m1m3_credit_in',
'ac_m1m3_credit_in_num',
'ac_m1m3_credit_def',
'ac_m1m3_loan',
'ac_m1m3_credit_status',
'ac_m1m3_cons',
'ac_m1m3_max_in',
'ac_m4m6_debit_balance',
'ac_m4m6_debit_out',
'ac_m4m6_debit_out_num',
'ac_m4m6_debit_invest',
'ac_m4m6_debit_repay',
'ac_m4m6_debit_in',
'ac_m4m6_debit_in_num',
'ac_m4m6_credit_out',
'ac_m4m6_credit_out_num',
'ac_m4m6_credit_cash',
'ac_m4m6_credit_in',
'ac_m4m6_credit_in_num',
'ac_m4m6_credit_def',
'ac_m4m6_loan',
'ac_m4m6_credit_status',
'ac_m4m6_cons',
'ac_m4m6_max_in',
'ac_m7m9_debit_balance',
'ac_m7m9_debit_out',
'ac_m7m9_debit_out_num',
'ac_m7m9_debit_invest',
'ac_m7m9_debit_repay',
'ac_m7m9_debit_in',
'ac_m7m9_debit_in_num',
'ac_m7m9_credit_out',
'ac_m7m9_credit_out_num',
'ac_m7m9_credit_cash',
'ac_m7m9_credit_in',
'ac_m7m9_credit_in_num',
'ac_m7m9_credit_def',
'ac_m7m9_loan',
'ac_m7m9_credit_status',
'ac_m7m9_cons',
'ac_m7m9_max_in',
'ac_m10m12_debit_balance',
'ac_m10m12_debit_out',
'ac_m10m12_debit_out_num',
'ac_m10m12_debit_invest',
'ac_m10m12_debit_repay',
'ac_m10m12_debit_in',
'ac_m10m12_debit_in_num',
'ac_m10m12_credit_out',
'ac_m10m12_credit_out_num',
'ac_m10m12_credit_cash',
'ac_m10m12_credit_in',
'ac_m10m12_credit_in_num',
'ac_m10m12_credit_def',
'ac_m10m12_loan',
'ac_m10m12_credit_status',
'ac_m10m12_cons',
'ac_m10m12_max_in',
'ac_m13m15_debit_balance',
'ac_m13m15_debit_out',
'ac_m13m15_debit_out_num',
'ac_m13m15_debit_invest',
'ac_m13m15_debit_repay',
'ac_m13m15_debit_in',
'ac_m13m15_debit_in_num',
'ac_m13m15_credit_out',
'ac_m13m15_credit_out_num',
'ac_m13m15_credit_cash',
'ac_m13m15_credit_in',
'ac_m13m15_credit_in_num',
'ac_m13m15_credit_def',
'ac_m13m15_loan',
'ac_m13m15_credit_status',
'ac_m13m15_cons',
'ac_m13m15_max_in',
'ac_m16m18_debit_balance',
'ac_m16m18_debit_out',
'ac_m16m18_debit_out_num',
'ac_m16m18_debit_invest',
'ac_m16m18_debit_repay',
'ac_m16m18_debit_in',
'ac_m16m18_debit_in_num',
'ac_m16m18_credit_out',
'ac_m16m18_credit_out_num',
'ac_m16m18_credit_cash',
'ac_m16m18_credit_in',
'ac_m16m18_credit_in_num',
'ac_m16m18_credit_def',
'ac_m16m18_loan',
'ac_m16m18_credit_status',
'ac_m16m18_cons',
'ac_m16m18_max_in',
'hf_balance',
'hf_acc_date',
'hf_bal_sign',
'hf_user_status',
'hf_auth_date']


NEW_LD_LIST = ['flag_accountChange',
                'ac_regionno',
                'bank_pf_ind',
                'bank_js_ind',
                'bank_zs_ind',
                'bank_zg_ind',
                'bank_gs_ind',
                'bank_xy_ind',
                'bank_pa_ind',
                'bank_zsx_ind',
                'bank_jt_ind',
                'card_index',
                'ac_m1_debit_balance',
                'ac_m1_debit_out',
                'ac_m1_debit_invest',
                'ac_m1_debit_repay',
                'ac_m1_debit_in',
                'ac_m1_credit_out',
                'ac_m1_credit_cash',
                'ac_m1_credit_in',
                'ac_m1_credit_def',
                'ac_m1_loan',
                'ac_m1_credit_status',
                'ac_m2_debit_balance',
                'ac_m2_debit_out',
                'ac_m2_debit_invest',
                'ac_m2_debit_repay',
                'ac_m2_debit_in',
                'ac_m2_credit_out',
                'ac_m2_credit_cash',
                'ac_m2_credit_in',
                'ac_m2_credit_def',
                'ac_m2_loan',
                'ac_m2_credit_status',
                'ac_m3_debit_balance',
                'ac_m3_debit_out',
                'ac_m3_debit_invest',
                'ac_m3_debit_repay',
                'ac_m3_debit_in',
                'ac_m3_credit_out',
                'ac_m3_credit_cash',
                'ac_m3_credit_in',
                'ac_m3_credit_def',
                'ac_m3_loan',
                'ac_m3_credit_status',
                'ac_m4_debit_balance',
                'ac_m4_debit_out',
                'ac_m4_debit_invest',
                'ac_m4_debit_repay',
                'ac_m4_debit_in',
                'ac_m4_credit_out',
                'ac_m4_credit_cash',
                'ac_m4_credit_in',
                'ac_m4_credit_def',
                'ac_m4_loan',
                'ac_m4_credit_status',
                'ac_m5_debit_balance',
                'ac_m5_debit_out',
                'ac_m5_debit_invest',
                'ac_m5_debit_repay',
                'ac_m5_debit_in',
                'ac_m5_credit_out',
                'ac_m5_credit_cash',
                'ac_m5_credit_in',
                'ac_m5_credit_def',
                'ac_m5_loan',
                'ac_m5_credit_status',
                'ac_m6_debit_balance',
                'ac_m6_debit_out',
                'ac_m6_debit_invest',
                'ac_m6_debit_repay',
                'ac_m6_debit_in',
                'ac_m6_credit_out',
                'ac_m6_credit_cash',
                'ac_m6_credit_in',
                'ac_m6_credit_def',
                'ac_m6_loan',
                'ac_m6_credit_status',
                'ac_m1m3_debit_balance',
                'ac_m1m3_debit_out',
                'ac_m1m3_debit_invest',
                'ac_m1m3_debit_repay',
                'ac_m1m3_debit_in',
                'ac_m1m3_credit_out',
                'ac_m1m3_credit_cash',
                'ac_m1m3_credit_in',
                'ac_m1m3_credit_def',
                'ac_m1m3_loan',
                'ac_m1m3_credit_status',
                'ac_m4m6_debit_balance',
                'ac_m4m6_debit_out',
                'ac_m4m6_debit_invest',
                'ac_m4m6_debit_repay',
                'ac_m4m6_debit_in',
                'ac_m4m6_credit_out',
                'ac_m4m6_credit_cash',
                'ac_m4m6_credit_in',
                'ac_m4m6_credit_def',
                'ac_m4m6_loan',
                'ac_m4m6_credit_status',
                'ac_m7m9_debit_balance',
                'ac_m7m9_debit_out',
                'ac_m7m9_debit_invest',
                'ac_m7m9_debit_repay',
                'ac_m7m9_debit_in',
                'ac_m7m9_credit_out',
                'ac_m7m9_credit_cash',
                'ac_m7m9_credit_in',
                'ac_m7m9_credit_def',
                'ac_m7m9_loan',
                'ac_m7m9_credit_status',
                'ac_m10m12_debit_balance',
                'ac_m10m12_debit_out',
                'ac_m10m12_debit_invest',
                'ac_m10m12_debit_repay',
                'ac_m10m12_debit_in',
                'ac_m10m12_credit_out',
                'ac_m10m12_credit_cash',
                'ac_m10m12_credit_in',
                'ac_m10m12_credit_def',
                'ac_m10m12_loan',
                'ac_m10m12_credit_status',
                'ac_m13m15_debit_balance',
                'ac_m13m15_debit_out',
                'ac_m13m15_debit_invest',
                'ac_m13m15_debit_repay',
                'ac_m13m15_debit_in',
                'ac_m13m15_credit_out',
                'ac_m13m15_credit_cash',
                'ac_m13m15_credit_in',
                'ac_m13m15_credit_def',
                'ac_m13m15_loan',
                'ac_m13m15_credit_status',
                'ac_m16m18_debit_balance',
                'ac_m16m18_debit_out',
                'ac_m16m18_debit_invest',
                'ac_m16m18_debit_repay',
                'ac_m16m18_debit_in',
                'ac_m16m18_credit_out',
                'ac_m16m18_credit_cash',
                'ac_m16m18_credit_in',
                'ac_m16m18_credit_def',
                'ac_m16m18_loan',
                'ac_m16m18_credit_status',
                'hf_balance',
                'hf_acc_date',
                'hf_bal_sign',
                'hf_user_status',
                'hf_auth_date']


PC_FIELD_LIST =['flag_payConsumption',
'pc_c1_date',
'pc_thm1_pay',
'pc_thm1_num',
'pc_thm1_1st_pay_mcc',
'pc_thm1_1st_num_mcc',
'pc_thm1_2nd_pay_mcc',
'pc_thm1_2nd_num_mcc',
'pc_thm1_3rd_pay_mcc',
'pc_thm1_3rd_num_mcc',
'pc_thm1_max_num_pvn',
'pc_thm1_night_pay',
'pc_thm1_night_num',
'pc_thm2_pay',
'pc_thm2_num',
'pc_thm2_1st_pay_mcc',
'pc_thm2_1st_num_mcc',
'pc_thm2_2nd_pay_mcc',
'pc_thm2_2nd_num_mcc',
'pc_thm2_3rd_pay_mcc',
'pc_thm2_3rd_num_mcc',
'pc_thm2_max_num_pvn',
'pc_thm2_night_pay',
'pc_thm2_night_num',
'pc_thm3_pay',
'pc_thm3_num',
'pc_thm3_1st_pay_mcc',
'pc_thm3_1st_num_mcc',
'pc_thm3_2nd_pay_mcc',
'pc_thm3_2nd_num_mcc',
'pc_thm3_3rd_pay_mcc',
'pc_thm3_3rd_num_mcc',
'pc_thm3_max_num_pvn',
'pc_thm3_night_pay',
'pc_thm3_night_num',
'pc_thm4_pay',
'pc_thm4_num',
'pc_thm4_1st_pay_mcc',
'pc_thm4_1st_num_mcc',
'pc_thm4_2nd_pay_mcc',
'pc_thm4_2nd_num_mcc',
'pc_thm4_3rd_pay_mcc',
'pc_thm4_3rd_num_mcc',
'pc_thm4_max_num_pvn',
'pc_thm4_night_pay',
'pc_thm4_night_num',
'pc_thm5_pay',
'pc_thm5_num',
'pc_thm5_1st_pay_mcc',
'pc_thm5_1st_num_mcc',
'pc_thm5_2nd_pay_mcc',
'pc_thm5_2nd_num_mcc',
'pc_thm5_3rd_pay_mcc',
'pc_thm5_3rd_num_mcc',
'pc_thm5_max_num_pvn',
'pc_thm5_night_pay',
'pc_thm5_night_num',
'pc_thm6_pay',
'pc_thm6_num',
'pc_thm6_1st_pay_mcc',
'pc_thm6_1st_num_mcc',
'pc_thm6_2nd_pay_mcc',
'pc_thm6_2nd_num_mcc',
'pc_thm6_3rd_pay_mcc',
'pc_thm6_3rd_num_mcc',
'pc_thm6_max_num_pvn',
'pc_thm6_night_pay',
'pc_thm6_night_num',
'pc_thm7_pay',
'pc_thm7_num',
'pc_thm7_1st_pay_mcc',
'pc_thm7_1st_num_mcc',
'pc_thm7_2nd_pay_mcc',
'pc_thm7_2nd_num_mcc',
'pc_thm7_3rd_pay_mcc',
'pc_thm7_3rd_num_mcc',
'pc_thm7_max_num_pvn',
'pc_thm7_night_pay',
'pc_thm7_night_num',
'pc_thm8_pay',
'pc_thm8_num',
'pc_thm8_1st_pay_mcc',
'pc_thm8_1st_num_mcc',
'pc_thm8_2nd_pay_mcc',
'pc_thm8_2nd_num_mcc',
'pc_thm8_3rd_pay_mcc',
'pc_thm8_3rd_num_mcc',
'pc_thm8_max_num_pvn',
'pc_thm8_night_pay',
'pc_thm8_night_num',
'pc_thm9_pay',
'pc_thm9_num',
'pc_thm9_1st_pay_mcc',
'pc_thm9_1st_num_mcc',
'pc_thm9_2nd_pay_mcc',
'pc_thm9_2nd_num_mcc',
'pc_thm9_3rd_pay_mcc',
'pc_thm9_3rd_num_mcc',
'pc_thm9_max_num_pvn',
'pc_thm9_night_pay',
'pc_thm9_night_num',
'pc_thm10_pay',
'pc_thm10_num',
'pc_thm10_1st_pay_mcc',
'pc_thm10_1st_num_mcc',
'pc_thm10_2nd_pay_mcc',
'pc_thm10_2nd_num_mcc',
'pc_thm10_3rd_pay_mcc',
'pc_thm10_3rd_num_mcc',
'pc_thm10_max_num_pvn',
'pc_thm10_night_pay',
'pc_thm10_night_num',
'pc_thm11_pay',
'pc_thm11_num',
'pc_thm11_1st_pay_mcc',
'pc_thm11_1st_num_mcc',
'pc_thm11_2nd_pay_mcc',
'pc_thm11_2nd_num_mcc',
'pc_thm11_3rd_pay_mcc',
'pc_thm11_3rd_num_mcc',
'pc_thm11_max_num_pvn',
'pc_thm11_night_pay',
'pc_thm11_night_num',
'pc_thm12_pay',
'pc_thm12_num',
'pc_thm12_1st_pay_mcc',
'pc_thm12_1st_num_mcc',
'pc_thm12_2nd_pay_mcc',
'pc_thm12_2nd_num_mcc',
'pc_thm12_3rd_pay_mcc',
'pc_thm12_3rd_num_mcc',
'pc_thm12_max_num_pvn',
'pc_thm12_night_pay',
'pc_thm12_night_num',
'pc_thm13_pay',
'pc_thm13_num',
'pc_thm13_1st_pay_mcc',
'pc_thm13_1st_num_mcc',
'pc_thm13_2nd_pay_mcc',
'pc_thm13_2nd_num_mcc',
'pc_thm13_3rd_pay_mcc',
'pc_thm13_3rd_num_mcc',
'pc_thm13_max_num_pvn',
'pc_thm13_night_pay',
'pc_thm13_night_num',
'pc_thm14_pay',
'pc_thm14_num',
'pc_thm14_1st_pay_mcc',
'pc_thm14_1st_num_mcc',
'pc_thm14_2nd_pay_mcc',
'pc_thm14_2nd_num_mcc',
'pc_thm14_3rd_pay_mcc',
'pc_thm14_3rd_num_mcc',
'pc_thm14_max_num_pvn',
'pc_thm14_night_pay',
'pc_thm14_night_num',
'pc_thm15_pay',
'pc_thm15_num',
'pc_thm15_1st_pay_mcc',
'pc_thm15_1st_num_mcc',
'pc_thm15_2nd_pay_mcc',
'pc_thm15_2nd_num_mcc',
'pc_thm15_3rd_pay_mcc',
'pc_thm15_3rd_num_mcc',
'pc_thm15_max_num_pvn',
'pc_thm15_night_pay',
'pc_thm15_night_num',
'pc_thm16_pay',
'pc_thm16_num',
'pc_thm16_1st_pay_mcc',
'pc_thm16_1st_num_mcc',
'pc_thm16_2nd_pay_mcc',
'pc_thm16_2nd_num_mcc',
'pc_thm16_3rd_pay_mcc',
'pc_thm16_3rd_num_mcc',
'pc_thm16_max_num_pvn',
'pc_thm16_night_pay',
'pc_thm16_night_num',
'pc_thm17_pay',
'pc_thm17_num',
'pc_thm17_1st_pay_mcc',
'pc_thm17_1st_num_mcc',
'pc_thm17_2nd_pay_mcc',
'pc_thm17_2nd_num_mcc',
'pc_thm17_3rd_pay_mcc',
'pc_thm17_3rd_num_mcc',
'pc_thm17_max_num_pvn',
'pc_thm17_night_pay',
'pc_thm17_night_num',
'pc_thm18_pay',
'pc_thm18_num',
'pc_thm18_1st_pay_mcc',
'pc_thm18_1st_num_mcc',
'pc_thm18_2nd_pay_mcc',
'pc_thm18_2nd_num_mcc',
'pc_thm18_3rd_pay_mcc',
'pc_thm18_3rd_num_mcc',
'pc_thm18_max_num_pvn',
'pc_thm18_night_pay',
'pc_thm18_night_num']

PC2_FIELD_LIST = ['flag_payConsumption2',
'pc_c2_date',
'pc_cst_claf',
'pc_cnt_claf',
'pc_cna_claf',
'pc_chv_claf',
'pc_cnfi_score',
'pc_rsk_score',
'pc_crb_score',
'pc_summary_score',
'pc_cnp_claf',
'pc_m1_pvn',
'pc_m3_max_pay',
'pc_m3_min_pay',
'pc_m3_mcc_num',
'pc_m6_max_pay',
'pc_m6_min_pay',
'pc_m6_mcc_num',
'pc_m6_act_avg_num',
'pc_m6_avg_pay',
'pc_m6_max_num_pvn',
'pc_m6_pay_stab',
'pc_m6_act_avg_pay',
'pc_m12_debit_pay',
'pc_m12_cash_num',
'pc_m12_cash_pay',
'pc_m12_overseas_num',
'pc_m12_overseas_pay',
'pc_m12_weekend_num']


PC2_SORT=['cst_score',
'cnt_score' ,
'cna_score',
'chv_score',
'dsi_score' ,
'rsk_score' ,
'crb_score',
'summary_score',
'cnp_score',
'LOC_1_var1',
'RFM_3_var3',
'RFM_3_var4',
'MCC_3_var1',
'RFM_6_var3',
'RFM_6_var4',
'MCC_6_var1',
'FLAG_6_var1',
'FLAG_6_var3',
'LOC_6_var11',
'RFM_6_var6',
'FLAG_6_var8',
'RFM_12_var23',
'RFM_12_var29',
'RFM_12_var30',
'RFM_12_var39',
'RFM_12_var40',
'RFM_12_var50']

AC_FIELD_LIST = ['ac_regionno',
            'ac_mobile_id',
            'ac_bank_pf_ind',
            'ac_bank_zs_ind',
            'ac_bank_gs_ind',
            'ac_bank_js_ind',
            'ac_bank_pa_ind',
            'ac_bank_zsx_ind',
            'ac_cardindex',
            'ac_m16m18_debit_out',
            'ac_m13m15_debit_out',
            'ac_m10m12_debit_out',
            'ac_m7m9_debit_out',
            'ac_m4m6_debit_out',
            'ac_m1m3_debit_out',
            'ac_m16m18_debit_in',
            'ac_m13m15_debit_in',
            'ac_m10m12_debit_in',
            'ac_m7m9_debit_in',
            'ac_m4m6_debit_in',
            'ac_m1m3_debit_in',
            'ac_m16m18_debit_repay',
            'ac_m13m15_debit_repay',
            'ac_m10m12_debit_repay',
            'ac_m7m9_debit_repay',
            'ac_m4m6_debit_repay',
            'ac_m1m3_debit_repay',
            'ac_m16m18_debit_invest',
            'ac_m13m15_debit_invest',
            'ac_m10m12_debit_invest',
            'ac_m7m9_debit_invest',
            'ac_m4m6_debit_invest',
            'ac_m1m3_debit_invest',
            'ac_m16m18_credit_out',
            'ac_m13m15_credit_out',
            'ac_m10m12_credit_out',
            'ac_m7m9_credit_out',
            'ac_m4m6_credit_out',
            'ac_m1m3_credit_out',
            'ac_m16m18_credit_cash',
            'ac_m13m15_credit_cash',
            'ac_m10m12_credit_cash',
            'ac_m7m9_credit_cash',
            'ac_m4m6_credit_cash',
            'ac_m1m3_credit_cash',
            'ac_m16m18_credit_in',
            'ac_m13m15_credit_in',
            'ac_m10m12_credit_in',
            'ac_m7m9_credit_in',
            'ac_m4m6_credit_in',
            'ac_m1m3_credit_in',
            'ac_m16m18_debit_balance',
            'ac_m13m15_debit_balance',
            'ac_m10m12_debit_balance',
            'ac_m7m9_debit_balance',
            'ac_m4m6_debit_balance',
            'ac_m1m3_debit_balance',
            'ac_m16m18_bill_if_pay',
            'ac_m13m15_bill_if_pay',
            'ac_m10m12_bill_if_pay',
            'ac_m7m9_bill_if_pay',
            'ac_m4m6_bill_if_pay',
            'ac_m1m3_bill_if_pay',
            'ac_m16m18_credit_status',
            'ac_m13m15_credit_status',
            'ac_m10m12_credit_status',
            'ac_m7m9_credit_status',
            'ac_m4m6_credit_status',
            'ac_m1m3_credit_status',
            'ac_m16m18_loan',
            'ac_m13m15_loan',
            'ac_m10m12_loan',
            'ac_m7m9_loan',
            'ac_m4m6_loan',
            'ac_m1m3_loan',
            'ac_m16m18_credit_def',
            'ac_m13m15_credit_def',
            'ac_m10m12_credit_def',
            'ac_m7m9_credit_def',
            'ac_m4m6_credit_def',
            'ac_m1m3_credit_def',
            'ac_cell_balance',
            'ac_cell_acc_date',
            'ac_cell_bal_sign',
            'ac_cell_user_status',
            'ac_cell_auth_date']

# 如果查不到数据，默认的数据
DEFAULT_LD = ['' for i in range(len(AC_FIELD_LIST))]
DEFAULT_LD2 = ['' for i in range(len(NEW_LD_LIST))]

RELATIVE_DICT = {'regionno':'ac_regionno',
                'mobileid':'ac_mobile_id',
                'bank_pf_ind':'ac_bank_pf_ind',
                'bank_zs_ind':'ac_bank_zs_ind',
                'bank_gs_ind':'ac_bank_gs_ind',
                'bank_js_ind':'ac_bank_js_ind',
                'bank_pa_ind':'ac_bank_pa_ind',
                'bank_zsx_ind':'ac_bank_zsx_ind',
                'card_cnt':'ac_cardindex',
                'deposit_outgo_m16_m18':'ac_m16m18_debit_out',
                'deposit_outgo_m13_m15':'ac_m13m15_debit_out',
                'deposit_outgo_m10_m12':'ac_m10m12_debit_out',
                'deposit_outgo_m7_m9':'ac_m7m9_debit_out',
                'deposit_outgo_m4_m6':'ac_m4m6_debit_out',
                'deposit_outgo_m1_m3':'ac_m1m3_debit_out',
                'deposit_income_m16_m18':'ac_m16m18_debit_in',
                'deposit_income_m13_m15':'ac_m13m15_debit_in',
                'deposit_income_m10_m12':'ac_m10m12_debit_in',
                'deposit_income_m7_m9':'ac_m7m9_debit_in',
                'deposit_income_m4_m6':'ac_m4m6_debit_in',
                'deposit_income_m1_m3':'ac_m1m3_debit_in',
                'deposit_repay_m16_m18':'ac_m16m18_debit_repay',
                'deposit_repay_m13_m15':'ac_m13m15_debit_repay',
                'deposit_repay_m10_m12':'ac_m10m12_debit_repay',
                'deposit_repay_m7_m9':'ac_m7m9_debit_repay',
                'deposit_repay_m4_m6':'ac_m4m6_debit_repay',
                'deposit_repay_m1_m3':'ac_m1m3_debit_repay',
                'deposit_invest_m16_m18':'ac_m16m18_debit_invest',
                'deposit_invest_m13_m15':'ac_m13m15_debit_invest',
                'deposit_invest_m10_m12':'ac_m10m12_debit_invest',
                'deposit_invest_m7_m9':'ac_m7m9_debit_invest',
                'deposit_invest_m4_m6':'ac_m4m6_debit_invest',
                'deposit_invest_m1_m3':'ac_m1m3_debit_invest',
                'credit_outgo_m16_m18':'ac_m16m18_credit_out',
                'credit_outgo_m13_m15':'ac_m13m15_credit_out',
                'credit_outgo_m10_m12':'ac_m10m12_credit_out',
                'credit_outgo_m7_m9':'ac_m7m9_credit_out',
                'credit_outgo_m4_m6':'ac_m4m6_credit_out',
                'credit_outgo_m1_m3':'ac_m1m3_credit_out',
                'credit_cash_out_m16_m18':'ac_m16m18_credit_cash',
                'credit_cash_out_m13_m15':'ac_m13m15_credit_cash',
                'credit_cash_out_m10_m12':'ac_m10m12_credit_cash',
                'credit_cash_out_m7_m9':'ac_m7m9_credit_cash',
                'credit_cash_out_m4_m6':'ac_m4m6_credit_cash',
                'credit_cash_out_m1_m3':'ac_m1m3_credit_cash',
                'credit_income_m16_m18':'ac_m16m18_credit_in',
                'credit_income_m13_m15':'ac_m13m15_credit_in',
                'credit_income_m10_m12':'ac_m10m12_credit_in',
                'credit_income_m7_m9':'ac_m7m9_credit_in',
                'credit_income_m4_m6':'ac_m4m6_credit_in',
                'credit_income_m1_m3':'ac_m1m3_credit_in',
                'balance_m16_m18':'ac_m16m18_debit_balance',
                'balance_m13_m15':'ac_m13m15_debit_balance',
                'balance_m10_m12':'ac_m10m12_debit_balance',
                'balance_m7_m9':'ac_m7m9_debit_balance',
                'balance_m4_m6':'ac_m4m6_debit_balance',
                'balance_m1_m3':'ac_m1m3_debit_balance',
                'bill_if_pay_all_m16_m18':'ac_m16m18_bill_if_pay',
                'bill_if_pay_all_m13_m15':'ac_m13m15_bill_if_pay',
                'bill_if_pay_all_m10_m12':'ac_m10m12_bill_if_pay',
                'bill_if_pay_all_m7_m9':'ac_m7m9_bill_if_pay',
                'bill_if_pay_all_m4_m6':'ac_m4m6_bill_if_pay',
                'bill_if_pay_all_m1_m3':'ac_m1m3_bill_if_pay',
                'credit_card_status_m16_m18':'ac_m16m18_credit_status',
                'credit_card_status_m13_m15':'ac_m13m15_credit_status',
                'credit_card_status_m10_m12':'ac_m10m12_credit_status',
                'credit_card_status_m7_m9':'ac_m7m9_credit_status',
                'credit_card_status_m4_m6':'ac_m4m6_credit_status',
                'credit_card_status_m1_m3':'ac_m1m3_credit_status',
                'loan_amt_m16_m18':'ac_m16m18_loan',
                'loan_amt_m13_m15':'ac_m13m15_loan',
                'loan_amt_m10_m12':'ac_m10m12_loan',
                'loan_amt_m7_m9':'ac_m7m9_loan',
                'loan_amt_m4_m6':'ac_m4m6_loan',
                'loan_amt_m1_m3':'ac_m1m3_loan',
                'if_pay_ontime_m16_m18':'ac_m16m18_credit_def',
                'if_pay_ontime_m13_m15':'ac_m13m15_credit_def',
                'if_pay_ontime_m10_m12':'ac_m10m12_credit_def',
                'if_pay_ontime_m7_m9':'ac_m7m9_credit_def',
                'if_pay_ontime_m4_m6':'ac_m4m6_credit_def',
                'if_pay_ontime_m1_m3':'ac_m1m3_credit_def',
                'hf_balance':'ac_cell_balance',
                'hf_acc_date':'ac_cell_acc_date',
                'hf_bal_sign':'ac_cell_bal_sign',
                'hf_user_status':'ac_cell_user_status',
                'hf_auth_date':'ac_cell_auth_date',
}

ICE = {
    "xxx001": IceSZDJ,
    "zdy_gtll": IceZdy,
    "zdy_getState": IceZdy,
    "zdy_vuici": IceZdy,
    "blxxb": IceBlxxb,
    "szdj" : IceSZDJ,
    "fy_dxyz" : IceLT,
    "fy_ltyz" : IceLT,
    "fy_ydyz" : IceLT,
    "xlxxcx" : IceXL,
    "ld" : IceLD,
    "zcx_sxzx" : IceZCX,
    "clwz" : IceCLWZ,
    "dwtz" : IceDWTZ,
    "qytz" : IceQYTZ,
    "qyjb" : IceQYJB,
    "dd" : IceDD,
    "bcjq" : IceBCJQ,
    "bchx" : IceBCHX,
    "shbcty" : IcePC2,
    "shbc" : IcePC,
    "jz" : IceJZD,
    "ldzh" : IceLD2,
    "mmd" : IceMMD,
    'dn_ftl': IceDN,
    'dn_tl': IceDN,
    'dn_tb': IceDN,
    'dn_state': IceDN,
    'dn_balance': IceDN,
    'dn_mcip': IceDN,
    'fy_ydcmoi': IceYD,
    'fy_ydms': IceYD,
    'fy_ydcmci': IceYD,
    'zskj_idjy': IceZSKJ,
    'hjkj_bcjq': IceHJKJ,
    'qcc_qydwtz': IceQCCDW,
    'qcc_qydwtztp': IceQCCDWTP,
    'qcc_qyygdgxtztp': IceQCCGD,
    'qcc_qyszgxzpcx': IceQCCSZ,
    'lw_clztcx': IceLWCP,
    'lw_cphsfzyz': IceLWCP,
    'zhx_hvvkjzpf': IceHVGV,
    'zhx_hvgcfxbq': IceHVGV,
    'zhx_hvgjfxbq': IceHVGV,
    'ylzc_zfxfxwph': IceYLZCXW,
    'xb_shsb': IceSHSB,
    'hjxxcx': IceHJXX,
    'rjh_ltsz': IceRJH,
    'sy_sfztwo': IceSYSFZ,
    'qcc_qygjzmhcx': IceQYMHCX,
    'qcc_dwtz': IceQCCDWTZ,
    'xz_sjzwzt': IceXZ,
    'xz_sjzwsc': IceXZ,
    'xz_sjsys': IceXZ,
    'blxxd': IceBLXXD,
    'zyhl_ydsj1': IceZYHL,
    'zyhl_ydsj2': IceZYHL,
    'zyhl_ydsj3': IceZYHL,
    'fy_mbtwo': IceFY,
}

