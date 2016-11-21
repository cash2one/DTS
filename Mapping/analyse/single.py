#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.views.generic import View

import os
import traceback
import logging
import time
import datetime
import urllib2
import urllib

from analyse.models import SourceFile, ColletDate
from account.models import Member
from analyse.mapping_headers import *
from util import iter_txt, get_md5
from ice import DataIce


errlog = logging.getLogger('daserr')
LOGIN_URL = [None, 'https://api.100credit.cn/bankServer/user/login.action', 'https://api.100credit.cn/bankServer2/user/login.action']
QUERY_URL = [None, 'https://api.100credit.cn/bankServer/data/bankData.action', 'https://api.100credit.cn/bankServer2/data/terData.action']


class CreateCustomView(View):
    def get(self, request):
        analy_names = []
        analys = Member.objects.filter(mem_type=2)
        for analy in analys:
            analy_names.append(analy.name)
        #put_in_collection()
        return render(request, 'single/create_custom.html', {'analys': analy_names})


def put_in_collection():
        try:
            name_dict = {'灿谷': '灿谷汽车金融', '光大信用卡': '光大',  '挖财数据': '挖财网', '平安银行': '平安信用卡', '夸克金融': '夸客金融'}
            file_path = '/opt/django_project/all_file/DTS/log/all_data_utf8.csv'
            _, ext = os.path.splitext(file_path)
            if ext == '.txt' or ext == '.csv':
                lines = iter_txt(file_path)
            rows = []
            id_error = 0
            cell_error = 0
            line_num = 0
            for line in lines:
                line_num += 1
                queue = []
                if line_num > 1:
                    line = line.strip().split(',')
                    for x in line:
                        queue.append(x)
                else:
                    continue
                queue = dict(zip(FILE_HEADS, queue))
                for key,value in queue.items():
                    value = queue[key]
                    if key in ('edu', 'if_house', 'civic_addr', 'civic_status'):
                        continue
                    if key == 'apply_amount' or 'approval_amount':
                        try:
                            value = float(value)
                            queue[key] = int(value)
                        except Exception, e:
                            value = ''
                    if key == 'apply_date' and len(queue['apply_date']) ==7:
                        queue['apply_date'] = queue['apply_date'] + '-01'
                    if key == 'id':
                        key = 'id_num'
                        queue[key] = queue.pop('id')
                    if not queue[key]:
                        queue.pop(key)

                comein_time = time.strftime('%Y-%m-%d %H:%M:%S')
                try:
                    file_name = queue.pop('source')
                except Exception, e:
                    continue
                file_name = queue.pop('source')
                if file_name in name_dict.keys():
                    user_name = name_dict[file_name]
                try:
                    file = SourceFile.objects.get(filename=file_name)
                    user = Member.objects.get(name=user_name)
                except Exception, e:
                    errlog.error(str(file_name) + str(user_name))
                queue.update({'source_file': file})
                queue.update({'user_type': file.user_type})
                queue.update({'guarantee_type': file.guarantee_type})
                queue.update({'file_source_type': file.file_source_type})
                queue.update({'custom_num': user.custom_num})
                queue.update({'comein_time': comein_time})

                rows.append(queue)
            for row in rows:
                try:
                    collect_date = ColletDate(**row)
                    collect_date.save()
                except Exception, e:
                    print row
                    errlog.error('加入数据集市:' + traceback.format_exc())
                    continue

            msg = '已成功加入数据集市'
            print msg
        except Exception, e:
            errlog.error("put in date collectionse error " + traceback.format_exc())
            print "********,入库失败"


class SingleMapView(View):
    def get(self, request):
        #page_num = request.GET.get('page', 1)
        return render(request, 'single/single_mapping.html', {'fileid': "hehe"})

    def ice_init(self):
        self.dataice = DataIce()
        try:
            self.dataice.initialize()
        except RuntimeError:
            errlog.error('in the  ice init ,there si out of runtime')
            return False
        return True

    def post(self, request):
        name = request.POST.get('name', '')
        name = name.strip()
        pid = request.POST.get('pid', '')
        pid = pid.strip()
        cell = request.POST.get('cell')
        cell = cell.strip()
        bank_card1 = request.POST.get('bank_card1', '')
        bank_card1 =bank_card1.strip()
        email = request.POST.get('email', '')
        addr = request.POST.get('addr', '')
        email = email.strip()
        date = request.POST.get('date', '2015-09-09')
        date = date.strip()
        swift = request.POST.get('swift', '')
        event = request.POST.get('even', '')
        meal = request.POST.get('meal', '')
        meal = meal.strip()
        event = event.strip()
        swift = swift.strip()
        apiname = request.POST.get('apiname', '')
        apicode = request.POST.get('apicode', '')
        apipasswd = request.POST.get('apipasswd', '')
        apiname = apiname.strip()
        apicode = apicode.strip()
        apipasswd = apipasswd.strip()

        if len(date) == 7:
            date = str(date) + '-01'
        if not apiname:
            res = '请输入您需要匹配的画像帐号名称'
            return render(request, 'single/results.html',{'credit_result': res})
        if not apipasswd:
            return render(request, 'single/results.html',{'credit_result': '请输入您需要匹配的画像帐号密码'})
        if not apicode:
            res = '请输入您需要匹配的画像帐号apicode'
            return render(request, 'single/results.html',{'credit_result': res})
        if not meal:
            res = '请输入您需要匹配的模块名称，注意大小写'
            return render(request, 'single/results.html',{'credit_result': res})
        if meal.startswith(','):
            meal = meal[1:]
        try:
            op = Operator(apiname, apipasswd, apicode)
            state, ret = op.login()
        except Exception, e:
            return render(request, 'single/results.html', {'credit_result': '画像帐号登录失败'})
        if not state:
            return render(request, 'single/results.html', {'credit_result': '画像帐号登录失败'})
        js = {
            'name': name,
            'user_date': date, 
            'meal': meal, 
            'cell': [cell], 
            'mail': [email],
            'home_addr': addr,
            'id': pid,
            'af_swift_number': swift,
            'event': event
        }
        res = op.get_one(json.dumps(js, ensure_ascii=False))
        result_credit = credit(res)
        res = json.dumps(res, ensure_ascii=False)
        res = res.encode('UTF-8')
        credit_sort = CREDIT_CRYPT_FLAG + CONSUMPTION_C + SPECIAL_C + STABILITY_C + MEDIA_C + LOCATION + TITLE + ASSETS + BRAND + SCORE
        return render(request, 'single/results.html',{'credit_result': res})#{'result_credit': result_credit, 'credit_sort': credit_sort})


    # def post(self, request):
    #     member = request.user.member
    #     apicode = '111134'
    #     name = request.POST.get('name', '')
    #     name = name.strip()
    #     pid = request.POST.get('pid', '')
    #     pid = pid.strip()
    #     cell = request.POST.get('cell')
    #     cell = cell.strip()
    #     bank_card1 = request.POST.get('bank_card1', '')
    #     bank_card1 =bank_card1.strip()
    #     email = request.POST.get('email', '')
    #     email = email.strip()
    #     date = request.POST.get('date', '2015-09-09')
    #     date =date.strip()
    #     date = date[:7]

    #     dataice = DataIce()
    #     try:
    #         dataice.initialize()
    #     except RuntimeError:
    #         errlog.error('in the  ice init ,there is out of runtime')
    #         return render(request, 'single/results.html',{"hehe": "ice超时，请重试。"})

    #     swift_number  = apicode + "_" + time.strftime('%Y%m%d%H%M%S') + str(random.randint(1000,9999))
    #     info_pc = dict({'cardId':bank_card1,
    #                           'client_type': '2',
    #                           'swift_number': swift_number})
    #     ret_pc = dataice.get_data((info_pc, 'shbc'))
    #     user_info2 = dict({'cardno':cardId,
    #                       'client_type': '2',
    #                       'swift_number': swift_number})
    #     ret_pc2 = dataice.get_data((user_info2, 'shbcty'))
    #     try:
    #         ret_pc = json.loads(ret_pc)
    #         ret_pc2 = json.loads(ret_pc2)
    #     except Exception, e:
    #         ret_pc = None
    #         ret_pc2 = None
    #     tr_ret_pc = IcePC.transform(ret_pc, ret_pc2)
    #     result_pc = dict(zip(PC_FIELD_LIST, tr_ret_pc))


    #     date_ld2 = date.replace('-','')
    #     info_ld2 = {'mobileid':cell,
    #         'querymonth':date_ld2,
    #         'client_type':'2',
    #         'swift_number': swift_number}
    #     ret_ld2 = dataice.get_data((info_ld2, 'ldtj'))
    #     try:
    #         ret_ld2 = json.loads(ret_ld2)
    #     except Exception, e:
    #         ret_ld2 = None
    #     try:
    #         tr_ret_ld2 = IceLD2.transform(ret_ld2)
    #     except Exception, e:
    #         errlog.error("ld2 trasnlate wrong:" + traceback.format_exc())
    #     print "ld2 after transform is :"
    #     print tr_ret_ld2
    #     result_ld2 = dict(zip(NEW_LD_LIST,tr_ret_ld2))
    #     print "ld2 after translate:"
    #     print result_ld2

    #     info_jzd = {'pid': pid,
    #         'client_type':'2',
    #         'swift_number': swift_number}
    #     ret_jzd = dataice.get_data((info_jzd, 'jz'))
    #     try:
    #         ret_jzd = json.loads(ret_jzd)
    #     except Exception, e:
    #         ret_jzd = None
    #     result_jzd, header = IceJZD.transform(ret_jzd)

    #     info_ld = {'mobiles':cell,
    #         'count':'1',
    #         'querymonth':date,
    #         'datetime':timestamp(),
    #         'client_type':'2',
    #         'swift_number': swift_number}
    #     ret_ld = dataice.get_data((info_ld, 'ld'))
    #     try:
    #         ret_ld = json.loads(ret_ld)
    #     except Exception, e:
    #         ret_ld =None
    #     result_ld = IceLD.transform(ret_ld)
    #     result_ld = dict(zip(AC_FIELD_LIST, result_ld))

    #     op = Operator()
    #     state, ret = op.login()
    #     if not state:
    #         errlog.error('画像登录失败。')
    #     js ={'name': name, 
    #         'user_date': date, 
    #         'meal': u'Authentication,Stability,Consumption,Score,Title,Media,Assets,Location,Brand,ApplyLoan,SpecialList,Accountchange', 
    #         'cell': [cell], 
    #         'mail': [email], 
    #         'id': pid}
    #     res = op.get_one(json.dumps(js, ensure_ascii=False))
    #     result_credit = credit(res)

    #     return render(request, 'single/results.html',{'result_pc': result_pc, 'pc_keys': PC_FIELD_LIST , 'result_ld':result_ld,'ld_keys': AC_FIELD_LIST, 'result_ld2': result_ld2, 'ld2_keys': NEW_LD_LIST, 'result_jzd':result_jzd,'jzd_keys':JZD_FIEL_LIST, 'result_credit': result_credit})

def credit(data):
    jd = data
    crypt = False
    port_state = False
    dd = {}
    modal = '2'
    if isinstance(jd, dict):
        try:
            for top_key in jd.keys():
                if top_key == u'Authentication':
                    if crypt and port_state:
                        if jd[top_key].keys():
                            dd.update({'flag_core_auth': '1'})
                        else:
                            dd.update({'flag_core_auth': '0'})
                    for key in jd[top_key].keys():
                        if key == 'key_relation':
                            dd.update({'auth_' + key.encode('utf-8'): jd[top_key][key]})
                        else:
                            if key == 'tel_home':
                                dd.update({'auth_home_tel': jd[top_key][key]})
                            elif key == 'tel_biz':
                                dd.update({'auth_biz_tel': jd[top_key][key]})
                            else:
                                dd.update({'auth_' + key.encode('utf-8'): jd[top_key][key]})
                elif top_key == 'SpecialList':
                    for key in jd[top_key].keys():
                        for key_type in jd[top_key][key].keys():
                            for item in jd[top_key][key][key_type]:
                                if item == 'number':
                                    key_name = 'sl_' + '_'.join([key.encode('utf-8'), key_type.encode('utf-8'), 'num'])
                                else:
                                    key_name = 'sl_' + '_'.join([key.encode('utf-8'), key_type.encode('utf-8'), item.encode('utf-8')])
                                dd.update({key_name: jd[top_key][key][key_type][item]})
                elif top_key == u'Title':
                    if crypt and port_state:
                        if jd[top_key].keys():
                            dd.update({'flag_core_title': '1'})
                        else:
                            dd.update({'flag_core_title': '0'})
                    for key in jd[top_key].keys():
                        dd.update({'title': jd[top_key][key]})
                elif top_key == u'Accountchange':
                    for key in jd[top_key].keys():
                        if key in ('cardindex', 'regionno'):
                            dd.update({'ac_' + key.encode("utf-8"): jd[top_key][key]})
                        else:
                            if isinstance(jd[top_key][key], dict):
                                for car_type in jd[top_key][key].keys():
                                    if isinstance(jd[top_key][key][car_type], dict):
                                        for item in jd[top_key][key][car_type]:
                                            if car_type == 'creditcard':
                                                key_name = '_'.join(['ac', key, 'credit', item.replace('income', 'in').replace('outgo','out').replace('default', 'def').replace('investment', 'invest')])
                                            elif car_type == 'debitcard':
                                                key_name = '_'.join(['ac', key, 'debit', item.replace('income', 'in').replace('outgo', 'out').replace('default', 'def').replace('investment','invest')])
                                            dd.update({key_name: jd[top_key][key][car_type][item]})
                                    else:
                                        dd.update({'ac_' + key.encode("utf-8") + '_' + car_type.encode("utf-8"): jd[top_key][key][car_type]})
                elif top_key == u'Score':
                    if modal[0] and modal[0][-1:] == '8':
                        if 'scorebr' in jd[top_key].keys():
                            dd.update({'Score_br_credit': jd[top_key]['scorebr']})
                        if 'scorecust' in jd[top_key].keys():
                            dd.update({'Score_cust_credit': jd[top_key]['scorecust']})
                    else:
                        dd['score_br_credit'] = jd[top_key].get('brcreditpoint', '')
                elif top_key == u'ApplyLoan':
                    for months in jd[top_key].keys():
                        if months in [u'month3', u'month6', u'month12']:
                            for key in jd[top_key][months].keys():
                                for is_bank in jd[top_key][months][key]:
                                    for item in jd[top_key][months][key][is_bank].keys():
                                        dd.update({'al_' + months.encode('utf-8')[0] + months.encode('utf-8')[5:] + '_' + key.encode('utf-8') + '_' + is_bank.encode('utf-8') + '_' + item.encode('utf-8')[:-3]: jd[top_key][months][key][is_bank][item]})
                elif top_key == u'Stability':
                    if isinstance(jd[top_key], dict):
                        if crypt and port_state:
                            if jd[top_key].keys():
                                dd.update({'flag_core_stab': '1'})
                            else:
                                dd.update({'flag_core_stab': '0'})
                        for key in jd[top_key].keys():
                            for item  in jd[top_key][key].keys():
                                if item == u'number':
                                    dd.update({'stab_' + key.encode('utf-8') + '_' + item.encode('utf-8')[:-3]: jd[top_key][key][item]})
                                else:
                                    dd.update({'stab_' + key.encode('utf-8') + '_' + item.encode('utf-8'): jd[top_key][key][item]})
                elif top_key == u'Consumption_c':
                    for key in jd[top_key].keys():
                        if key in ('time_recent', 'continue'):
                            name = 'cons_' +  key.encode('utf-8')
                            name = name.replace('continue', 'cont')
                            value = jd[top_key][key]
                            if isinstance(value, dict):
                                value = ''
                            dd .update({name: value})
                        else:
                            if isinstance(jd[top_key][key], dict):
                                for level in jd[top_key][key].keys():
                                    if isinstance(jd[top_key][key][level], dict):
                                        for item in jd[top_key][key][level]:
                                            name = 'cons_' + key.encode('utf-8') + '_' + level.encode('utf-8') + '_' + item.encode('utf-8')
                                            name = name.replace('number', 'num').replace('日用百货', 'RYBH').replace('母婴用品', 'MYYP').replace('家用电器', 'JYDQ').replace('month', 'm').replace('total', 'tot')
                                            value = jd[top_key][key][level][item]
                                            dd.update({name:value})
                elif top_key == u'Consumption':
                    if isinstance(jd[top_key], dict):
                        if crypt and port_state:
                            if jd[top_key].keys():
                                dd.update({'flag_core_cons': '1'})
                            else:
                                dd.update({'flag_core_cons': '0'})
                        for key in jd[top_key].keys():
                            if key in [u'month3', u'month6', u'month12']:
                                if isinstance(jd[top_key][key], dict):
                                    for key_type in jd[top_key][key].keys():
                                        for item in jd[top_key][key][key_type].keys():
                                            if item == u'maxpay':
                                                dd.update({'cons_' + 'm12' + '_' + key_type.encode('utf-8').replace('其他', '其它') + '_level': jd[top_key]['level'].get(key_type, '')})
                                            if item == u'number':
                                                dd.update({'cons_' + key.encode('utf-8')[0]  + key.encode('utf-8')[5:] + '_' + key_type.encode('utf-8').replace('其他', '其它') + '_' + item.encode('utf-8')[:-3]: jd[top_key][key][key_type][item]})
                                            else:
                                                dd.update({'cons_' + key.encode('utf-8')[0]  + key.encode('utf-8')[5:] + '_' + key_type.encode('utf-8').replace('其他', '其它') + '_' + item.encode('utf-8'): jd[top_key][key][key_type][item]})
                            elif key in [u'level',]:
                                if isinstance(jd[top_key][key], dict):
                                    for item in jd[top_key][key].keys():
                                        dd.update({'cons_' + 'm12' + '_' + item.encode('utf-8').replace('其他', '其它') + '_level': jd[top_key][key].get(item, '')})
                elif top_key == u'Assets':
                    if isinstance(jd[top_key], dict):
                        if crypt and port_state:
                            if jd[top_key].keys():
                                dd.update({'flag_core_assets': '1'})
                            else:
                                dd.update({'flag_core_assets': '0'})
                        for item in jd[top_key].keys():
                            dd.update({'assets_' + item.encode('utf-8'): jd[top_key][item]})
                elif top_key == u'Media':
                    if isinstance(jd[top_key], dict):
                        if crypt and port_state:
                            if jd[top_key].keys():
                                dd.update({'flag_core_media': '1'})
                            else:
                                dd.update({'flag_core_media': '0'})
                        for month in jd[top_key].keys():
                            if isinstance(jd[top_key][month], dict):
                                for key_type in jd[top_key][month].keys():
                                    for item in jd[top_key][month][key_type].keys():
                                        dd.update({'media_' + month.encode('utf-8')[0] + month.encode('utf-8')[5:] + '_' + key_type.encode('utf-8').replace('其他', '其它') + '_' + item.encode('utf-8'): jd[top_key][month][key_type][item]})
 
                elif top_key == u'Brand':
                    if isinstance(jd[top_key], dict):
                        if crypt and port_state:
                            if jd[top_key].keys():
                                dd.update({'flag_core_brand': '1'})
                            else:
                                dd.update({'flag_core_brand': '0'})
                        for top_n in jd[top_key].keys():
                            dd.update({'brand_' + top_n.encode('utf-8'): jd[top_key][top_n]})
                elif top_key == u'Location':
                    if isinstance(jd[top_key], dict):
                        if crypt and port_state:
                            if jd[top_key].keys():
                                dd.update({'flag_core_location': '1'})
                            else:
                                dd.update({'flag_core_location': '0'})
                            if not port_state:
                                if jd[top_key].keys():
                                    dd.update({'flag_location': '1'})
                                else:
                                    dd.update({'flag_location': '0'})
                        for key_type in jd[top_key].keys():
                            for addr in jd[top_key][key_type].keys():
                                dd.update({ 'location_' + key_type.encode('utf-8')[:-5] + '_' + (addr[:4] + addr[-1]).encode('utf-8'): jd[top_key][key_type][addr]})
                elif top_key == u'SpecialList_c':
                    if isinstance(jd[top_key], dict):
                        for top_type in jd[top_key].keys():
                            if top_type in ['cell', 'gid', 'id']:
                                for item in jd[top_key][top_type].keys():
                                    dd.update({'sl_' + top_type.encode("utf-8") +'_' + item.encode("utf-8"):jd[top_key][top_type][item]})
                elif top_key == u'Stability_c':
                    if isinstance(jd[top_key], dict):
                        for top_type in jd[top_key].keys():
                            if top_type == 'Authentication':
                                for item in jd[top_key][top_type].keys():
                                    name = 'stab_auth_' + item.encode("utf-8")
                                    if modal[0][-1:] == '8':
                                        name = name.replace('tel_biz', 'biz_tel').replace('tel_home', 'home_tel')
                                    dd.update({name: jd[top_key][top_type][item]})
                            if top_type in ['id', 'cell', 'addr', 'mail', 'name', 'tel']:
                                if isinstance(jd[top_key][top_type], dict):
                                    for item in jd[top_key][top_type].keys():
                                        stab_name = 'stab_' + top_type.encode("utf-8") +'_' + item.encode("utf-8")
                                        stab_name = stab_name.replace("number",'num')
                                        dd.update({stab_name:jd[top_key][top_type][item]})
                elif top_key == u'Media_c':
                    if isinstance(jd[top_key], dict):
                        for month in jd[top_key].keys():
                            if isinstance(jd[top_key][month], dict):
                                for key_type in jd[top_key][month].keys():
                                    if isinstance(jd[top_key][month][key_type], dict ):
                                        for item in jd[top_key][month][key_type].keys():
                                            media_name = 'media_' + month.encode("utf-8") +'_' + key_type.encode("utf-8") +'_'+ item.encode("utf-8")
                                            media_name = media_name.replace('month','m').replace('total', 'tot').replace('catenum', 'cate').replace('文学艺术', 'WXYS').replace('财经', 'CJ').replace('母婴/育儿', 'MYYE')
                                            if media_name.startswith('media_tot') or media_name.startswith('media_max'):
                                                media_name = media_name.replace('visitdays','days')
                                            if media_name.startswith('media_tot'):
                                                media_name = media_name.replace('cate','catenum')
                                            dd.update({media_name:jd[top_key][month][key_type][item]})
                elif top_key == 'PayConsumption':
                    for month in jd[top_key].keys():
                        for top_type in jd[top_key][month].keys():
                            if isinstance(jd[top_key][month][top_type], dict):
                                for item in jd[top_key][month][top_type].keys():
                                    name = "pc_" + month.encode("utf-8") + "_" + top_type.encode("utf-8") + "_" + item.encode("utf-8")
                                    value = jd[top_key][month][top_type][item]
                                    name = name.replace("payMcc", "pay_mcc").replace("numberMcc", "num_mcc").replace("number", "num").replace("first", "1st").replace("third", "3rd").replace("second", "2nd")
                                    if isinstance(value , unicode):
                                        value = value.replace("\N", "null")
                                    dd.update({name: value})
                            else:
                                name = "pc_" + month.encode("utf-8") + "_" + top_type.encode("utf-8")
                                value =  jd[top_key][month][top_type]
                                name = name.replace("maxNumberProvince", "max_num_pvn").replace('number', "num")
                                if isinstance(value, unicode):
                                    value = value.replace("\N", "null")
                                dd.update({name:value})

                elif top_key == u'Flag':
                    xd3_flag_head = []
                    for top_type in jd[top_key].keys():
                        if modal[0][-1:] == '8':
                            name = 'flag_' + top_type.encode('utf-8')
                            flag_state = name.startswith('flag_core')
                            xd3_flag_head.append(name)
                            if crypt and flag_state:
                                dd.update({name: jd[top_key][top_type]})
                            elif not crypt and flag_state:  
                                pass
                            else:
                                dd.update({name:jd[top_key][top_type]})
                        else:
                            if isinstance(jd[top_key][top_type], dict):
                                for item in jd[top_key][top_type].keys():
                                    if item == 'key' and port_state :
                                        dd.update({'flag_core_key': jd[top_key][top_type][item]})
                            else:
                                if modal[0][-1:] == '8':
                                    if top_type in ('media', 'assets', 'authentication', 'consumption', 'stability'):
                                        continue
                                name = 'flag_' + top_type.encode('utf-8')
                                flag_state = name.startswith('flag_core')
                                if crypt and flag_state:
                                    dd.update({name: jd[top_key][top_type]})
                                elif not crypt and flag_state:  
                                    pass
                                else:
                                    dd.update({name:jd[top_key][top_type]})
        except Exception, e:
            errlog.error(traceback.format_exc())
    return dd


def timestamp():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


class Operator:
    tid = None
    tmd5 = None

    def __init__(self, apiname, apipasswd, apicode):
        self.name = apiname
        self.apicode = apicode
        self.password = apipasswd

    def post(self, url, data):
        req = urllib2.Request(url)
        data = urllib.urlencode(data)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = opener.open(req, data)
        res = response.read()
        return json.loads(res)

    def login(self):
        res = self.post(LOGIN_URL[2], {
            'userName': self.name,
            'password': self.password,
            'apiCode': self.apicode
            })
        if res['code'] != '00':
            return False, '画像查询错误'
        self.tid = res['tokenid']
        self.tmd5 = get_md5(self.apicode + res['tokenid'])
        print 'tid:', self.tid, 'tmd5', self.tmd5
        return True, '00'

    def get_one(self, data):
        res = self.post(QUERY_URL[2], {
            'tokenid': self.tid,
            'interCommand': '1000',
            'apiCode': self.apicode,
            'jsonData': data,
            'checkCode': get_md5(data+self.tmd5)
            })
        return res


JZD_FIEL_LIST = [
    'id',
    'at_name',
    'date',
    'at_arr_cty_total',
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
]


AC_FIELD_LIST = [
    'ac_regionno',
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
    'ac_cell_auth_date'
]


NEW_LD_LIST = [
    'flag_ac_month',
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
]


PC_FIELD_LIST = [
    'flag_payConsumption',
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
    'pc_thm18_night_num',
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
    'pc_m12_weekend_num'
]


JZD_FIEL_LIST = [
    'id',
    'at_name',
    'date',
    'at_arr_cty_total',
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
]

FILE_HEADS = [
    'cus_num',
    'id',
    'cell',
    'email',
    'qq_num',
    'name',
    'home_addr',
    'home_tel',
    'biz_addr',
    'biz_tel',
    'other_addr',
    'bank_card1',
    'bank_card2',
    'flag1',
    'flag2',
    'notes',
    'apply_date',
    'observe_date',
    'apply_channel',
    'apply_id',
    'apply_addr',
    'apply_amount',
    'apply_product',
    'approval_status',
    'approval_date',
    'approval_amount',
    'collateral',
    'loan_date',
    'loan_purpose',
    'loan_status',
    'repayment_periods',
    'age',
    'race',
    'gender',
    'birthday',
    'marriage',
    'edu',
    'wechat_city',
    'wechat_name',
    'wechat_province',
    'providentfund',
    'socialsecurity',
    'id_ps',
    'id_start',
    'id_end',
    'id_city',
    'id_type',
    'civic_addr',
    'civic_status',
    'postalcode',
    'city',
    'province',
    'contact_name_1',
    'contact_relation_1',
    'contact_cell_1',
    'contact_name_2',
    'contact_relation_2',
    'contact_cell_2',
    'contact_name_3',
    'contact_relation_3',
    'contact_cell_3',
    'if_house',
    'if_vehicle',
    'housing_cate',
    'vehicle_id',
    'vehicle_type',
    'biz_name',
    'biz_size',
    'industry',
    'company_cate',
    'salary',
    'position',
    'working_period',
    'acc_open_date',
    'card_level',
    'branch',
    'currency',
    'ins_balance',
    'update_balance',
    'update_capital',
    'update_date',
    'update_interest',
    'update_overduepayment',
    'update_overlimitfee',
    'update_servicefee',
    'bill_day',
    'bill_post',
    'bill_addr',
    'ins_amount',
    'ins_date_claims',
    'ins_firstlogindate',
    'ins_newvehicleprice',
    'ins_period',
    'ins_yearly_claims_num',
    'imei',
    'imsi',
    'mobil_type',
    'GID',
    'other_var1',
    'var_exp1',
    'other_var2',
    'var_exp2',
    'other_var3',
    'var_exp3',
    'source',
    'flag',
    'def_days'
]
