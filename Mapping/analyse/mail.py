#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import smtplib 
import logging
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

errlog = logging.getLogger('daserr')


def send_mail(receiver,subject,content):
    if not receiver:
        return False
    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", receiver) is None:
        errlog.error("send_mail , the email address is wrong" + str(receiver))
        return False
    sender = "dts@100credit.com"
    username = 'dts@100credit.com'
    password = '018660'

    msgRoot = MIMEText(content,_subtype='plain',_charset='utf-8')
    msgRoot['Subject'] = Header(subject, 'utf-8')
    msgRoot["From"] = sender
    msgRoot["To"] = receiver

    smtp = smtplib.SMTP()
    smtp.connect('smtp.100credit.com')
    smtp.login(username,password)
    smtp.sendmail(sender,receiver,msgRoot.as_string())
    smtp.quit()


def mail_to_coder(receiver,subject,content):
    sender = "dts@100credit.com"
    username = 'dts@100credit.com'
    password = '018660'

    msgRoot = MIMEText(content,'html','utf-8')
    msgRoot['Subject'] = Header(subject, 'utf-8')
    msgRoot["From"] = sender
    msgRoot["To"] = receiver

    smtp = smtplib.SMTP()
    smtp.connect('smtp.100credit.com')
    smtp.login(username,password)
    smtp.sendmail(sender,receiver,msgRoot.as_string())
    smtp.quit()



def send_attmail(receiver,file_path,subject,msg):
    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", receiver) is None:
        errlog.error("send_mail , the email address is wrong" + str(receiver))
        return False
    sender = "dts@100credit.com"
    username = 'dts@100credit.com'
    password = '018660'

    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = Header(subject, 'utf-8')

    att = MIMEText(open(file_path,'rb').read(),'base64','utf-8')
    att['Content-Type'] = 'application/octet-stream'
    file_name = os.path.basename(file_path)
    file_att ='attachment; filename="fn"'
    file_att = file_att.replace('fn',file_name)
    att['Content-Disposition'] = file_att
    content = MIMEText(msg, 'plain','utf-8')
    msgRoot["Accept-Charset"]="ISO-8859-1,utf-8"
    msgRoot.attach(content)

    msgRoot.attach(att)
    smtp = smtplib.SMTP()
    smtp.connect('smtp.100credit.com')
    smtp.login(username,password)
    smtp.sendmail(sender,receiver,msgRoot.as_string())
    smtp.quit()
