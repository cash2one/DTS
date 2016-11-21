#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.views.generic import View
from django.http import HttpResponse, Http404, JsonResponse
from django.db import transaction
from django.contrib.auth.models import User
from django.views.decorators.csrf import  csrf_exempt



import os
import time
import subprocess
import xlrd
import json
import traceback
import logging
import re
import smtplib

from account.models import Member
from analyse.models import SourceFile, MappingedFile, ReportFile
from analyse.util import check_passwd_strong
from analyse.mail import send_mail, send_attmail
from util import gen_passwd

# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 25M  - 26214400
# 50MB - 5242880

#MAX_SOURCE_FILE_SIZE = 26214400
UP_FILE_MAX_LINES = 400001
errlog = logging.getLogger('daserr')
behaviorlog = logging.getLogger('behavior')

MODAL = '''您好，以下是贵公司在百融数据测试系统（DTS）的账号基本信息
DTS网址：https://dts.100credit.com/
账号：%s 密码：%s
您可以登录DTS，将测试数据上传至DTS，完成测试后，分析师会将脱敏后的匹配结果与分析报告发给您。

DTS简单说明：
1、为了保证贵公司数据安全，首次登录须修改登录密码；
2、根据页面提示，上传需要测试的数据文件； 
3、为了保证数据安全，DTS采用了IP限制策略，请按照如下方法操作，否则无法登陆DTS：
打开DTS链接，页面将会显示“您的IP是:xxx.xxx.xxx.xx,不在授权范围以内，请联系与您沟通的工作人员”。按照提示联系工作人员，添加ip后方可使用。
系统邮件，请勿回复，谢谢！
'''


class UpSourceFileView(View):
    def get(self, request):
        return render(request, 'custom/up_source_file.html')

    @transaction.atomic
    def post(self, request):
        file = request.FILES.get('file', '')
        extra_info = request.POST.get('extra_info', '')
        err = []
        if not file:
            err.append('请选择一个文件！')
            return render(request, 'custom/up_source_file.html', {'err': '\n'.join(err)})
        _, file_ext = os.path.splitext(file.name)
        if file_ext[1:] not in ['txt', 'xlsx', 'xls', 'csv']:
            err.append('文件格式必须为txt, xlsx, xls, csv')
            return render(request, 'custom/up_source_file.html', {'err': '\n'.join(err)})
        if file_ext in ['.xls','.xlsx']:
            try:
                print file.temporary_file_path(), type(file.temporary_file_path())
                excel = xlrd.open_workbook(file.temporary_file_path())
                sheet = excel.sheet_by_index(0)
                total_lines = sheet.nrows
            except Exception:
                err.append("excel文件处理错误,请换个格式！")
                return render(request, 'custom/up_source_file.html', {'err': '\n'.join(err)})
                errlog.error('xlrd处理客户上传文件错误'+traceback.format_exc())
        else:
            total_lines = int(subprocess.check_output('cat %s | wc -l' % file.temporary_file_path(), shell=True))
        if total_lines > UP_FILE_MAX_LINES:
            err.append('文件行数不得超过40万')
            return render(request, 'custom/up_source_file.html', {'err': '<br>'.join(err)})
        cum_analyse = request.user.member.analyst_custom
        rece = cum_analyse.email
        subject = "您的客户：" + request.user.member.name + "上传了文件：" + file.name
        behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + '客户名为：' + request.user.member.name + ' 上传了' + file.name + '文件')
        content = "请登录DTS查看。"
        try:
            send_mail(rece,subject, content)
        except Exception:
            err.append('分析师邮箱错误，请联系与您沟通的工作人员！')
            return render(request, 'custom/up_source_file.html', {'err': '<br>'.join(err)})

        member = request.user.member
        sf = SourceFile(custom=member, filename=file, extra_info=extra_info,
                file_size=file.size, file_from=request.user.member.name)
        sf.total_lines = total_lines
        basename, ext = os.path.splitext(file.name)
        filename = '_'.join([request.user.member.name, basename, time.strftime('%Y%m%d-%H%M')]) + ext
        sf.filename.save(filename, file)
        sf.can_down.add(member)
        sf.can_down.add(member.datatran_custom)
        sf.save()
        return redirect('/als/custom/source_files/')


@csrf_exempt
def create_user(request):
    try:
        login_name = request.POST.get('login_name', '')
        user_name = request.POST.get('user_name', '')
        email = request.POST.get('email', '')
        analy = request.POST.get('analy', '')
        city = request.POST.get('city' '')
        from_sta = request.POST.get('state', 'crm')
        analy = analy.replace("a3","分析师4").replace('俞浩明', '俞浩明_分析').replace('蒋宏', '蒋宏_分析')
        analy = analy.strip()

        errlog.error("create custom from crm :" + login_name + user_name + email + analy + city)
        if email:
            email = email.strip()
            if  not re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email):
                return JsonResponse({'msg': 'emailFormatError'})
        if login_name:
            try:
                cus_name = User.objects.get(username=login_name)
                if cus_name:
                    return JsonResponse({'msg': 'login_nameError'})
            except Exception, e:
                errlog.error('create user ,login_name is :' + str(login_name))
        try:
            cus_email = Member.objects.get(email=email, mem_type=1)
            if cus_email:
                return JsonResponse({'msg': "emailError"})
        except Exception, e:
            errlog.error('create user, email is :' + str(email))
        analy = Member.objects.get(name=analy)
        datatran_custom = Member.objects.get(name='数据检查小红')

        passwd = gen_passwd(6)
        user = User.objects.create_user(login_name,'', passwd)
        user.is_staff = True
        user.save
        userd = User.objects.get(username=login_name)
        member = Member(user=userd,
                analyst_custom=analy,
                datatran_custom= datatran_custom,
                email=email,
                name=user_name,
                custom_city=city)
        member.save()
        subject = "百融数据 测试系统（DTS）账号"
        content = MODAL %(login_name, passwd)
        content_ana = "已经给客户%s开通DTS帐号，帐号密码已通过邮件发送给%s" %(user_name, user_name)
        send_mail(email, subject, content)
        if True:
            sub = "客户帐号已开通"
            send_mail(analy.email, sub, content_ana)
            behaviorlog.error('crm开通帐号' + user_name + ',分析师是：' + str(analy.name) )
            return JsonResponse({'msg': 'success'})
    except Exception, e:
        errlog.error("with crm ,create custon error :" + traceback.format_exc())
    return JsonResponse({'msg': 'success'})


class SourceFileListView(View):
    def get(self, request):
        page_num = request.GET.get('page', 1)
        source_files = SourceFile.objects.filter(custom=request.user.member, is_delete=False).order_by('-create_time')
        p = Paginator(source_files, 15)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'custom/source_file_list.html', {'page': page})


class MappingedFileView(View):
    def get(self, request):
        page_num = request.GET.get('page', 1)
        fileid = None
        try:
            fileid = int(request.GET.get('fileid'))
            source_file = SourceFile.objects.get(pk=fileid)
            if source_file.is_delete:
                raise Http404
        except:
            raise Http404
        source_files = MappingedFile.objects.filter(customer=request.user.member, is_crypt=False, is_cus_visible=True, is_haina=False, source_file=fileid).order_by('-create_time')
        p = Paginator(source_files, 15)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'custom/mappinged_file_list.html', {'page': page, 'fileid': fileid})

class ReportFileView(View):
    def get(self, request):
        file_id = request.GET.get('fileid')
        page_num = request.GET.get('fileid')
        try:
            file_id = int(file_id)
            source_file = SourceFile.objects.get(pk=file_id)
            if source_file.is_delete:
                raise Http404
        except:
            raise Http404
        files = ReportFile.objects.filter(customer=request.user.member, source_file=file_id).order_by('-create_time')[:50]
        p=Paginator(files, 15)
        try:
            page = p.page(int(page_num))
        except Exception, e:
            page = p.page(1)
        return render(request, 'custom/report_files.html', {'page': page, 'fileid': file_id})


class FirstModifyPasswd(View):
    def get(self, request):
        return render(request, 'custom/first_modify_passwd.html')

    @transaction.atomic
    def post(self, request):
        new_passwd = request.POST.get('new_passwd', '').strip()
        confirm_passwd = request.POST.get('confirm_passwd', '').strip()

        user = request.user
        if new_passwd != confirm_passwd:
            return render(request, 'custom/first_modify_passwd.html', {'err': '新密码输入不一致'})
        if len(new_passwd) < 6 or len(new_passwd) > 30:
            return render(request, 'custom/first_modify_passwd.html', {'err': '密码长度为大于6小于30位'})
        # if not check_passwd_strong(new_passwd):
        #     return render(request, 'custom/first_modify_passwd.html', {'err': '密码强度不够'})
        user.set_password(new_passwd)
        user.save()
        user.member.b_first_modify_passwd = True
        user.member.save()
        return redirect('/')


class DeleteFileView(View):
    def get(self, request):
        fileid = request.GET.get('fileid', '')
        file = SourceFile.objects.get(pk=fileid)
        file.is_delete = True
        file.save()
        return HttpResponse(json.dumps('删除成功'), content_type='application/json')
        
