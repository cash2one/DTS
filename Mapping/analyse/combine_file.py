#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.files import File

from collections import defaultdict
import traceback
import codecs
import os
import time
import logging

from analyse.models import MappingedFile
import util

errlog = logging.getLogger('daserr')

TMP_PATH = settings.MY_TMP_PATH


def third_to_source(third_file, source_files, member):
    third_fields = third_file.fields.split(",")
    third_index = [i for i, j in enumerate(third_fields) if j]
    third_res = defaultdict(str)
    skip_lines = third_file.skip_lines
    third_heads = ''

    for line in util.iter_txt(settings.MEDIA_ROOT + third_file.file.name):
        try:
            line = line.strip().split(third_file.splitor)
            if skip_lines > 0:
                if not third_heads:
                    third_heads = line[len(third_index):]
                    skip_lines -= 1
                continue
            key = []
            for index in third_index:
                key.append(line[index].strip())
            third_res['|'.join(key)]=third_file.splitor.join(line[len(third_index):]).strip()
        except:
            errlog.error('读取第三方匹配文件出错：' + third_file.file.name)
    for source_file in source_files.select_related('custom__analyst_custom'):
        source_fields = source_file.fields.split(',')
        source_index = []
        source_file_name = os.path.basename(str(source_file))
        tmp_file = source_file_name[:-4] + '_' + third_file.file_from + source_file_name[-4:]
        tmp_file_crypt = source_file_name[:-4] + '_' + third_file.file_from + '_crypt' + source_file_name[-4:]

        #crypt_fun = {}
        try:
            for fields in third_fields:
                source_index.append(source_fields.index(fields))
            #if fields == 'id':
                #crypt_fun[source_fields.index(fields)] = util.crypt_id
            #elif fields == 'cell':
                #crypt_fun[source_fields.index(fields)] = util.crypt_cell
            #elif fields == 'mail':
                #crypt_fun[source_fields.index(fields)] = util.crypt_mail
            #else:
                #continue
        except:
            errlog.error(traceback.format_exc())
            continue

        timestamp = time.strftime('%Y%m%d-%H%M')

        fh = codecs.open(TMP_PATH + timestamp + tmp_file, 'w', encoding='utf8')
        cfh = codecs.open(TMP_PATH + timestamp + tmp_file_crypt, 'w', encoding='utf8')
        fh.write('openid,' + ','.join(source_file.fields.split(',') + third_heads) + '\n')
        cfh.write('openid,' + ','.join(source_file.fields.split(',') + third_heads) + '\n')

        line_num = 0
        openid_prex = '%05d' % source_file.id
        skip_lines = source_file.skip_lines
        for line in util.iter_txt(settings.MEDIA_ROOT + source_file.filename.name):
            try:
                line = line.strip().split(source_file.splitor)
                line_num += 1
                if skip_lines > 0:
                    skip_lines -= 1
                    continue
                key = []
                for i in source_index:
                    key.append(line[i])
                if not third_res['|'.join(key)]:
                    continue
                tmp = [openid_prex + ('%07d' % line_num)] + line + [third_res['|'.join(key)]]
                fh.write(','.join(tmp) + '\n')
                ll = util.crypt_line(','.join(line), source_file.fields, ',')
                tmp = [openid_prex + ('%07d' % line_num)] + ll.split(',') + [third_res['|'.join(key)]]
                cfh.write(','.join(tmp) + '\n')
            except:
                errlog.error('合并第三方结果出错：', source_file.filename.name)
                errlog.error(traceback.format_exc())
        fh.close()
        cfh.close()
        try:
            mf = MappingedFile()
            mf.source_file = source_file
            mf.customer = source_file.custom
            mf.parent_file = third_file
            mf.file_size = os.path.getsize(TMP_PATH + timestamp + tmp_file)
            mf.file_from = third_file.file_from
            mf.is_third_file = True
            mf.is_crypt = False
            mf.file.save('_'.join([os.path.splitext(tmp_file)[0], timestamp]) + '.txt',
                    File(open(TMP_PATH + timestamp + tmp_file)))
            mf.can_down.add(member)
            mf.can_down.add(source_file.custom)
            mf.save()

            mf = MappingedFile()
            mf.source_file = source_file
            mf.customer = source_file.custom
            mf.parent_file = third_file
            mf.file_size = os.path.getsize(TMP_PATH + timestamp + tmp_file_crypt)
            mf.file_from = third_file.file_from
            mf.is_third_file = True
            mf.is_crypt = True
            mf.file.save('_'.join([os.path.splitext(tmp_file_crypt)[0], timestamp]) + '.txt',
                    File(open(TMP_PATH + timestamp + tmp_file_crypt)))
            mf.can_down.add(member)
            mf.can_down.add(source_file.custom.analyst_custom)
            mf.save()
        except:
            errlog.error(traceback.format_exc())
        finally:
            util.try_delete_file(TMP_PATH + timestamp + tmp_file)
            util.try_delete_file(TMP_PATH + timestamp + tmp_file_crypt)
