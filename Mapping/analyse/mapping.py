#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import timezone
from django.core.files import File

from Queue import Queue
from sets import Set
import codecs
import urllib2
import threading
import urllib
import csv
import ssl
import os
import logging
import traceback
import re
import time
import util
from account.models import Queryer
from analyse.models import MappingedFile, MealHead, Meal, MealSort, Interface, SourceFile, Member, LogInfo
from mapping_headers import *
import icedts


LOGIN_URL = [None, 'https://api.100credit.cn/bankServer/user/login.action', 'https://api.100credit.cn/bankServer2/user/login.action']
QUERY_URL = [None, 'https://api.100credit.cn/bankServer/data/bankData.action', 'https://api.100credit.cn/bankServer2/data/bankData.action', 'https://api.100credit.cn/bankServer2/data/terData.action']
HAINA_API_URL = 'http://192.168.22.27:8081/HainaApi/data/getData.action'


interfaces = Interface.objects.all()
PORT = {}
for interface in interfaces:
    PORT.update({interface.name: interface.chinese_name})

MODAL_NAME = {}
model_name = Meal.objects.filter()
for name in model_name:
    MODAL_NAME.update({name.name: name.chinese_name})

CN_2_EN_EC_FR_CLASS = {
    '服装配饰': 'FZPS', '鞋': 'X', '母婴用品': 'MYYP', '文化娱乐': 'WHYL', '运动户外': 'YDHW',
    '日用百货': 'RYBH', '个护化妆': 'GHHZ', '箱包': 'XB', '手机/手机配件': 'SJSJPJ', '电脑/办公': 'DNBG',
    '美食特产': 'MSTC', '家具建材': 'JJJC', '通讯': 'TX', '家用电器': 'JYDQ', '家居家纺': 'JJJF', '数码': 'SM',
    '钟表首饰': 'ZBSS', '汽车用品': 'QCYP', '网络游戏/虚拟物品': 'WLYXXNWP', '医疗保健': 'YLBJ', '本地生活': 'BDSH',
    '珠宝贵金属': 'ZBGJS', '收藏': 'SC', '宠物生活': 'CWSH', '出差旅游': 'CCLY', '教育培训': 'JYPX', '房产': 'FC',
    '保险/理财': 'BXLC', '其它': 'QT'
}
CN_2_EN_MEDIA_FR_CLASS = {
    '财经': 'CJ', '交友': 'JYOU', '军事': 'JS', '彩票': 'CP', '旅游': 'LY', '女性时尚': 'NXSS', '汽车': 'QC',
    '社区': 'SQ', '生活': 'SH', '视频': 'SP', 'IT': 'IT', '数码': 'SM', '手机': 'SJ', '体育': 'TY', '游戏': 'YXI',
    '文学艺术': 'WXYS', '新闻': 'XW', '音乐': 'YYUE', '支付': 'ZF', '影视': 'YS', '邮箱': 'YXIANG', '招聘': 'ZP',
    '教育': 'JYU', '房产': 'FC', '应用': 'YYONG', '动漫': 'DM', '美食': 'MS', '母婴/育儿': 'MYYE', '知识问答': 'ZSWD',
    '娱乐': 'YL', '历史': 'LS', '健康': 'JK', '户外': 'HW', '其它': 'QT'
}
FIELDS_2_SEND_FIELDS = {
    'id': 'id',
    'cell': 'cell',
    'email': 'mail',
    'name': 'name',
    'home_addr': 'home_addr',
    'biz_addr': 'biz_addr',
    'other_addr': 'oth_addr',
    'home_tel': 'tel_home',
    'biz_tel': 'tel_biz',
    'bank_id': 'bank_id',
    'apply_date': 'user_date',
    'apply_amount': 'apply_money',
    'apply_product': 'apply_product',
    'loan_date': 'loan_reason',
    'repayment_periods': 'refund_periods',
    'age': 'age',
    'gender': 'sex',
    'marriage': 'marriage',
    'edu': 'exducationallevel',
    'civic_addr': 'per_addr',
    'postal_code': 'postal_code',
    'contact_cell_1': 'linkman_cell',
    'contact_name_1': 'linkman_rela',
    'housing_cate': 'house_type',
    'biz_name': 'biz_workfor',
    'industry': 'biz_industry',
    'company_cate': 'biz_type',
    'salary': 'incode',
    'position': 'biz_positon',
    'bank_card1': 'bank_card1',
    'bank_card2': 'bank_card2',
}

g_mapping_files = {}

TMP_PATH = settings.MY_TMP_PATH

errlog = logging.getLogger('daserr')

behaviorlog = logging.getLogger('behavior')

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context


class Operator(object):
    name = ''
    apicode = ''
    password = ''
    tid = None
    tmd5 = None

    def __init__(self, qer):
        self.name = qer.name
        self.apicode = qer.apicode
        self.password = qer.passwd

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
            return False, res['code']
        self.tid = res['tokenid']
        self.tmd5 = util.get_md5(self.apicode + res['tokenid'])
        return True, '00'

    def get_one(self, data, modal):
        url = QUERY_URL[3]
        if modal in ['TelCheck', 'IdPhoto', 'TelPeriod', 'TelStatus']:
            url = HAINA_API_URL
            api_data = {}
            data = json.loads(data)
            for key in ['meal', 'cell', 'id', 'name']:
                api_data.update({key: data[key]})
            api_data['cell'] = api_data['cell'][0]
            api_data = json.dumps(api_data, ensure_ascii=False)
            res = self.post(url, {
                'tokenid': self.tid,
                'apiCode': self.apicode,
                'jsonData': api_data,
                'checkCode': util.get_md5(api_data+self.tmd5)
                })
        else:
            res = self.post(url, {
                'tokenid': self.tid,
                'interCommand': '1000',
                'apiCode': self.apicode,
                'jsonData': data,
                'checkCode': util.get_md5(data+self.tmd5),
                })
        return res


class BaseMapping(object):

    def __init__(self, srcfile, member, select, ip, username, modal):
        self.srcfile = srcfile
        self.member = member
        self.select = select
        self.modal = modal
        self.ip = ip
        self.username = username
        self.qer = Queryer.objects.get(constom=member)
        if len(self.qer.mapping_files) > 1200:
            self.qer.mapping_files = self.qer.mapping_files[:1200]
            self.qer.save()
        self.header_rel = icedts.HEADER_REL[str(select)]
        self.startline = int(srcfile.skip_lines)
        self.file_name = os.path.basename(str(srcfile))
        self.file_base_name = os.path.splitext(self.file_name)[0]
        self.file_path = os.path.join(settings.MEDIA_ROOT, srcfile.filename.name)
        self.fields = srcfile.fields
        self.total_lines = srcfile.total_lines
        self.timestamp = time.strftime('%Y%m%d-%H%M')
        self.crypt_file_name = '_'.join([self.file_base_name, self.timestamp, 'crypt']) + '.csv'
        self.show_file_name = '_'.join([self.file_base_name, self.timestamp]) + '.csv'
        self.crypt_txt_name = '_'.join([self.file_base_name, self.timestamp, 'crypt']) + '.txt'
        self.show_txt_name = '_'.join([self.file_base_name, self.timestamp]) + '.txt'
        self.crypt_txt_path = os.path.join(TMP_PATH, self.crypt_txt_name)
        self.show_txt_path = os.path.join(TMP_PATH, self.show_txt_name)
        self.crypt_file_path = os.path.join(TMP_PATH, self.crypt_file_name)
        self.show_file_path = os.path.join(TMP_PATH, self.show_file_name)
        self.filereader = icedts.FileReader(self.file_path, self.header_rel, self.fields,
                                            startline=self.startline, port_type=self.select)
        self.apicode = self.qer.apicode
        self.ice = icedts.ICE[select](self.filereader, self.apicode)
        self.ice_status = self.ice.ice_init()
        self.ice_check = self.ice.check_ice(modal, select)

    def check(self):
        qer = Queryer.objects.get(constom=self.member)
        qer.start_match = timezone.now()
        if not self.filereader.exist():
            qer.is_busy = False
            qer.end_match = timezone.now()
            qer.save()
            return False, '没有找到原文件!'
        if not self.filereader.checkfields():
            qer.is_busy = False
            qer.end_match = timezone.now()
            qer.save()
            return False, '文件缺少必要的字段'
        if not self.filereader.check_line():
            qer.is_busy = False
            qer.end_match = timezone.now()
            qer.save()
            return False, '文件里没有数据'
        if not self.ice_status:
            self.ice.destroy()
            qer.is_busy = False
            qer.end_match = timezone.now()
            qer.save()
            errlog.error('ice服务异常, 初始化失败')
            return False, 'ice服务初始化超时, 请稍后再试!'
        if not self.ice_check:
            self.ice.destroy()
            qer.is_busy = False
            qer.end_match = timezone.now()
            qer.save()
            errlog.error('ice服务异常, 无法查询到数据')
            return False, 'ice服务连接超时, 无法查询到数据, 请稍后再试或联系管理员!'
        return True, 'ok'

    def match(self):
        try:
            qer = Queryer.objects.get(constom=self.member)
            fields = self.fields.strip().split(',')
            if self.select in icedts.HEADER_TRAN.keys():
                fields_rel = self.filereader.translate(icedts.HEADER_TRAN[self.select],fields)
            else:
                fields_rel = self.filereader.translate({},fields)
            info_list, data_txt = self.ice.generate_query_infos(self.select, fields, fields_rel, self.modal)
            results, list_txt = self.ice.query_ice_data(info_list, data_txt, self.select)
            LogInfo.objects.create(username=self.username,
                ip = self.ip,
                filename = self.srcfile.filename,
                query_interface = PORT[str(self.select)],
                num = self.srcfile.total_lines
                )
            headers, lines = self.ice.process_result(results, self.srcfile.id, fields, fields_rel, self.modal, self.select)
            self.ice.write_to_csv(self.show_file_path, headers, lines, crypt=False)
            self.ice.write_to_csv(self.crypt_file_path, headers, lines, crypt=True)
            self.ice.write_to_txt(self.show_txt_path, headers, list_txt, crypt=False)
            self.ice.write_to_txt(self.crypt_txt_path, headers, list_txt, crypt=True)
        except Exception:
            self.ice.destroy()
            qer.end_match = timezone.now()
            qer.is_busy = False
            qer.save()
            errlog.exception('处理ice结果的时候出错了')
            return False, '处理ice结果的时候出错了, 联系管理员!'
        try:
            mf = MappingedFile(source_file=self.srcfile,
                               customer=self.srcfile.custom,
                               file_size=os.path.getsize(self.show_file_path),
                               is_cus_visible=False,
                               is_crypt=False,
                               is_haina=True,
                               is_csv=True,
                               file_from=PORT[str(self.select)])
            mf.file.save(self.show_file_name, File(open(self.show_file_path)))
            mf.can_down.add(self.member)
            mf.can_down.add(self.srcfile.custom)
            mf.save()
            mf = MappingedFile(source_file=self.srcfile,
                               customer=self.srcfile.custom,
                               file_size=os.path.getsize(self.crypt_file_path),
                               is_cus_visible=False,
                               is_crypt=True,
                               is_haina=True,
                               is_csv=True,
                               file_from=PORT[str(self.select)])
            mf.file.save(self.crypt_file_name, File(open(self.crypt_file_path)))
            mf.can_down.add(self.member)
            mf.save()
            mf = MappingedFile(source_file=self.srcfile,
                               customer=self.srcfile.custom,
                               file_size=os.path.getsize(self.show_txt_path),
                               is_cus_visible=False,
                               is_crypt=False,
                               is_haina=True,
                               is_csv=True,
                               file_from=PORT[str(self.select)])
            mf.file.save(self.show_txt_name, File(open(self.show_txt_path)))
            mf.can_down.add(self.member)
            mf.can_down.add(self.srcfile.custom)
            mf.save()
            mf = MappingedFile(source_file=self.srcfile,
                               customer=self.srcfile.custom,
                               file_size=os.path.getsize(self.crypt_txt_path),
                               is_cus_visible=False,
                               is_crypt=True,
                               is_haina=True,
                               is_csv=True,
                               file_from=PORT[str(self.select)])
            mf.file.save(self.crypt_txt_name, File(open(self.crypt_txt_path)))
            mf.can_down.add(self.member)
            mf.save()
        except:
            errlog.error('保存文件错误. 文件：' + self.file_base_name)
            errlog.error(traceback.format_exc())
            qer.end_match = timezone.now()
            qer.is_busy = False
            qer.save()
        finally:
            self.ice.destroy()
            util.try_delete_file(self.show_file_path)
            util.try_delete_file(self.crypt_file_path)
            util.try_delete_file(self.show_txt_path)
            util.try_delete_file(self.crypt_txt_path)
            filename = str(self.file_name) + PORT[str(self.select)] + '匹配成功,'
            qer.mapping_files = time.strftime('%Y%m%d-%H%M') + filename + qer.mapping_files
            behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + filename)
            qer.end_match = timezone.now()
            qer.is_busy = False
            qer.save()
        return True, '匹配完成'


def start_mapping(srcfile, member, select, ip, username, modal):
    switch = {
        'tyhx3': mapping_1,
        'xdhx3': mapping_1,
        'sjpl3': mapping_3t,
        'TelCheck': mapping_1,
        'IdPhoto': mapping_1,
        'TelPeriod': mapping_1,
        'TelStatus': mapping_1
    }
    try:
        qer = Queryer.objects.get(constom=member)
        if len(qer.mapping_files) > 1200:
            qer.mapping_files = qer.mapping_files[:1200]
            qer.save()
        filename = os.path.basename(srcfile.filename.name)
        filename = str(filename) + PORT[str(select)]
        state, info = switch[select](srcfile, member, select, ip, username, modal)
        qer = Queryer.objects.get(constom=member)
        if info.startswith('ice'):
            qer.mapping_files = filename + "ice超时匹配失败," + qer.mapping_files
            behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + filename + 'ice超时匹配失败')
            qer.is_busy = False
            qer.end_match = timezone.now()
            qer.save()
            return False, 'ice服务异常, 请稍后再试!'
        if not state:
            qer = Queryer.objects.get(constom=member)
            qer.mapping_files = time.strftime('%Y%m%d-%H%M%S') + filename + str(info) + '匹配失败,' + qer.mapping_files
            behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + filename + str(info) + '匹配失败')
            qer.is_busy = False
            qer.end_match = timezone.now()
            qer.save()
            errlog.error(filename + '匹配失败')
        return state, info
    except Exception:
        qer = Queryer.objects.get(constom=member)
        qer.is_busy = False
        qer.end_match = timezone.now()
        qer.save()
        errlog.exception('mapping wrong')
        return False, 'mapping wrong'


def mapping_3t(file, member, select, ip, username, modal):
    modal = 'EcCateThree'
    return mapping_1(file, member, select, ip, username, modal)


def mapping_1(file, member, select, ip, username, modal):
    max_map_list = []
    if isinstance(modal, list):
        for m in modal:
            obj = Meal.objects.get(name=str(m))
            try:
                max_map_list.append(int(obj.max_map))
            except TypeError:
                max_map_list.append(400000)
        max_map = min(max_map_list)
    else:
        obj = Interface.objects.get(name=str(modal))
        max_map = obj.max_map
    total = int(file.total_lines)
    if total > max_map:
        return False, '请求数量超限'

    qer = member.queryer
    filename = os.path.basename(str(file))
    try:
        op = Operator(qer)
        r, code = op.login()
        if not r:
            qer.is_busy = False
            qer.end_match = timezone.now()
            qer.save()
            return False, '查询者登陆错误, ' + code

        timestamp = time.strftime('%Y%m%d-%H%M')
        key = qer.name

        g_mapping_files[key] = {'filename': filename,
                                'splitor': file.splitor,
                                'fields': file.fields,
                                'skip': file.skip_lines,
                                'num': file.skip_lines,
                                'lines_queue': Queue(maxsize=5000),
                                'res_queue': Queue(maxsize=5000),
                                'is_cus_visible': False,
                                'is_succ': True,
                                'post_over': False,
                                'missed_line_num': 0}

        file_path = os.path.join(settings.MEDIA_ROOT, file.filename.name)
        rt = threading.Thread(
            target=read_file_to_queue,
            args=(file_path, g_mapping_files[key]['lines_queue'], g_mapping_files[key]['skip'], member.thread_num)
        )

        rt.start()

        threads = []
        to_pick = line_to_pick(file.fields)

        for i in range(member.thread_num):
            t = threading.Thread(target=query_line_from_queue, args=(key, op, file.fields, file.splitor, to_pick, modal))
            t.start()
            threads.append(t)

        t = threading.Thread(target=write_file_from_queue, args=(key, file, timestamp, member, modal, ip, username, select))
        t.start()

        rt.join()
        for tt in threads:
            tt.join()

        g_mapping_files[key]['res_queue'].put(None, block=True)
        t.join()
    except Exception:
        errlog.exception('Mapping出错：')
        errlog.error(traceback.format_exc())
    finally:
        qer.end_match = timezone.now()
        qer.is_busy = False
        if select == '5':
            filename = str(filename) + '信贷接口2.0' + '匹配成功,'
        elif select == '8':
            filename = str(filename) + '信贷接口3.0' + '匹配成功,'
        elif select == 'c':
            filename = str(filename) + '通用版接口3.0' + '匹配成功,'
        else:
            filename = str(filename) + PORT[select] + '匹配成功,'
        qer.mapping_files = time.strftime('%Y%m%d-%H%M') + filename + qer.mapping_files
        behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + filename)
        qer.save()
        try:
            del g_mapping_files[key]
        except UnboundLocalError:
            pass
    return True, '匹配完成'


def crypt_line(line, fields, splitor):
    fields = fields.split(',')
    line = line.split(splitor)
    res = []
    for i, fld in enumerate(fields):
        tmp = tt = line[i]
        if fld == 'id':
            if tt:
                if len(tt) == 18:
                    tmp = tt[:14] + '##' + tt[16] + '#'
                elif len(tt) == 15:
                    tmp = tt[:12] + '##' + tt[-1]
        elif fld == 'cell':
            if tt:
                tmp = tt[:7] + '####'
        elif fld == 'bank_card2' or fld == 'bank_card1':
            if tt and len(tt) > 12:
                tmp = tt[:12] + '#' * (len(tt[12:]) - 1) + tt[-1:]
        elif fld == 'email':
            if tt:
                if '@' in tt:
                    tmp = '####'+tt[tt.find('@'):]
        elif fld == 'name':
            if tt:
                tmp = '###'
        elif fld == 'home_tel' or fld == 'biz_tel':
            if tt:
                if '-' in tt:
                    tmp = tt.split('-')[0] + '-' + '####'
                else:
                    tmp = '####'
        res.append(tmp)
    return '\t'.join(res)


def write_file_from_queue(key, file, timestamp, member, modal, ip, username, select='1'):
    file_basename = os.path.basename(str(file))
    openid_prex = 'br%06d' % file.id
    # crypt_file_full_name = os.path.join(settings.MEDIA_ROOT, 'mappinged_file', '_'.join([os.path.splitext(file_basename)[0], timestamp, 'crypt']) + '.txt')
    crypt_file_name = '_'.join([os.path.splitext(file_basename)[0], timestamp, 'crypt']) + '.txt'
    crypt_fh = codecs.open(TMP_PATH + crypt_file_name, 'w', encoding='utf8')
    show_file_name = '_'.join([os.path.splitext(file_basename)[0], timestamp]) + '.txt'
    show_fh = codecs.open(TMP_PATH + show_file_name, 'w', encoding='utf8')
    res_queue = g_mapping_files[key]['res_queue']
    while True:
        js = res_queue.get(block=True)
        # json.dumps(js,ensure_ascii=False),'js'
        if js == None:
            break
        try:
            params = js['params']
            line_num = params['line_num']
            cypt_line = crypt_line(params['line'], g_mapping_files[key]['fields'], g_mapping_files[key]['splitor'])
            show_line = '\t'.join(params['line'].split(g_mapping_files[key]['splitor']))
            en_res = json.dumps(cn2en_json(js['res']),ensure_ascii=False)
        except:
            errlog.error('处理返回数据错误：' + traceback.format_exc())
        for prm,fh in [(show_line, show_fh), (cypt_line, crypt_fh)]:
            try:
                row = []
                row.append(openid_prex + ('%07d' % line_num))
                row.append(prm)
                row.append(en_res)
                fh.write('\t'.join(row) + '\n')
            except:
                errlog.error('匹配结果写入出错。文件：' + file_basename + '\t' + json.dumps(params))
                errlog.error(traceback.format_exc())

    crypt_fh.close()
    show_fh.close()
    try:
        file_from = ''
        if modal == 'EcCateThree':
            file_from = "商品消费评估—三级品类3.0"
        else:
            if select == 'xdhx3':
                meals = Meal.objects.filter(interface='信贷版接口3.0')
            elif select == 'tyhx3':
                meals = Meal.objects.filter(interface='通用版接口3.0')
            else:
                meals = Meal.objects.filter(interface='海纳api')
            for meal in meals:
                if meal.name in modal:
                    file_from = file_from + meal.chinese_name + ','
            file_from = PORT[select] + ':'+ file_from[:-1]

        LogInfo.objects.create(username=username, ip=ip, filename=file.filename, query_interface=file_from, num=file.total_lines)

        mf = MappingedFile(source_file=file, customer=file.custom, file_size=os.path.getsize(TMP_PATH + crypt_file_name), is_cus_visible=False, is_crypt=True, file_from=file_from, is_haina=False)
        mf.file.save(crypt_file_name, File(open(TMP_PATH + crypt_file_name)))
        mf.can_down.add(member)
        mf.save()

        mf = MappingedFile(source_file=file, customer=file.custom, file_size=os.path.getsize(TMP_PATH + show_file_name), is_cus_visible=False, is_crypt=False, file_from=file_from, is_haina=False)
        mf.file.save(show_file_name, File(open(TMP_PATH + show_file_name)))
        mf.can_down.add(member)
        mf.can_down.add(file.custom)
        mf.save()
    except:
        errlog.error('保存txt文件错误。文件：' + file_basename)
        errlog.error(traceback.format_exc())
    try:
        txt2csv(TMP_PATH + crypt_file_name, file.fields, modal, crypt = True)
        mf = MappingedFile(source_file=file, customer=file.custom, is_cus_visible=False, is_crypt=True, is_csv=True, file_from=file_from, is_haina=False)
        mf.file_size=os.path.getsize(TMP_PATH + crypt_file_name[:-3] + 'csv')
        mf.file.save(crypt_file_name[:-3] + 'csv', File(open(TMP_PATH + crypt_file_name[:-3] + 'csv')))
        mf.can_down.add(member)
        mf.save()

        txt2csv(TMP_PATH + show_file_name, file.fields, modal, crypt = False)
        mf = MappingedFile(source_file=file, customer=file.custom, is_cus_visible=False, is_crypt=False, is_csv=True, file_from=file_from, is_haina=False)
        mf.file_size=os.path.getsize(TMP_PATH + show_file_name[:-3] + 'csv')
        mf.file.save(show_file_name[:-3] + 'csv', File(open(TMP_PATH + show_file_name[:-3] + 'csv')))
        mf.can_down.add(file.custom)
        mf.save()
    except:
        errlog.error('保存csv文件错误。文件：' + file_basename)
        errlog.error(traceback.format_exc())
    finally:
        util.try_delete_file(TMP_PATH + crypt_file_name[:-3] + 'csv')
        util.try_delete_file(TMP_PATH + show_file_name[:-3] + 'csv')
        util.try_delete_file(TMP_PATH + crypt_file_name)
        util.try_delete_file(TMP_PATH + show_file_name)


def cn2en_json(jd):
    keys = [key.encode('utf-8') for key in jd.keys()]
    if 'Consumption' in keys:
        for month in jd['Consumption'].keys():
            for key in jd['Consumption'][month].keys():
                jd['Consumption'][month][CN_2_EN_EC_FR_CLASS[key.encode('utf-8').replace('其他', '其它')]] = jd['Consumption'][month][key]
                if CN_2_EN_EC_FR_CLASS[key.encode('utf-8').replace('其他', '其它')] != key:
                    del jd['Consumption'][month][key]
    if 'Media' in keys:
        for month in jd['Media'].keys():
            for key in jd['Media'][month].keys():
                if key == '钟表首饰$首饰$头饰':
                    del jd['Media'][month][key]
                    continue
                jd['Media'][month][CN_2_EN_MEDIA_FR_CLASS[key.encode('utf-8').replace('其他', '其它')]] = jd['Media'][month][key]
                if CN_2_EN_MEDIA_FR_CLASS[key.encode('utf-8').replace('其他', '其它')] != key:
                    del jd['Media'][month][key]
    return jd


def judge_res(res):
    if isinstance(res, dict):
        if 'code' in res.keys():
            if res['code'] == '00':
                if 'Flag' in res.keys():
                    for key, item in res['Flag'].items():
                        if item == '99':
                            return False
            if res['code'] == '100001':
                return False
            if res['code'] == '100002':
                if 'Flag' in res.keys():
                    for key, item in res['Flag'].items():
                        if item == '99':
                            return False
    return True


def query_line_from_queue(key, op, fields, splitor, to_pick, modal):
    lines_queue = g_mapping_files[key]['lines_queue']
    res_queue = g_mapping_files[key]['res_queue']
    while True:
        line = lines_queue.get(block=True)
        if line is None:
            break
        try:
            js = line2json(line['line'], fields, splitor, to_pick, modal)
            if not js:
                g_mapping_files[key]['missed_line_num'] += 1
                continue
            g_mapping_files[key]['num'] += 1
            res = op.get_one(json.dumps(js, ensure_ascii=False), modal)
            for x in range(4):
                if x == 3:
                    break
                if judge_res(res):
                    break
                else:
                    res = op.get_one(json.dumps(js, ensure_ascii=False), modal)
            res_queue.put({'res': res, 'params': line})
        except Exception:
            errlog.exception('查询画像出错')


def line_to_pick(fields):
    keys = FIELDS_2_SEND_FIELDS.keys()
    dd = {}
    for i, field in enumerate(fields.split(',')):
        if field in keys:
            dd[i] = FIELDS_2_SEND_FIELDS[field]
        else:
            dd[i] = field
    return dd


def line2json(line, fields, splitor, to_pick, modal):
    line = line.split(splitor.decode('string_escape'))
    xd3_meals = MealSort.objects.get(name='xd_sort')
    xd3_list = xd3_meals.sort.replace('|', ',').split(',')  # {'apply8' : u',ApplyLoan', 'location8': u',Location', 'special8': u',SpecialList_c', 'stab8': u',Stability_c', 'cons8': u',Consumption_c', 'media8': u',Media_c', 'account8': u',Accountchange', 'paycon8': u',PayConsumption', 'score_br8': u',brcreditpoint', 'score_cust8': u',ScoreCust', 'monthaccount8': u',AccountchangeMonth', 'telecheck8': ',TelecomCheck', 'scorebank8': u',scorebank', 'scorep2p8': u',scorep2p', 'scorecf8': u',scorecf'}
    hx3_meal = MealSort.objects.get(name='sort')
    hx3_list = hx3_meal.sort.split(',')  # {'auth3': ',Authentication', 'stab3': ',Stability', 'cons3': ',Consumption', 'title3': ',Title', 'media3': ',Media', 'assets3': ',Assets', 'brand3': ',Brand', 'special3': ',SpecialList'}
    if len(line) != len(fields.split(',')):
        return False
    selected_modal = u''
    for x in xd3_list:
        if x in modal:
            selected_modal = selected_modal + ',' + x
    for x in hx3_list:
        if x in modal:
            selected_modal = selected_modal + ',' +  x
    if modal == 'EcCateThree':
        selected_modal = 'EcCateThree'
    if modal == 'TelCheck':
        selected_modal = 'TelCheck'
    if modal == 'IdPhoto':
        selected_modal = 'IdPhoto'
    if modal == 'TelPeriod':
        selected_modal = 'TelPeriod'
    if modal == 'TelStatus':
        selected_modal = 'TelStatus'
    if selected_modal.startswith(','):
        selected_modal = selected_modal[1:]
    js = {'cell': [], 'mail': [], 'bank_id': '', 'meal': selected_modal}
    for index, key in to_pick.items():
        if key in ['cell', 'mail']:
            js[key].append(line[index].strip())
        elif key in ['bank_card1', 'bank_card2']:
            if len(line[index].strip()) > 12:
                js['bank_id'] = line[index].strip()
        else:
            if key == 'apply_date':
                if not line[index].strip():
                    js.update({key: time.strftime('%Y-%m-%d')})
                else:
                    js.update({key: line[index].strip()})
            if key == 'observe_date':
                if not line[index].strip():
                    js.update({key: time.strftime('%Y-%m-%d')})
                else:
                    js.update({key: line[index].strip()})
            elif key == 'other_var5':
                js.update({'brand_top_num': line[index].strip()})  
            elif key == 'other_var4':
                js.update({'sl_user_date': line[index].strip()})             
            else:
                js[key] = line[index].strip()
    return js


def read_file_to_queue(filepath, queue, skip, thread_num):
    _, ext = os.path.splitext(filepath)
    line_num = 0
    if ext == '.txt' or ext == '.csv':
        lines = util.iter_txt(filepath)
    elif ext == '.xls' or ext == '.xlsx':
        lines = util.iter_xls(filepath)
    for line in lines:
        line_num += 1
        if line_num > skip:
            queue.put({'line': line.strip(), 'line_num': line_num}, block=True)
    for i in range(thread_num):
        queue.put(None, block=True)


def check_fields_valid(fields):
    # TODO 调整字段检查
    if not fields:
        return False
    for key in fields:
        if not key.strip():
            return False
    if len(Set(fields)) < len(fields):
        return False
    return True


def create_head(modal, crypt):
    heads = []
    heads_dict = {}
    behavior1 = [AUTH, LOCATION, STABILITY, CONSUMPTION, TITLE, ASSETS, MEDIA, BRAND, SCORE]  # 通用2.0
    behavior5 = [LOCATION, STABILITY_C, CONSUMPTION_C, MEDIA_C, SCORE]  # 通用3.0
    xd3_dict = {'apply8': APPLY, 'location8': LOCATION, 'special8': SPECIAL_C, 'stab8': STABILITY_C, 'cons8': CONSUMPTION_C, 'media8': MEDIA_C, 'account8': ACCOUNT_XD3, 'paycon8': PAYCON, 'score_br8': SCOREBR, 'score_cust8': SCORECUST, 'telecheck8': TELECOMCHECK, 'monthaccount8': ACCOUNTCHANGEMONTH, 'scorebank8': SCOREBANK, 'scorep2p8': SCOREP2P, 'scorecf8': SCORECF}
    hx3_sort = MealSort.objects.get(name='sort_head')
    hx3_sort = hx3_sort.sort.split(',')

    hx3_dict = {'auth3': AUTH, 'stab3': STABILITY, 'cons3': CONSUMPTION, 'title3': TITLE, 'assets3': ASSETS, 'media3': MEDIA, 'brand3': BRAND, 'special3': SPECIAL}
    xd3_sort = MealSort.objects.get(name='xd_sort_head')
    xd3_sort = xd3_sort.sort.split(',')

    for sort in (xd3_sort, hx3_sort):
        for item in sort:
            if item and item in modal:
                meal = Meal.objects.get(name=item)
                meal_head = MealHead.objects.filter(meal=meal).order_by('id')
                for head in meal_head:
                    heads_dict.update({head.name: head.head})
                    heads.append(str(head.head))
    if modal == 'EcCateThree':
        heads = ECCATETHREE
    if modal == 'TelCheck':
        heads = ['flag_telCheck', 'operation', 'result']
    if modal == 'IdPhoto':
        heads = ['flag_idphoto', 'resCode', 'result', 'message', 'idCardPhoto']
    if modal == 'TelStatus':
        heads = ['flag_telstatus', 'result', 'operation', 'value', 'costTime']
    if modal == 'TelPeriod':
        heads = ['flag_telperiod', 'result', 'operation', 'value', 'costTime']    
    return heads, heads_dict


def txt2csv(ifp, fields, modal, language=2, crypt=False):
    head_ex = []
    all_rows = []
    head_yu = []
    with open(ifp) as ifh:
        heads, heads_dict = create_head(modal, crypt)
        heads_dict_keys = heads_dict.keys()
        xd3_flag_head = []
        
        tmp = ['openid']
        for field in fields.split(','):
            if field == 'tel_home':
                tmp.append('home_tel')
            elif field == 'tel_biz':
                tmp.append('biz_tel')
            else:
                tmp.append(field)
        for line in ifh:
            dd = {}
            lse = line.strip().split('\t')
            for i in range(len(tmp)):
                dd[tmp[i]] = lse[i]
            jd = json.loads(lse[-1])
            top_keys = jd.keys()
            if modal == 'TelCheck':  # 海纳api
                for top_key in top_keys:
                    if isinstance(jd[top_key], dict):
                        for key, value in jd[top_key].items():
                            dd.update({key: value})
                    else:
                        dd.update({top_key: jd[top_key]})
            elif modal == 'IdPhoto':  # 海纳api
                for top_key in top_keys:
                    if isinstance(jd[top_key], dict):
                        for key, value in jd[top_key].items():
                            if isinstance(jd[top_key][key], dict):
                                for x, y in jd[top_key][key].items():
                                    dd.update({x:y})
                            else:
                                dd.update({key: value})
                    else:
                        dd.update({top_key: jd[top_key]})

            elif modal == 'TelStatus':  # 海纳api
                for top_key in top_keys:
                    if isinstance(jd[top_key], dict):
                        for key, value in jd[top_key].items():
                            if isinstance(jd[top_key][key], dict):
                                for x, y in jd[top_key][key].items():
                                    dd.update({x:y})
                            else:
                                dd.update({key: value})
                    else:
                        dd.update({top_key: jd[top_key]})

            elif modal == 'TelPeriod':  # 海纳api
                for top_key in top_keys:
                    if isinstance(jd[top_key], dict):
                        for key, value in jd[top_key].items():
                            if isinstance(jd[top_key][key], dict):
                                for x, y in jd[top_key][key].items():
                                    dd.update({x:y})
                            else:
                                dd.update({key: value})
                    else:
                        dd.update({top_key: jd[top_key]})

            elif modal == 'EcCateThree':
                for top_key in top_keys:
                    if isinstance(jd[top_key], dict):
                        for level in jd[top_key].keys():
                            if level == 'month12':
                                if isinstance(jd[top_key][level], dict):
                                    for item in jd[top_key][level]:
                                        if isinstance(jd[top_key][level][item], dict):
                                            for value in jd[top_key][level][item]:
                                                item_str = str(item)
                                                # item_str,'item'
                                                if value == 'maxpay':
                                                    continue
                                                if value == 'pay':
                                                    if item in EC_DICT.keys():
                                                        for v in EC_DICT[item_str]:
                                                            if v[-1] == 'y':
                                                                dd.update({v: jd[top_key][level][item][value]})
                                                if value == 'visits':
                                                    if item in EC_DICT.keys():
                                                        for v in EC_DICT[item_str]:
                                                            if v[-1] == 's':
                                                                dd.update({v: jd[top_key][level][item][value]})
                                                if value == 'number':
                                                    if item in EC_DICT.keys():
                                                        for v in EC_DICT[item_str]:
                                                            if v[-1] == 'm':
                                                                dd.update({v: jd[top_key][level][item][value]})
                                                else:
                                                    continue
                                        else:
                                            dd.update({name: jd[top_key][level]})
                            if level == 'ecCateThree':
                                dd.update({'flag_EcCateThree': jd[top_key][level][0]})
                    else:
                        dd.update({top_key: jd[top_key]})
            else:
                for top_key in jd.keys():
                    if top_key == u'Flag':
                        xd3_flag_head = []
                        for top_type in jd[top_key].keys():
                            name = 'flag_' + top_type.encode('utf-8')
                            flag_state = name.startswith('flag_core')
                            xd3_flag_head.append(name)
                            if crypt and flag_state:
                                dd.update({name: jd[top_key][top_type]})
                            elif not crypt and flag_state:  
                                pass
                            else:
                                dd.update({name:jd[top_key][top_type]})
                        jd.pop('Flag')
                        continue                        
                        
                    if top_key == u'Execution':
                        if jd[top_key]:
                            for second_key in jd[top_key]:
                                if 'bad' in second_key[-4:]:
                                    for three in jd[top_key][second_key]:
                                        name = 'ex_bad'+second_key[-1]+'_'+three
                                        head_ex.append(name)
                                        dd.update({name:jd[top_key][second_key][three]})
                                if 'executed' in second_key[-10:]:
                                    for three in jd[top_key][second_key]:
                                        name = 'ex_execut'+second_key[-1]+'_'+three
                                        head_ex.append(name)
                                        dd.update({name:jd[top_key][second_key][three]})
                        head_ex = list(set(head_ex))
                        jd.pop('Execution')
                        continue

                    if top_key == u'Brand':
                        val_top6 = ''
                        if jd[top_key]:
                            for second_key in jd[top_key]:
                                if second_key in ["top1", "top2", "top3", "top4", "top5"]:
                                    dd.update({"brand_"+second_key: jd[top_key][second_key]})
                                else:
                                    val_top6 = val_top6 + jd[top_key][second_key] + ','
                        val_top6 = val_top6.rstrip(',')
                        dd.update({"brand_top6": val_top6})
                        jd.pop('Brand')
                        continue

                    if isinstance(jd[top_key], dict):
                        for second_key in jd[top_key]:
                            if isinstance(jd[top_key][second_key], dict):
                                for item in jd[top_key][second_key]:
                                    if isinstance(jd[top_key][second_key][item], dict):
                                        for one in jd[top_key][second_key][item]:
                                            if isinstance(jd[top_key][second_key][item][one], dict):
                                                for key in jd[top_key][second_key][item][one]:
                                                    if isinstance(jd[top_key][second_key][item][one][key], dict):
                                                        pass
                                                    else:
                                                        name = top_key + "_" + second_key + "_" + item + "_" + one + "_" + key
                                                        if name in heads_dict_keys:
                                                            name = heads_dict[name]
                                                        dd.update({name:jd[top_key][second_key][item][one][key]})
                                            else:
                                                name = top_key + "_" + second_key + "_" + item + "_" + one
                                                value = str(jd[top_key][second_key][item][one])
                                                if name in heads_dict_keys:
                                                    name = heads_dict[name]
                                                dd.update({name:value.replace('\N', 'null')})
                                    else:
                                        name = top_key + "_" + second_key + "_" + item
                                        value = str(jd[top_key][second_key][item])
                                        if name in heads_dict_keys:
                                            name = heads_dict[name]
                                        dd.update({name :value.replace('\N', 'null')})
                            else:
                                name = top_key + "_" + second_key
                                if name in heads_dict_keys:
                                    name = heads_dict[name]
                                dd.update({name: jd[top_key][second_key]})
                    else:
                        if top_key in heads_dict_keys:
                            top_key = heads_dict[top_key]
                        dd.update({top_key : jd[top_key]})
            all_rows.append(dd.copy())
            dd.clear()
        head_sort = ['ex_bad_name','ex_bad_cid','ex_bad_cidtype','ex_bad_datatime','ex_bad_datatypeid','ex_bad_datatype','ex_bad_leader','ex_bad_address','ex_bad_court','ex_bad_time','ex_bad_casenum','ex_bad_money','ex_bad_base','ex_bad_basecompany','ex_bad_obligation','ex_bad_lasttime','ex_bad_performance','ex_bad_concretesituation','ex_bad_breaktime','ex_bad_posttime','ex_bad_performedpart','ex_bad_unperformpart','ex_execut_name','ex_execut_cid','ex_execut_cidtype','ex_execut_datatime','ex_execut_datatypeid','ex_execut_datatype','ex_execut_court','ex_execut_time','ex_execut_casenum','ex_execut_money','ex_execut_statute','ex_execut_basic','ex_execut_basiccourt']
        for i in range(1,10):
            list1 = []
            headed = []
            for j in head_ex:
                if len(j) > 10:
                    if j[6] == str(i) or j[9] == str(i):
                        list1.append(j)
            for k in head_sort:
                if str(k[:6]+str(i)+k[6:]) in list1:
                    headed.append(k[:6]+str(i)+k[6:])
                if str(k[:9]+str(i)+k[9:]) in list1:
                    headed.append(k[:9]+str(i)+k[9:])
            head_yu = head_yu + headed
        heads = tmp + ['code', 'swift_number'] + xd3_flag_head + heads + head_yu
        for line in all_rows:
            for key in line.keys():
                if key not in heads:
                    line.pop(key)

        f = open(ifp[:-4] + '.csv', 'wb')
        f.write(u'\ufeff'.encode('utf-8'))

        csvfile = csv.DictWriter(f, heads, delimiter=',')
        csvfile.writeheader()
        for row in all_rows:
            try:
                csvfile.writerow(row)
            except:
                errlog.error('保存csv失败:' + json.dumps(row) + traceback.format_exc())
                continue
        f.close()


def check_before_mapping(filename, fields, splitor, skip_lines):
    fields = fields.strip().split(',')
    f_len = len(fields)
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
    cell_pattern = re.compile('^0\d{2,3}\d{7,8}$|^1[34578]\d{9}$')
    id_pattern = re.compile('^\w{15}$|^\w{18}$')
    date_index = []
    cell_index = []
    id_index = []
    date_num = ''
    cell_num = ''
    id_num = ''
    if 'observe_date' not in fields:
        return False, '数据观测日期为必标注项'
    if 'apply_date' in fields:
        date_index.append(fields.index('apply_date'))
        check_date = True
    else:
        check_date = False
    if 'cell' in fields:
        cell_index.append(fields.index('cell'))
        check_cell = True
    else:
        check_cell = False
    if 'id' in fields:
        id_index.append(fields.index('id'))
        check_id = True
    else:
        check_id = False
    line_num = 0
    _, ext = os.path.splitext(filename)
    if ext == '.xlsx' or ext == '.xls':
        iter_lines = util.iter_xls(filename)
    else:
        iter_lines = util.iter_txt(filename)

    msg_data = []
    for line in iter_lines:
        line_num += 1
        if line_num <= skip_lines:
            continue
        line = line.strip().split(splitor)
        if f_len != len(line):
            return False, str(line_num) + '行，列数不对'

        if check_date:

            for index in date_index:
                if line[index] and not date_pattern.match(line[index].strip()):
                    return False, '申请日期格式不正确'

        if check_cell:
            for index in cell_index:
                if not cell_pattern.match(line[index].strip()):
                    msg_data.append('手机号存在空值或格式错误\n')
            
        if check_id:
            for index in id_index:
                if not id_pattern.match(line[index].strip()):
                    msg_data.append('身份证号存在空值或格式错误\n')

    msg_data = ''.join(list(set(msg_data)))
    if msg_data:
        msg = '标注成功\n' + msg_data +'请确保上述问题不会影响到匹配结果.'
    else:
        msg = '标注成功'
    return True, msg
