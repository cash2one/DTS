# coding=utf-8
# !/usr/bin/python

import time
import imaplib
import email
import sys
import os
import re
import logging
import traceback
import subprocess
from django.http import HttpResponse, request
from account.models import Member
from mail import send_mail
from models import SourceFile
from django.core.files import File
from django.conf import settings
from django.views.generic import View



TMP_PATH = settings.MY_TMP_PATH

errlog = logging.getLogger('daserr')
behaviorlog = logging.getLogger('behavior')

# 保存文件方法（都是保存在指定的根目录下）
def save_file(filename, data, path):
    try:
        filepath = path + filename
        f = open(filepath, 'wb')
        f.write(data)
        f.close()
    except Exception, e:
        errlog.error('保存文件错误, 原因为: struct error-- '+str(traceback.format_exc()))


# 字符编码转换方法
def my_unicode(s, encoding):
    if encoding:
        return unicode(s, encoding)
    else:
        return unicode(s)


# 解析邮件方法（区分出正文与附件）
def parse_email(msg, mypath):
    mailContent = None
    contenttype = None
    suffix = None
    file_path = None
    for part in msg.walk():
         if not part.is_multipart():
            contenttype = part.get_content_type()   
            filename = part.get_filename()
            charset = part.get_charset()
            # 是否有附件
            if filename:
                h = email.Header.Header(filename)
                dh = email.Header.decode_header(h)
                fname = dh[0][0]
                encodeStr = dh[0][1]
                if encodeStr != None:
                    if charset == None:
                        fname = fname.decode(encodeStr, 'utf-8')
                    else:
                        fname = fname.decode(encodeStr, charset)
                data = part.get_payload(decode=True)
                # 保存附件
                if fname is not None or fname != '':
                    if str(fname)[-4:] in ('.png', '.gif', '.jpg', 'jpeg', '.bmp', '.pdf'):
                        continue
                    save_file(fname, data, mypath)
                    file_path = mypath + fname
            else:
                if contenttype in ['text/plain']:
                    suffix = '.txt'
                if contenttype in ['text/html']:
                    suffix = '.htm'
                if charset == None:
                    mailContent = part.get_payload(decode=True)
                else:
                    mailContent = part.get_payload(decode=True).decode(charset)
    return (file_path, mailContent, suffix)

 
def deal_mail(request):
    mailhost = 'pop.100credit.com'
    account = settings.MAIL
    password = settings.MAIL_PASSWD
    mypath = TMP_PATH
    port = 993
    for x in range(3):
        try:
            imapServer = imaplib.IMAP4_SSL(mailhost, port)
            break
        except Exception, e:
            if x == 2:
                errlog.error("ssl get wrong")
                return False
    for num in range(3):
        try:
            imapServer.login(account, password)
            break
        except Exception, e:
            if x == 2:
                errlog.error("shake hands wrong" )
                return False
    imapServer.select()
    # 邮件状态设置，新邮件为Unseen
    resp, items = imapServer.search(None, "Unseen")
    for i in items[0].split():
        # get information of email
        resp, mailData = imapServer.fetch(i, "(RFC822)")
        mailText = mailData[0][1]
        msg = email.message_from_string(mailText)
        ls = msg["From"].split(' ')
        if(len(ls) == 2):
            fromname = email.Header.decode_header((ls[0]).strip('\"'))
            recver = my_unicode(fromname[0][0], fromname[0][1]) + ls[1]
        else:
            recver = msg["From"]
        file_path, mailContent, suffix = parse_email(msg, mypath)
        if file_path is None:
           continue

        # 发送邮件
        regex = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}\b", re.IGNORECASE)
        recver = re.findall(regex, recver)[0]
        try:
            member = Member.objects.get(email = recver, mem_type = 1)
        except Member.DoesNotExist:
            errlog.error("there is no custom")
            continue

        try:
            msg = "通过邮件上传"
            file_size = os.path.getsize(file_path)
            sf = SourceFile()
            sf.custom = member
            fpath, upload_fname = os.path.split(file_path)
            if str(upload_fname).endswith(".tar.gz") or str(upload_fname).endswith(".tar.bz"):
                basename = str(upload_fname)[:-7]
                ext = str(upload_fname)[-7:]
            elif str(upload_fname).endswith(".tar.bz2"):
                basename = str(upload_fname)[:-8]
                ext = str(upload_fname)[-8:]
            else :
                basename, ext = os.path.splitext(upload_fname)
            filename = '_'.join([member.name, basename, time.strftime('%Y%m%d-%H%M')]) + ext
            total_lines = int(subprocess.check_output('cat %s | wc -l' % file_path, shell=True))
            sf.filename.save(filename,File(open(file_path)))
            sf.extra_info = msg
            sf.file_size = file_size
            sf.total_lines  = total_lines
            sf.file_from = member.name
            sf.can_down.add(member)
            sf.can_down.add(member.datatran_custom)
            sf.save()
            os.remove(file_path)

            behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + '客户名为：' + member.name + ' 通过邮件上传了' + filename + '文件')
            msg = "您的客户" + member.name + "您的客户上传了文件"
            re_msg = "百融DTS文件上传成功"
            content = "您刚刚发邮件的附件文件已成功上传DTS，有结果后分析师会联系您。"
            send_mail(recver, re_msg, content)
            if not member.analyst_custom.email:
                errlog.error(str(member.name) + "this custom don't have analyse ")
                continue
            ana_recver = member.analyst_custom.email
            content = "您的客户" + member.name + "您的客户上传了文件,请登录DTS查看。"
            send_mail(ana_recver, msg, content)
        except Exception, e:
            errlog.error("文件上传失败" + str(traceback.format_exc()))
            msg = "百融DTS文件上传失败"
            msg_content = "刚刚您上传文件失败，请再次上传，或者联系您对应的百融分析师"
            send_mail(recver, msg, msg_content)

    imapServer.close()
    imapServer.logout()

