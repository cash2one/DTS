#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import md5
import xlrd
import traceback
import re
import subprocess
import random
import os
import datetime
import time, MySQLdb
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from django.db import connection
from django.conf import settings 

_letter_cases = "abcdefghjkmnpqrstuvwxy" # 小写字母，去除可能干扰的i，l，o，z
_upper_cases = _letter_cases.upper() # 大写字母
_numbers = ''.join(map(str, range(3, 10))) # 数字
init_chars = ''.join((_letter_cases, _upper_cases, _numbers))

logger = logging.getLogger('daserr')


def crypt_row(row,headers):
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
        return row


def sql_connect(sql):
    cursor = connection.cursor()
    # print sql,222
    # conn = MySQLdb.connect(host="localhost",user="root",passwd="123",db="Map",charset="utf8")
    # cursor = conn.cursor()     
    cursor.execute(sql)
    row = cursor.fetchall()
    return row

def get_md5(data):
    m = md5.new()
    m.update(data)
    return m.hexdigest()

def readxlrdfile(filepath, limit=-1):
    rs = []
    i = 1
    try:
        excel = xlrd.open_workbook(filepath)
        sheet = excel.sheet_by_index(0)
        for rownum in range(sheet.nrows):
            tl = []
            temp = sheet.row_values(rownum)
            for k in range(len(temp)):
                if isinstance(temp[k], float) :
                    if 17899 < int(temp[k]) < 55134 :
                        date_time = datetime.date.fromordinal(datetime.date(1899,12,31).toordinal()-1+int(temp[k])).strftime("%Y-%m-%d")
                        tl.append(date_time)
                    else:
                        tl.append(str(temp[k]).split('.')[0])
                elif isinstance(temp[k], int):
                    tl.append(str(temp[k]))
                else:
                    tl.append(temp[k])
            rs.append(','.join(tl))
            if limit >0 and i>limit:
                break
            i = i+1
    except :
        logger.error("excel something wrong " + traceback.format_exc())
    return rs

    
def readtxtfile(filepath, limit=-1):
    rs = []
    i = 0
    try:
        # f = open(filepath, 'r')
        with open(filepath, 'r') as f:
            for line in f:
                rs.append(line.replace('\n','').replace('\t', '\\t').replace('\r', ''))
                if limit > 0 and i>limit:
                    break
                i += 1
        #f.close()
    except:
        #f.close()
        logger.error('读取txt文件：' + str(filepath))
        logger.error(traceback.format_exc())
    return rs


def readfilelines(filepath, line_num):
    if filepath[-3:] in  ['txt', 'csv']:
        return True, readtxtfile(filepath, line_num)
    elif filepath[-3:]  == 'xls':
        return True, readxlrdfile(filepath, line_num)
    elif filepath[-4:] == 'xlsx':
        return True, readxlrdfile(filepath, line_num)
    else:
        return False, '不支持该文件格式！'


def iter_txt(file):
    if os.path.isfile(file):
        with open(file) as f:
            for line in f:
                yield line


def iter_xls(file):
    excel = xlrd.open_workbook(file)
    sheet = excel.sheet_by_index(0)
    for rownum in xrange(sheet.nrows):
        tl = []
        temp = sheet.row_values(rownum)
        for k in range(len(temp)):
            if type(temp[k]) is float:
                if 17899 < int(temp[k]) < 55134 :
                    date_time = datetime.date.fromordinal(datetime.date(1899,12,31).toordinal()-1+int(temp[k])).strftime("%Y-%m-%d")
                    tl.append(date_time)
                else:
                    tl.append(str(temp[k]).split(".")[0])
            elif type(temp[k]) is int:
                tl.append(str(temp[k]))
            else:
                tl.append(temp[k])
        yield ','.join(tl)

def gen_passwd(pass_length):
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mypw = ""

    for i in range(pass_length):
        next_index = random.randrange(len(alphabet))
        mypw = mypw + alphabet[next_index]
    return mypw

def crypt_id(id_no):
    if id_no:
        if len(id_no) == 18:
            id_no = id_no[:14] + '##' + id_no[16] + '#'
        elif len(id_no) == 15:
            id_no = id_no[:12] + '##' + id_no[-1]
        return id_no
    return ''

def crypt_cell(cell):
    if cell:
        return cell[:7] + '####'
    return ''

def crypt_mail(mail):
    if mail:
        if '@' in mail:
            return '####'+mail[mail.find('@'):]
        else:
            return mail
    return ''

def try_delete_file(filepath):
    try:
        os.remove(filepath)
    except:
        pass

def crypt_line(line, fields, splitor):
    fields = fields.split(',')
    line = line.split(splitor)
    res = []
    tmp = ''
    for i, fld in enumerate(fields):
        tmp = tt = line[i]
        if fld == 'id':
            if tt:
                if len(tt) == 18:
                    tmp = tt[:14] + '##' + tt[16] + '#'
                elif len(tt) == 15:
                    tmp = tt[:12] + '##' + tt[-1]
        elif fld == 'id_num':
            if tt:
                if len(tt) == 18:
                    tmp = tt[:14] + '##' + tt[16] + '#'
                elif len(tt) == 15:
                    tmp = tt[:12] + '##' + tt[-1]
        elif fld == 'cell':
            if tt:
                tmp = tt[:7] + '####'
        elif fld == 'bank_card2' or fld == 'bank_card1':
            if len(tt) > 10:
                tmp = tt[:12] + '#' * (len(tt[12:]) - 1) + tt[-1:]
        elif fld == 'email':
            if tt:
                if '@' in tt:
                    tmp = '####'+tt[tt.find('@'):]
        elif fld == 'name':
            if tt:
                tmp = '###'
        elif fld == 'tel_home' or fld == 'tel_biz':
            if tt:
                if '-' in tt:
                    tmp = tt.split('-')[0] + '-' + '####'
                else:
                    tmp = '####'
        res.append(tmp)
    return splitor.join(res)

def create_validate_code(size=(120, 30),
                         chars=init_chars,
                         img_type="GIF",
                         mode="RGB",
                         bg_color=(255, 255, 255),
                         fg_color=(0, 0, 255),
                         font_size=18,
                         font_type="/home/zy/Project/Mapping_celery/Mapping/static/fonts/ae_AlArabiya.ttf",
                         length=4,
                         draw_lines=True,
                         n_line=(1, 2),
                         draw_points=True,
                         point_chance = 2):
    '''
    @todo: 生成验证码图片
    @param size: 图片的大小，格式（宽，高），默认为(120, 30)
    @param chars: 允许的字符集合，格式字符串
    @param img_type: 图片保存的格式，默认为GIF，可选的为GIF，JPEG，TIFF，PNG
    @param mode: 图片模式，默认为RGB
    @param bg_color: 背景颜色，默认为白色
    @param fg_color: 前景色，验证码字符颜色，默认为蓝色#0000FF
    @param font_size: 验证码字体大小
    @param font_type: 验证码字体，默认为 ae_AlArabiya.ttf
    @param length: 验证码字符个数
    @param draw_lines: 是否划干扰线
    @param n_lines: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
    @param draw_points: 是否画干扰点
    @param point_chance: 干扰点出现的概率，大小范围[0, 100]
    @return: [0]: PIL Image实例
    @return: [1]: 验证码图片中的字符串
    '''

    width, height = size # 宽， 高
    img = Image.new(mode, size, bg_color) # 创建图形
    draw = ImageDraw.Draw(img) # 创建画笔

    def get_chars():
        '''生成给定长度的字符串，返回列表格式'''
        return random.sample(chars, length)

    def create_lines():
        '''绘制干扰线'''
        line_num = random.randint(*n_line) # 干扰线条数

        for i in range(line_num):
            # 起始点
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            #结束点
            end = (random.randint(0, size[0]), random.randint(0, size[1]))
            draw.line([begin, end], fill=(0, 0, 0))

    def create_points():
        '''绘制干扰点'''
        chance = min(100, max(0, int(point_chance))) # 大小限制在[0, 100]

        for w in xrange(width):
            for h in xrange(height):
                tmp = random.randint(0, 100)
                if tmp > 100 - chance:
                    draw.point((w, h), fill=(0, 0, 0))

    def create_strs():
        '''绘制验证码字符'''
        c_chars = get_chars()
        strs = ' %s ' % ' '.join(c_chars) # 每个字符前后以空格隔开

        font = ImageFont.truetype(font_type, font_size)
        font_width, font_height = font.getsize(strs)

        draw.text(((width - font_width) / 3, (height - font_height) / 3),
                    strs, font=font, fill=fg_color)

        return ''.join(c_chars)

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    strs = create_strs()

    # 图形扭曲参数
    params = [1 - float(random.randint(1, 2)) / 100,
              0,
              0,
              0,
              1 - float(random.randint(1, 10)) / 100,
              float(random.randint(1, 2)) / 500,
              0.001,
              float(random.randint(1, 2)) / 500
              ]
    img = img.transform(size, Image.PERSPECTIVE, params) # 创建扭曲

    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE) # 滤镜，边界加强（阈值更大）

    return img, strs

def check_passwd_strong(passwd):
    if not re.search(r'\d', passwd):
        return False
    if not re.search(r'[a-z]', passwd):
        return False
    for char in '@#~$!%^&*()_-.,?><=+-':
        if char in passwd:
            return True
    return False

