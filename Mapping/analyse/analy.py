#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from django.views.generic import View
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.db import transaction
from celery.task.control import revoke
from django.utils import timezone
from django.views.decorators.csrf import  csrf_exempt
from django.contrib.auth.models import User

import json
import os
import cStringIO as StringIO
import traceback
import logging
import re
import tasks
import csv
import time
import random
import datetime
import codecs
import smtplib

from analyse.models import SourceFile, MappingedFile, ReportFile, ColletDate, Coder
from account.models import Member, Queryer, Filter
from models import MealHead, Meal, MealSort, Interface, LogInfo
from util import readfilelines, try_delete_file, iter_txt, crypt_line, iter_xls, sql_connect
import mapping
from analyse.mail import send_attmail, mail_to_coder
from mapping_headers import MARK_HEAD

errlog = logging.getLogger('daserr')
behaviorlog = logging.getLogger('behavior')

PER_PAGE_NUM = 15

Z_COMMAND = "7za a -p%s -tzip %s %s"
H_COMMAND = 'cp %s %s'

TMP_PATH = settings.MY_TMP_PATH
MEDIA_ROOT = settings.MEDIA_ROOT


def choice(request):
    username = request.GET.get("username")
    apicode =request.GET.get("apicode")
    user = User.objects.get(username=username)
    member = user.member
    old_queryer = Queryer.objects.get(constom=member)
    old_queryer.constom = None
    old_queryer.save()
    try:
        new_queryer = Queryer.objects.get(apicode=apicode)
    except Exception:
        errlog.error('后台apicode错误：'+ traceback.format_exc())
        return HttpResponse('apicode配置错误，请联系管理员！')
    new_queryer.constom = member
    new_queryer.save()
    return HttpResponseRedirect('/als/analyst/cus_files/')


class CusFilesView(View):
    def get(self, request):
        query_custom = request.GET.get('cus_id', '')
        query_time1= request.GET.get('time1', '')
        query_time2 = request.GET.get('time2', '')
        query_file_name = request.GET.get('file_name', '')
        page_num = request.GET.get('page', 1)
        user = request.user
        analy = request.user.member
        name = request.user.username

        filter_obj = Filter.objects.all()[0].api_list
        analy_code_list = filter_obj.split(';')
        obj = []
        for i in analy_code_list:
            analy_code = i.split(':')
            if name in analy_code:
                obj = analy_code[1].split(',')
                break
        try:
            apicode = analy.queryer.apicode
        except Exception:
            return HttpResponse('apicode配置错误，请联系管理员！')
        
        apermission = analy.permission
        interfaces = Interface.objects.all()
        interface_names = {}
        for interface in interfaces:
            interface_names.update({interface.name: interface.chinese_name})
        permission = {}
        if ',' in apermission:
            apermissions = apermission.split(',')
            for per in apermissions:
                if ':' in per:
                    key, status = per.split(':')
                    if status == '1' and key in interface_names.keys():
                        permission.update({key: interface_names[key]})
        permission_sort = ['tyhx3', 'xdhx3', 'sjpl3', "zyhl_ydsj1", "zyhl_ydsj2", "zyhl_ydsj3", "fy_mbtwo", 'TelPeriod', 'xz_sjzwzt', 'blxxd', 'xz_sjzwsc', 'xz_sjsys', 'TelStatus', 'qcc_qygjzmhcx', 'qcc_dwtz', 'xb_shsb', 'sy_sfztwo', 'rjh_ltsz', 'hjxxcx', 'IdPhoto', 'TelCheck', 'ylzc_zfxfxwph', 'lw_clztcx', 'lw_cphsfzyz', 'zhx_hvvkjzpf', 'zhx_hvgcfxbq', 'zhx_hvgjfxbq', 'qcc_qydwtz', 'qcc_qydwtztp', 'qcc_qyygdgxtztp', 'qcc_qyszgxzpcx','hjxxcx','xlxxcx','fy_dxyz','fy_ltyz', 'fy_ydyz','dn_ftl','dn_tl','dn_tb','dn_state','dn_balance','dn_mcip', 'loss', 'szdj', 'mmd', 'ldzh', 'jz', 'shbc', 'shbcty', 'bchx', 'ltst|ltid|dxst|dxid', 'bcjq', 'ldtj', 'ldv2', 'xxx001', 'rlsb', 'qyzh', 'dd', 'idjy', 'qyjb', 'qytz', 'dwtz', 'clwz', 'idnph', 'zcx_sxzx', 'blxxb', 'zdy_vuici', 'zdy_getState', 'zdy_gtll', 'fy_ydcmoi','fy_ydms','fy_ydcmci','zskj_idjy', 'hjkj_bcjq']
        hx3_portrait = analy.portrait3_permission
        hx_pers = hx3_portrait.split(',')
        hx_per_list = []
        for hx_per in hx_pers:
            if ':' in hx_per:
                modal, status = hx_per.split(':')
                if status == '1':
                    hx_per_list.append(modal)
        hx3_permission = {}
        hx3_list = []
        hx3_sort = []
        hx_meals = Meal.objects.filter()
        if hx_meals:
            for meal in hx_meals:
                if meal.name in hx_per_list:
                    hx3_permission.update({meal.name: meal.chinese_name})
        js_hx3_sort =  MealSort.objects.get(name='sort')
        if js_hx3_sort:
            head_sort = js_hx3_sort.sort.split(',')
            js_hx3_sort = js_hx3_sort.sort
            for one in head_sort:
                hx3_sort.append(one)
        xd3_credit = analy.credit3_permission
        xd3_credit2 = analy.credit3_permission2
        xd_per_list = []
        xd_pers = xd3_credit.split(',')
        for xd_per in xd_pers:
            if ':' in xd_per:
                modal, status = xd_per.split(':')
                if status == '1':
                    xd_per_list.append(modal)
        xd3_permission = {}
        xd3_list = []
        xd3_sort = []
        xd3_meals= Meal.objects.filter(interface='信贷版接口3.0')
        if xd3_meals:
            for meal in xd3_meals:
                if meal.name in xd_per_list:
                    xd3_permission.update({meal.name: meal.chinese_name})
        sort = MealSort.objects.get(name='xd_sort')

        sorts = sort.sort.split('|')
        js_xd3_sort = sort.sort.replace('|', ',')
        qz_sort = sorts[0].split(',')
        xy_sort = sorts[1].split(',')
        score_sort = sorts[2].split(',')
        customs = Member.objects.filter(analyst_custom=analy, mem_type=1)
        custom_ids = []
        for custom in customs:
            custom_ids.append(custom.id)
        custom_ids.append(analy.id)
        query_custom_id ='ALL'
        if query_custom == 'ALL':
            files = SourceFile.objects.filter(custom_id__in=custom_ids, is_delete=False).order_by('-create_time')
        elif query_custom:
            query_custom = Member.objects.get(pk=query_custom)
            query_custom_id = query_custom.id
            files = SourceFile.objects.filter(custom_id=query_custom, is_delete=False).order_by('-create_time')
        else:
            files = SourceFile.objects.filter(custom_id__in=custom_ids, is_delete=False).order_by('-create_time')
        if query_time1:
            query_time = query_time1[-4:] + '-' + query_time1[:2] + '-' + query_time1[3:5]
            files = files.filter(create_time__gte=query_time)
        if query_time2:
            query_time = query_time2[-4:] + '-' + query_time2[:2] + '-' + query_time2[3:5]
            files = files.filter(create_time__lte=query_time)
        if query_file_name:
            files = files.filter(filename__contains=query_file_name)
        p = Paginator(files, PER_PAGE_NUM)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'analyst/cus_files.html', {'apicode': apicode, 'page': page,'customs': customs\
            , 'permission': permission, 'permission_sort': permission_sort, 'hx3_permission': hx3_permission\
            , 'hx3_sort': hx3_sort, 'js_hx3_sort': js_hx3_sort, 'xd3_permission': xd3_permission,'js_xd3_sort': js_xd3_sort\
            , 'qz_sort': qz_sort, 'xy_sort': xy_sort, 'score_sort': score_sort, 'cus_id': query_custom, 'file_name': query_file_name\
            , 'query_custom_id': query_custom_id, 'time1': query_time1, 'time2': query_time2, 'obj': obj, 'user':user})


class CusMappingedFilesView(View):
    def get(self, request):
        page_num = request.GET.get('page', 1)
        file_id = request.GET.get('fileid')
        analy = request.user.member
        try:
            file_id = int(file_id)
            source_file = SourceFile.objects.get(pk=file_id)
            if source_file.is_delete:
                raise Http404
        except:
            raise Http404
        files = MappingedFile.objects.filter(source_file=file_id, is_crypt=True).order_by('-create_time')
        p = Paginator(files, PER_PAGE_NUM)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'analyst/cus_mappinged_files.html', {'page': page, 'fileid': file_id})


class SourceFileHeadView(View):
    def get(self, request):
        try:
            fileid = int(request.GET.get('fileid'))
            file = SourceFile.objects.get(custom__analyst_custom=request.user.member, pk=fileid, is_delete=False)
        except:
            return HttpResponse(json.dumps('读取文件出错！'), content_type='application/json')
        res, content = readfilelines(settings.MEDIA_ROOT + file.filename.name, 7)
        return HttpResponse(json.dumps(content), content_type='application/json')


class StartMappingView(View):
    def get_client_ip(self, request):
        real_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if real_ip:
            ip = real_ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request):
        fileid = request.GET.get('fileid')
        select = request.GET.get('select')
        if fileid is None or select is None:
            return JsonResponse({'msg': '参数错误!'})

        member = request.user.member
        if member.mem_type != Member.ANALYSTS:
            return JsonResponse({'msg': '你无权限进行mapping！'})
        try:
            srcfile = SourceFile.objects.get(pk=fileid)
        except SourceFile.DoesNotExist:
            errlog.exception("here is start mapping:")
            return JsonResponse({'msg': '文件不存在!'})
        if not srcfile.fields.strip():
            return JsonResponse({'msg': '未标注的文件无法进行匹配'})
        srcfile.can_delete = False
        srcfile.save()
        ip = self.get_client_ip(request)
        username = request.user.username
        try:
            msg = task_queue(srcfile.id, member.id, select, ip, username)
        except Exception:
            msg = 'Task queue error'
            errlog.exception(msg)
        return JsonResponse({'msg': msg})


def task_queue(srcfile_id, member_id, select, ip, username, modal=''):
    try:
        srcfile = SourceFile.objects.get(id=srcfile_id)
    except SourceFile.DoesNotExist:
        errlog.exception('error: SourceFile不存在')
        return 'error: SourceFile不存在'
    try:
        member = Member.objects.get(id=member_id)
    except Member.DoesNotExist:
        errlog.exception('error: Member不存在')
        return 'error: Member不存在'

    try:
        qer = Queryer.objects.get(constom=member)
        interface = Interface.objects.get(name=select)
        if interface.max_map:
            if srcfile.total_lines > interface.max_map:
                return '该接口单次匹配量在%s以内，不能加入队列！' % interface.max_map

        if qer.is_busy:
            tasks.wait.delay(srcfile.id, member.id, select, ip, username, modal)
            return '已加入队列'

        if select in ['sjpl3', 'tyhx3', 'xdhx3', 'TelCheck', 'IdPhoto', 'TelStatus', 'TelPeriod']:
            if select in ['TelCheck', 'IdPhoto', 'TelStatus', 'TelPeriod']:
                modal = select
            result = tasks.for_hx.delay(srcfile, member, select, ip, username, modal)
        else:
            start = mapping.BaseMapping(srcfile, member, select, ip, username, modal)
            status, message = start.check()
            if not status:
                return message
            result = tasks.for_ice.delay(srcfile, member, select, ip, username, modal)
        qer.is_busy = True
        qer.do_on_file = os.path.basename(str(srcfile))
        qer.end_match = timezone.now()
        qer.save()
        member.taskid = result.id
        member.save()
        return '匹配执行中'
    except Exception:
        errlog.error(traceback.format_exc())


class ShutDown(View):
    def get(self, request):
        try:
            qer = request.user.member.queryer
            member = request.user.member
            taskid = member.taskid
            status = qer.is_busy
            revoke(taskid,terminate=True,singal='SIGKILL')
            qer.is_busy = False
            qer.save()
            return JsonResponse({'msg': 1})
        except Exception, e:
            errlog.error(traceback.format_exc())
            return JsonResponse({'msg': 0})
       

class UpReportView(View):
    def get(self, request):
        try:
            fileid = int(request.GET['fileid'])
            source_file = SourceFile.objects.get(pk=fileid)
            if source_file.is_delete:
                raise Http404
            default_mail = ""
            mappinged_files = MappingedFile.objects.filter(customer__analyst_custom=request.user.member,
                    is_crypt=True, source_file=fileid)[:40]
            source_file = SourceFile.objects.get(pk=fileid)
            if source_file.custom.email and re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", source_file.custom.email):
                default_mail = source_file.custom.email
            member = request.user.member
            if member == source_file.custom:
                default_mail = ''
            return render(request, 'analyst/up_report.html', {'mappinged_files': mappinged_files, 'fileid': fileid,'default_mail' : default_mail})
        except Exception:
            errlog.error('up file error' + traceback.format_exc())
            return HttpResponse('get error')
        
    @transaction.atomic
    def post(self, request):
        try:
            fileid = int(request.POST['fileid'])
            mappinged_files_id = request.POST.getlist('mappinged_files')
            mappinged_files_id = [int(x) for x in mappinged_files_id]
            file_desc = request.POST.get('file_desc')
            file = request.FILES.get('file')

            email_state = request.POST.get("change")
            change_email = request.POST.get("change_email")

            err = []
            if not mappinged_files_id or not file:
                err.append('请选择匹配后的文件 和 要提交的文件！')
                mappinged_files = MappingedFile.objects.filter(customer__analyst_custom=request.user.member,
                        is_crypt=True,source_file=fileid)[:40]
                return render(request, 'analyst/up_report.html', {'mappinged_files': mappinged_files,'fileid': fileid,
                    'err': '<br>'.join(err)})
            if ReportFile.objects.filter(report_file='report_file/' + os.path.splitext(file.name)[0] + '.7z').exists():
                err.append('此文件已存在，请换个文件名！')
                mappinged_files = MappingedFile.objects.filter(customer__analyst_custom=request.user.member,
                        is_crypt=True, source_file=fileid)[:40]
                return render(request, 'analyst/up_report.html', {'mappinged_files': mappinged_files,'fileid': fileid,
                    'err': '<br>'.join(err)})
            with open(TMP_PATH + file.name, 'w') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            zipf_name = os.path.splitext(file.name)[0]+'.7z'
            send_name = TMP_PATH + 'Bairong_Test_Result_Report.7z'
            passwd = random.randint(1000,9999)
            os.system(Z_COMMAND % (passwd,TMP_PATH + zipf_name,
                TMP_PATH + file.name))
            os.system(H_COMMAND % (TMP_PATH + zipf_name, send_name))
            member = request.user.member
            report_file = ReportFile()
            report_file.file_desc = file_desc
            report_file.file_size = os.path.getsize(TMP_PATH + zipf_name)
            report_file.passwd = passwd
            report_file.uploader = member
            report_file.report_file.save(zipf_name,
                    File(open(TMP_PATH + zipf_name)))
            report_file.save()

            try_delete_file(TMP_PATH + zipf_name)
            try_delete_file(TMP_PATH + file.name)

            mappinged_files = MappingedFile.objects.filter(customer__analyst_custom = request.user.member,
                    is_crypt=True, pk__in=mappinged_files_id)
            tt = False
            source_file_id = 0
            for mappinged_file in mappinged_files:
                if not tt:
                    report_file.customer = mappinged_file.customer
                    report_file.source_file = mappinged_file.source_file
                    source_file_id = mappinged_file.source_file.id
                    report_file.can_down.add(mappinged_file.customer)
                    report_file.can_down.add(member)
                    report_file.save()
                    tt = True
                report_file.mappinged_files.add(mappinged_file)
                mappinged_file.related_report = report_file
                mappinged_file.save()
            report_file.save()

            if email_state:
                rece = report_file.customer.email
                if change_email: 
                    rece = change_email
                sub = "百融测试结果"
                ms = "您好，贵公司在百融公司的测试结果已完成，附件是分析师上传的分析报告，请查收！稍后百融的数据分析师会把测试结果的解压密码告知您"
                # file_path = settings.MEDIA_ROOT + str(report_file.report_file)
                try:
                    send_attmail(rece,send_name,sub,ms)
                except smtplib.SMTPRecipientsRefused:
                    return render(request, 'analyst/up_report.html', {'error': '客户邮箱错误!'})
                os.remove(send_name)
            return redirect('/als/analyst/cus_report_files/?fileid=' + str(source_file_id))
        except Exception:
            errlog.error('文件上传失败:'+traceback.format_exc())
            return render(request, 'analyst/up_report.html', {'error': '上传失败请联系管理员！'})
        

class CusReportFilesView(View):
    def get(self, request):
        file_id = request.GET.get('fileid')
        file_id = int(file_id)
        source_file = SourceFile.objects.get(pk=file_id)
        if source_file.is_delete:
            return render(request, 'analyst/cus_report_files.html', {'error': "源文件已被删除"})
        analy = request.user.member
        files = ReportFile.objects.filter(customer__analyst_custom=analy, source_file=file_id,
                uploader=analy).order_by('create_time')[:50]
        return render(request, 'analyst/cus_report_files.html', {'report_files': files})


class MappingProgressView(View):
    def get(self, request):
        infos = []
        try:
            res = '功能暂不提供。'
            qer = request.user.member.queryer
            status = qer.is_busy
        except Exception, e:
            errlog.error('mapping progress , get queryer wrong:' + traceback.format_exc())
            return HttpResponse('apicode配置错误，请联系管理员！')
        if qer.is_busy:
            res = '文件： ' + qer.do_on_file +  '   匹配中。'
            infos.append(res)
        else:
            infos.append('无正在匹配的文件')
        mapping_files = qer.mapping_files
        if mapping_files:
            infos.append('文件匹配结果（最近七条）：')
            mapping_files = mapping_files.split(',')
            time =0 
            for mapping_file in mapping_files:
                time = time + 1
                if time >7 :
                    continue
                infos.append(mapping_file)
        return render(request, 'analyst/mapping_progress.html', {'infos': infos, 'status':status})


class DownSourceView(View):
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    def get(self, request):
        file_id = request.GET.get('fileid')
        member = request.user.member
        try:
            file_id = int(file_id)
        except:
            raise Http404
        sf = get_object_or_404(SourceFile, pk=file_id)

        fields = sf.fields
        splitor = sf.splitor
        if not fields or not splitor:
            return HttpResponse('请先标注！')
        else:
            return HttpResponse('禁止下载源文件')
        skip_num = sf.skip_lines
        all_line = []
        openid_prex = 'br1%06d' % sf.id
        line_num = 0
        _, ext = os.path.splitext(sf.filename.name)
        if ext in ['.xls','.xlsx']:
            lines = iter_xls(settings.MEDIA_ROOT + sf.filename.name)
        else:
            lines = iter_txt(settings.MEDIA_ROOT + sf.filename.name)
        for line in lines:
            line_num += 1
            line = line.strip()
            if skip_num:
                skip_num -= 1
                all_line.append("openid" + ',' + line)
                continue
            all_line.append(openid_prex + ('%07d' % line_num) + ',' + crypt_line(line, fields, splitor))
        data = StringIO.StringIO()
        data.write('\n'.join(all_line))
        data.seek(0)
        response = HttpResponse(FileWrapper(data), content_type='application/zip')
        file_name = os.path.basename(str(sf))
        file_name, _ = os.path.splitext(file_name)
        ip = self.get_client_ip(request)
        behaviorlog.error(time.strftime('%Y%m%d%H%M%S') +'IP :'+ ip + '分析师：'  + member.name + '下载了文件：' + str(file_name))
        response['Content-Disposition'] = 'attachemt; filename=' + file_name + ".txt; filename*=utf-8''"+file_name+".txt"
        return response


class MyCus(View):
    def get(self, request):
        customs = Member.objects.filter(analyst_custom=request.user.member).order_by('-create_time')
        return render(request, 'analyst/my_cus.html', {'customs': customs})


class SendCusMappingFileView(View):
    def get(self,request):
        CP_COMMAND = "cp %s  %s"
        fileid = request.GET.get("fileid")
        try :
            map_file = MappingedFile.objects.get(pk = fileid)
            customer = map_file.customer
            recever = customer.email
            map_file_path = str(map_file.file).replace('_crypt','')
            _ , ext = os.path.splitext(map_file_path)
            if ext == ".txt":
                return HttpResponse(json.dumps('禁止发送txt文件，请发送scv文件！'), content_type='application/json')
            if map_file.is_haina:
                return HttpResponse(json.dumps('禁止发送非通用接口和信贷接口匹配的文件！'), content_type='application/json')
            member = request.user.member
            if member == customer:
                return HttpResponse(json.dumps('禁止发送抽样文件！'), content_type='application/json')
            file_path = settings.MEDIA_ROOT + map_file_path

            os.system(CP_COMMAND %(file_path,TMP_PATH))
            file_path = TMP_PATH + os.path.basename(file_path)
            zipf_name = 'Bairong_Test_Result.7z'
            passwd = random.randint(1000,9999)
            map_file.password = passwd
            map_file.save()
            os.system(Z_COMMAND % (passwd,zipf_name, file_path))
            subject = '百融测试-匹配结果'
            msg = "您好，贵公司在百融的测试匹配已完成，请查收。稍后百融的分析师会把测试匹配结果的解压密码告诉您。"
            send_attmail(recever, zipf_name, subject, msg)
            os.remove(file_path)
            os.remove(zipf_name)
        except Exception, e:
            errlog.error("send custom mappinged file :" + traceback.format_exc())

        return HttpResponse(json.dumps('发送成功！'), content_type='application/json')


class SendMailToCoder(View):
    def get(self,request):
        try:
            recever = 'yu.zhao@100credit.com'
            member = request.user.member
            name = member.name
            mail = member.email
            fileid = request.GET.get("fileid")
            data = request.GET.get('data')
            mark = request.GET.get('mark')
            collect = request.GET.get('collect')
            modal =[] 
            if data == 'true':
                interface = '信息补充套餐'
                modal.append('data')
            if mark == 'true':
                interface = '营销失联套餐'
                modal.append('mark')
            if collect == 'true':
                interface = '催收失联套餐'
                modal.append('collect')
            if len(modal) != 1:
                return HttpResponse(json.dumps('请选择一个模块！'), content_type='application/json')
            source_file = SourceFile.objects.get(pk = fileid)
            filename = source_file
            file_from = source_file.file_from
            total_lines = source_file.total_lines
            create_time = source_file.create_time
            subject = "申请授权码"
            content = '<style class="fox_global_style"> div.fox_html_content { line-height: 1.5;} /* 一些默认样式 */ blockquote { margin-Top: 0px; margin-Bottom: 0px; margin-Left: 0.5em } ol, ul { margin-Top: 0px; margin-Bottom: 0px; list-style-position: inside; } p { margin-Top: 0px; margin-Bottom: 0px } </style><p style="margin-right: 0cm; margin-left: 0cm; line-height: 15.75pt; font-family: 微软雅黑; text-align: justify; font-size: 15px;"><font face="微软雅黑"><b>申请人 :'+str(name)+'</b></font></p> <p style="margin-right: 0cm; margin-left: 0cm; line-height: 15.75pt; font-family: 微软雅黑; text-align: justify; font-size: 15px;"><font face="微软雅黑"><b>申请套餐 :'+str(interface)+'</b></font></p><p style="margin-right: 0cm; margin-left: 0cm; line-height: 15.75pt; font-family: 微软雅黑; text-align: justify; font-size: 15px;"><font face="微软雅黑"><b>文件名 :'+str(filename)+'</b></font></p> <p style="margin-right: 0cm; margin-left: 0cm; line-height: 15.75pt; font-family: 微软雅黑; text-align: justify; font-size: 15px;"><font face="微软雅黑"><b>文件来源 :'+str(file_from)+'</b></font></p><p style="margin-right: 0cm; margin-left: 0cm; line-height: 15.75pt; font-family: 微软雅黑; text-align: justify; font-size: 15px;"><font face="微软雅黑"><b>文件行数 :'+str(total_lines)+'</b></font></p> <p style="margin-right: 0cm; margin-left: 0cm; line-height: 15.75pt; font-family: 微软雅黑; text-align: justify; font-size: 15px;"><font face="微软雅黑"><b>文件创建时间 :'+str(create_time)+'</b></font></p> <p style="margin-right: 0cm; margin-left: 0cm; line-height: 15.75pt; font-family: 微软雅黑; text-align: justify; font-size: 15px;"><font face="微软雅黑">邮箱：<a href="mailto:yu.zhao@100credit.com" >'+str(mail)+'</a></font></p>'
            mail_to_coder(recever, subject, content)
        except Exception, e:
            errlog.error("send mail to coder error :" + traceback.format_exc())   
            return HttpResponse(json.dumps('发送失败！'), content_type='application/json')
        return HttpResponse(json.dumps('发送成功！'), content_type='application/json')


class GetMapFilePasswd(View):
    def get(self, request):
        fileid = request.GET.get("fileid")
        password = MappingedFile.objects.get(pk=fileid)
        if password.password :
            msg = "密码为：" + str(password.password)
        else :
            msg="请先点击发送邮件"
        return HttpResponse(json.dumps(msg),content_type='application/json')


class LetCustomGetView(View):
    def get(self, request):
        try:
            fileid = request.GET.get("fileid")
            source_files = MappingedFile.objects.get(pk=fileid)
            file_name = str(source_files.file).replace('_crypt', '')
            dest_file = MappingedFile.objects.get(file=file_name)
            if dest_file.is_haina:
                return HttpResponse(json.dumps("非通用版匹配接口和信贷接口匹配的文件禁止客户查看"), content_type="application/json")
            dest_file.is_cus_visible = True
            dest_file.save()
        except Exception:
            errlog.error("let custom get mappinged file :" + traceback.format_exc())
            return HttpResponse(json.dumps("操作失败"), content_type='application/json')
        return HttpResponse(json.dumps("已允许客户查看"), content_type="application/json")


class SelectModelView(View):
    def get_client_ip(self, request):
        real_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if real_ip:
            ip = real_ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request):
        try:
            fileid = request.GET.get('fileid')
            select = request.GET.get('select')
            member = request.user.member
            modal = []
            if select == 'tyhx3' or select == 'xdhx3':
                meals = request.GET.get('meals', '')
                if meals.startswith(','):
                    meals = meals[1:]
                if meals:
                    meals = meals.split(',')
                    for meal in meals:
                        modal.append(meal)
            else:
                for x in ['apply', 'special', 'behavior', 'account', 'paycon', 'monthaccount', 'telecheck']:
                    if request.GET.get(x) == "true":
                        x += str(select)
                        modal.append(x)
            if not modal:
                return HttpResponse(json.dumps({'msg':'请选择模块后再匹配'}), content_type="application/json")

            if member.mem_type != Member.ANALYSTS:
                return HttpResponse(json.dumps({'msg': '你无权限进行mapping！'}), content_type="application/json")
            try:
                file = SourceFile.objects.get(pk=fileid)
            except:
                return HttpResponse(json.dumps({'msg': '该文件不存在!'}), content_type="application/json")
            if not file.fields.strip():
                return HttpResponse(json.dumps({'msg': '未标注的文件无法进行匹配'}), content_type="application/json")
            try:
                file.can_delete = False
                file.save()
                ip = self.get_client_ip(request)
                username = request.user.username
                msg = task_queue(file.id, member.id, select, ip, username, modal)
                return HttpResponse(json.dumps({'msg': msg}), content_type="application/json") 
            except:
                errlog.error(traceback.format_exc())

        except:
            print traceback.format_exc()
            


class BcjqModelView(View):
    def get_client_ip(self, request):
        real_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if real_ip:
            ip = real_ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request):
        fileid = request.GET.get('fileid')
        select = request.GET.get('select')
        modal = []
        for x in ['bcjq_card_name', 'bcjq_card_cell', 'bcjq_card_name_id', 'bcjq_name_id_cell']:
            if request.GET.get(x) == 'true':
                modal.append(x)
        if not modal:
            return HttpResponse(json.dumps({'msg':'请选择一个接口后再匹配'}), content_type="application/json")
        if len(modal) > 1:
            return HttpResponse(json.dumps({'msg':'请不要选择多个模块'}), content_type="application/json")
        member = request.user.member
        if member.mem_type != Member.ANALYSTS:
            return HttpResponse(json.dumps({'msg': '你无权限进行mapping！'}), content_type="application/json")
        try:
            file = SourceFile.objects.get(pk=fileid)
        except:
            return HttpResponse(json.dumps({'msg': '该文件不存在!'}), content_type="application/json")
        if not file.fields.strip():
            return HttpResponse(json.dumps({'msg': '未标注的文件无法进行匹配'}), content_type="application/json")
        if int(file.total_lines) > 20000:
            return HttpResponse(json.dumps({'msg': '超出该接口最大匹配条数，数据源接口限制单次查询请少于两万条'}), content_type='application/json')
        try:
            file.can_delete = False
            file.save()
            ip = self.get_client_ip(request)
            username = request.user.username
            msg = task_queue(file.id, member.id, select, ip, username, modal)
        except:
            errlog.error(traceback.format_exc())
        return HttpResponse(json.dumps({'msg': msg}), content_type="application/json")


class LossModelView(View):
    def get_client_ip(self, request):
        real_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if real_ip:
            ip = real_ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request):
        fileid = request.GET.get('fileid')
        select = request.GET.get('select')
        code = request.GET.get('loss_code')
        try:
            coder = Coder.objects.get(code=str(code))
        except Exception, e:
            return HttpResponse(json.dumps({'msg':'无效的授权码'}), content_type="application/json")
        if coder.is_outdate == True:
            return HttpResponse(json.dumps({'msg':'授权码已过期'}), content_type="application/json")
        modal = []
        modal.append(str(code))
        for x in ['loss_data', 'loss_mark', 'loss_collect']:
            if request.GET.get(x) == 'true':
                modal.append(x)
        if len(modal) != 2:
            return HttpResponse(json.dumps({'msg':'请选择一个模块!'}), content_type="application/json")
        if modal[1] != str(coder.permission):
            return HttpResponse(json.dumps({'msg':'你没有该套餐的权限'}), content_type="application/json")
        member = request.user.member
        if member.mem_type != Member.ANALYSTS:
            return HttpResponse(json.dumps({'msg': '你无权限进行mapping！'}), content_type="application/json")
        try:
            file = SourceFile.objects.get(pk=fileid)
        except:
            return HttpResponse(json.dumps({'msg': '该文件不存在!'}), content_type="application/json")
        if not file.fields.strip():
            return HttpResponse(json.dumps({'msg': '未标注的文件无法进行匹配'}), content_type="application/json")
        if int(file.total_lines) > 20000:
            return HttpResponse(json.dumps({'msg': '超出该接口最大匹配条数，数据源接口限制单次查询请少于两万条'}), content_type='application/json')
        try:
            file.can_delete = False
            file.save()
            ip = self.get_client_ip(request)
            username = request.user.username
            msg = task_queue(file.id, member.id, select, ip, username, modal)
        except:
            errlog.error(traceback.format_exc())
        return HttpResponse(json.dumps({'msg': msg}), content_type="application/json")


class CompanyModelView(View):

    def get(self, request):
        fileid = request.GET.get('fileid')
        select = request.GET.get('select')
        modal = []
        for x in ['name_company', 'card_company']:
            if request.GET.get(x) == 'true':
                modal.append(x)
        if not modal:
            return HttpResponse(json.dumps({'msg':'请选择一个接口后再匹配'}), content_type="application/json")
        if len(modal) > 1:
            return HttpResponse(json.dumps({'msg':'请不要选择多个模块'}), content_type="application/json")
        member = request.user.member
        if member.mem_type != Member.ANALYSTS:
            return HttpResponse(json.dumps({'msg': '你无权限进行mapping！'}), content_type="application/json")
        try:
            file = SourceFile.objects.get(pk=fileid)
        except:
            return HttpResponse(json.dumps({'msg': '该文件不存在!'}), content_type="application/json")
        if not file.fields.strip():
            return HttpResponse(json.dumps({'msg': '未标注的文件无法进行匹配'}), content_type="application/json")
        try:
            file.can_delete = False
            file.save()
            ip = self.get_client_ip(request)
            username = request.user.username
            msg = task_queue(file.id, member.id, select, ip, username, modal)
        except:
            errlog.error(traceback.format_exc())
        return HttpResponse(json.dumps({'msg': msg}), content_type="application/json")


class OperatorModelView(View):
    def get_client_ip(self, request):
        real_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if real_ip:
            ip = real_ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request):
        fileid = request.GET.get('fileid')
        select = request.GET.get('select')
        modal = []
        for x in ['lt_cell_state', 'lt_card_name', 'dx_cell_state', 'dx_card_name']:
            if request.GET.get(x) == 'true':
                modal.append(x)
        if not modal:
            return HttpResponse(json.dumps({'msg':'请选择一个接口后再匹配'}), content_type="application/json")
        if len(modal) > 1:
            return HttpResponse(json.dumps({'msg':'请选择一个接口后再匹配，不要多选'}), content_type="application/json")
        if 'lt_cell_state' in modal or 'lt_cell_state' in modal:
            return HttpResponse(json.dumps({'msg':'联通接口未上线'}), content_type="application/json")

        member = request.user.member
        if member.mem_type != Member.ANALYSTS:
            return HttpResponse(json.dumps({'msg': '你无权限进行mapping！'}), content_type="application/json")
        try:
            file = SourceFile.objects.get(pk=fileid)
        except:
            return HttpResponse(json.dumps({'msg': '该文件不存在!'}), content_type="application/json")
        if not file.fields.strip():
            return HttpResponse(json.dumps({'msg': '未标注的文件无法进行匹配'}), content_type="application/json")
        try:
            file.can_delete = False
            file.save()
            ip = self.get_client_ip(request)
            username = request.user.username
            msg = task_queue(file.id, member.id, select, ip, username, modal)
        except:
            errlog.error(traceback.format_exc())
        return HttpResponse(json.dumps({'msg': msg}), content_type="application/json")


class CollectDateView(View):

    def get(self, request):
        try:
            fileid = request.GET.get('fileid', '')
            file = SourceFile.objects.get(pk=fileid)
            analy_member = request.user.member
            file_path = os.path.join(settings.MEDIA_ROOT, file.filename.name)
            _, ext = os.path.splitext(file_path)
            line_num = 0
            file_head = file.fields
            file_head = file_head.split(',')
            if ext == '.txt' or ext == '.csv':
                lines = iter_txt(file_path)
            elif ext == '.xls' or ext == '.xlsx':
                lines = iter_xls(file_path)
            rows = []
            for line in lines:
                if line_num == 0:
                    pass
                else:
                    queue = []
                    line = line.strip().split(',')
                    for x in line:
                        queue.append(x)
                    queue = dict(zip(file_head, queue))
                    comein_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    queue.update({'source_file': file})
                    queue.update({'user_type': file.user_type})
                    queue.update({'guarantee_type': file.guarantee_type})
                    queue.update({'file_source_type': file.file_source_type})
                    queue.update({'analyst': file.custom.analyst_custom.name})
                    queue.update({'up_time': file.create_time})
                    if 'apply_date' not in queue.keys():
                        queue.update({'apply_date': str(file.create_time.date())})
                    if 'cus_num' in queue.keys():
                        queue.pop('cus_num')
                    if 'id' in queue.keys():
                        queue.update({'id_num':queue['id']})
                        queue.pop('id')
                    rows.append(queue)
                line_num += 1
        except Exception, e:
            errlog.error('加入数据集市失败1:' + traceback.format_exc())
            return JsonResponse({'msg': '加入数据集市失败'})
        
        for row in rows:
            try:
                collect_date = ColletDate(**row)
                collect_date.save()
            except Exception, e:
                errlog.error('加入数据集市失败2:' + traceback.format_exc())
                return JsonResponse({'msg':'加入数据集市失败'})
        file.is_sampling = True
        file.save()
        msg = '已成功加入数据集市'
        behaviorlog.error( time.strftime('%Y%m%d-%H%M%S') + str(analy_member.name) + '将文件' + str(file) + '添加至数据集市。')
        return JsonResponse({'msg': msg})


class SamplingView(View):
    def get(self, request):
        if request.user.member.mem_type != Member.CHECKER:
            raise Http404
        return render(request, 'analyst/sampling.html', {'file_source_type': SourceFile.FILE_SOURCE_TYPES,
                'guarantee_type': SourceFile.GUARANTEE_TYPE,
                'user_type': SourceFile.USER_TYPE})


def loginfo(request):
    start_date = request.GET.get('apply_date1')
    end_date = request.GET.get('apply_date2')
    if start_date and end_date:
        d1 = datetime.datetime.strptime(start_date, "%m/%d/%Y")
        d2 = datetime.datetime.strptime(end_date, "%m/%d/%Y")
        infos = LogInfo.objects.filter(create_time__gte=d1, create_time__lte=d2)
    else:
        infos = LogInfo.objects.all()
    page_num = request.GET.get('page_num')
    p = Paginator(infos, 12)
    try:
        page = p.page(int(page_num))
    except:
        page = p.page(1)
    return render(request, 'analyst/loginfo.html', {'page': page})


@csrf_exempt
def sampling_condition(request):

    if request.user.member.mem_type != Member.CHECKER:
            raise Http404
    if request.method == 'POST':
        keys = []
        values = []
        for key in request.POST:
            if key != 'csrfmiddlewaretoken':
                keys.append(key)
                value = request.POST.get(key)
            if value and value != '请选择':
                values.append(value)
                continue
        if not values:
            return render(request, 'analyst/sampling.html', {'err': '请选择筛选条件！', 'file_source_type': SourceFile.FILE_SOURCE_TYPES,
                'guarantee_type': SourceFile.GUARANTEE_TYPE,
                'user_type': SourceFile.USER_TYPE})
        file_source_type = request.POST.get("company_cate")
        guarantee_type = request.POST.get('collateral')
        user_type = request.POST.get("user_type")
        apply_date1 = request.POST.get("apply_date1", '')
        apply_date2 = request.POST.get("apply_date2", '')
        raw_sql = 'select source_file_id, analyst, file_source_type, guarantee_type, user_type, count(source_file_id), up_time  from analyse_colletdate where '
        if apply_date1 and apply_date2:
            apply_date1 = apply_date1[-4:] + '-' + apply_date1[:2] + '-' + apply_date1[3:5]
            apply_date2 = apply_date2[-4:] + '-' + apply_date2[:2] + '-' + apply_date2[3:5]
            raw_sql = raw_sql + " apply_date between '" + str(apply_date1) + "' and '" + str(apply_date2) + "' "     
        else:
            year = datetime.datetime.now().year
            month = datetime.datetime.now().month
            day = datetime.datetime.now().day
            if month < 10:
                now = str(year) + '-0' + str(month) + '-' + str(day)
            else:
                now = str(year) + '-' + str(month) + '-' + str(day)
            raw_sql = raw_sql + " apply_date = '" + now + "' "
        if file_source_type and file_source_type != u'请选择':
            raw_sql = raw_sql + " and file_source_type = '" + str(file_source_type) + "' "
        if guarantee_type and guarantee_type != u'请选择':
            raw_sql = raw_sql + " and  guarantee_type = '" + str(guarantee_type) + "' " 
        if user_type and user_type != u'请选择':
            raw_sql = raw_sql + " and user_type = '" + str(user_type) + "' " 
        raw_sql = raw_sql + " group by source_file_id;"
        print raw_sql,3333333
        try:
            raw_querySet = sql_connect(raw_sql)
        except Exception, e:
            errlog.error('sampling sql error, sql is ' + raw_sql + traceback.format_exc())
            return render(request, 'analyst/sampling.html', {'err': '查询出错！', 'file_source_type': SourceFile.FILE_SOURCE_TYPES,
                'guarantee_type': SourceFile.GUARANTEE_TYPE,
                'user_type': SourceFile.USER_TYPE})
        dict_orders = []
        if raw_querySet:
            for raw in raw_querySet:
                dict_datas = {}
                id_num = raw[0]
                source_file = SourceFile.objects.get(pk=raw[0])
                dict_datas.update({'file_id': id_num, 'file':source_file,'user_type': raw[4], 'analyst': raw[1], 'file_source_type': raw[2], 'guarantee_type': raw[3], 'lines': source_file.total_lines, 'up_time': raw[6]})
                dict_orders.append(dict_datas)
            return render(request, 'analyst/sampling.html', {'datas': dict_orders, 'file_source_type': SourceFile.FILE_SOURCE_TYPES,
                'guarantee_type': SourceFile.GUARANTEE_TYPE,
                'user_type': SourceFile.USER_TYPE})
        
        return render(request, 'analyst/sampling.html', {"err":'查询结果为空', 'file_source_type': SourceFile.FILE_SOURCE_TYPES,
                'guarantee_type': SourceFile.GUARANTEE_TYPE,
                'user_type': SourceFile.USER_TYPE})
    return render(request, 'analyst/sampling.html', {'file_source_type': SourceFile.FILE_SOURCE_TYPES,
                'guarantee_type': SourceFile.GUARANTEE_TYPE,
                'user_type': SourceFile.USER_TYPE})

@csrf_exempt
def make_file(request):
    if request.method == 'POST':
        lines = request.POST.getlist('lines')
        file_id = request.POST.getlist('file_id')
        nums = request.POST.getlist('nums')
        data = ''
        total_num = 0
        for line in lines:
            data = data + line
            if not line:
                try:
                    total_num = total_num + int(line)
                except ValueError:
                    return render(request, 'analyst/sampling.html', {'err': '只能输入整数,且数值要小于行数!'}) 
                except:
                    errlog.error('make_file err:'+ traceback.format_exc())
        if not data:
            return render(request, 'analyst/sampling.html', {'err': '请输入抽取行数!'})
        if total_num > 100000:
            return render(request, 'sampling.html', {'err': '抽样总数请少于10万'})
        datas = zip(file_id, lines, nums)
        result = []
        for key in datas:
            if not key[2]:
                continue 
            if int(key[2]) > int(key[1]):
                return render(request, 'analyst/sampling.html', {'err': '抽取行数请小于总行数'})
            sql = "select * from analyse_colletdate where source_file_id = " + str(key[0]) + " order by rand() limit " + str(key[2]);
            res = sql_connect(sql)  
            for val in res:
                a = list(val)
                a.pop(0)
                a.pop(0)
                a.pop(0)
                a.pop(0)
                a.pop(2)
                a.pop()
                a.pop()
                result.append(tuple(a))
        header = [u'分析师', u'上传到DTS时间','id_num', 'cell', 'email', 'name', 'home_addr', 'home_tel'
        	, 'biz_addr', 'biz_tel', 'other_addr', 'bank_card1', 'bank_card2', 'flag1', 'flag2', 'flag'
        	, 'def_days', 'def_times', 'amount', 'notes', 'apply_date', 'observe_date', 'apply_channel'
        	, 'apply_id', 'apply_addr', 'apply_amount', 'apply_product', 'approval_status', 'approval_date'
        	, 'approval_amount', 'device_type', 'device_id', 'apply_type', 'type_vehicle_id', 'af_swift_number'
        	, 'custApiCode', 'envent', 'collateral', 'loan_date', 'loan_purpose', 'loan_status', 'repayment_periods'
        	, 'age', 'race', 'gender', 'birthday', 'marriage', 'edu', 'wechat_city', 'wechat_name', 'wechat_province'
        	, 'providentfund', 'socialsecurity', 'id_ps', 'id_start', 'id_end', 'id_city', 'id_type', 'civic_addr'
        	, 'civic_status', 'postalcode', 'city', 'province', 'contact_name_1', 'contact_relation_1', 'contact_cell_1'
        	, 'contact_name_2', 'contact_relation_2', 'contact_cell_2', 'contact_name_3', 'contact_relation_3'
        	, 'contact_cell_3', 'contact_name_4', 'contact_relation_4', 'contact_cell_4', 'contact_name_5'
        	, 'contact_relation_5', 'contact_cell_5', 'if_house', 'if_vehicle', 'housing_cate', 'vehicle_id'
        	, 'vehicle_type', 'biz_name', 'biz_size', 'industry', 'company_cate', 'salary', 'position'
        	, 'working_period', 'acc_open_date', 'card_level', 'branch', 'currency', 'ins_balance', 'update_balance'
        	, 'update_capital', 'update_date', 'update_interest', 'update_overduepayment', 'update_overlimitfee'
        	, 'update_servicefee', 'bill_day', 'bill_post', 'bill_addr', 'ins_amount', 'ins_date_claims'
        	, 'ins_firstlogindate', 'ins_newvehicleprice', 'ins_period', 'ins_yearly_claims_num', 'imei'
        	, 'mobil_type', 'gid', 'other_var1', 'var_exp1', 'other_var2', 'var_exp2', 'other_var3'
        	, 'var_exp3', 'other_var4', 'var_exp4', 'other_var5', 'var_exp5' ]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sample_'+ str(datetime.datetime.now().date()) +'.csv"'
        response.write(codecs.BOM_UTF8)
        writer = csv.writer(response)
        writer.writerow(header)
        writer.writerows(result)
        return response


def delete_report(request):
    fileid = request.POST.get('fileid')
    member =request.user.member
    file = ReportFile.objects.get(pk=int(fileid))
    source_file_id = file.source_file.id
    behaviorlog.error('analy名为：' + str(member.name) + '删除了报告：' + str(file.report_file))
    file.delete()
    return HttpResponse(json.dumps({'fileid': source_file_id}), content_type="application/json")


class GetCustomNumView(View):
    def get(self, request):
        try:
            company_cate = request.GET.get('company_cate', '')
            custom_num = []
            files = SourceFile.objects.filter(file_source_type=company_cate, is_sampling=False)
            for file in files:
                cus_num = Member.objects.get(pk=file.custom.id)
                custom_num.append(cus_num.custom_num)
            custom_num = list(set(custom_num))
            custom_sort = []
            for custom_num_date in range(100):
                num_zero = 7 - len(str(custom_num_date))
                sort = 'CUSTEST' + num_zero*'0' + str(custom_num_date)
                custom_sort.append(sort)
            return HttpResponse(json.dumps({'custom_num': custom_num, 'custom_sort': custom_sort}), content_type="application/json")
        except Exception, e:
            errlog.error(traceback.format_exc())


class GetFileNumView(View):
    def get(self, request):
        try:
            custom_num = request.GET.get('custom_num', '')
            file_num = []
            try:
                member = Member.objects.get(custom_num=custom_num)
            except Exception, e:
                return HttpResponse(json.dumps({'file_num': file_num}), content_type="application/json")    
            files = SourceFile.objects.filter(custom=member, is_sampling=True)
            for file in files:
                file_num.append(file.sampling_sort)
            return HttpResponse(json.dumps({'file_num': file_num}), content_type="application/json")
        except Exception, e:
            errlog.error(traceback.format_exc())


SAMPLINGSORT = [
    'file_num', 'custom_num', 'cus_num', 'id', 'cell', 'email', 'qq_num', 'name', 'home_addr', 'home_tel',
    'biz_addr', 'biz_tel', 'other_addr', 'bank_card1', 'bank_card2', 'flag1', 'flag2', 'flag', 'def_days',
    'def_times', 'amount', 'notes', 'apply_date', 'observe_date', 'apply_channel', 'apply_id', 'apply_addr',
    'apply_amount', 'apply_product', 'approval_status', 'approval_date', 'approval_amount', 'collateral', 'loan_date',
    'loan_purpose', 'loan_status', 'repayment_periods', 'age', 'race', 'gender', 'birthday',
    'marriage', 'edu', 'wechat_city', 'wechat_name', 'wechat_province', 'providentfund', 'socialsecurity', 'id_ps',
    'id_start', 'id_end', 'id_city', 'id_type', 'civic_addr', 'civic_status', 'postalcode',
    'city', 'province', 'contact_name_1', 'contact_relation_1', 'contact_cell_1', 'contact_name_2', 'contact_relation_2',
    'contact_cell_2', 'contact_name_3', 'contact_relation_3', 'contact_cell_3', 'contact_name_4', 'contact_relation_4',
    'contact_cell_4', 'contact_name_5', 'contact_relation_5', 'contact_cell_5', 'if_house', 'if_vehicle',
    'housing_cate', 'vehicle_id', 'vehicle_type', 'biz_name', 'biz_size', 'industry', 'company_cate',
    'salary', 'position', 'working_period', 'acc_open_date', 'card_level', 'branch', 'currency',
    'ins_balance', 'update_balance', 'update_capital', 'update_date', 'update_interest', 'update_overduepayment',
    'update_overlimitfee', 'update_servicefee', 'bill_day', 'bill_post', 'bill_addr', 'ins_amount',
    'ins_date_claims', 'ins_firstlogindate', 'ins_newvehicleprice', 'ins_period', 'ins_yearly_claims_num',
    'imei', 'imsi', 'event', 'af_swift_number', 'mobil_type', 'gid',
    'other_var1', 'var_exp1', 'other_var2', 'var_exp2', 'other_var3', 'var_exp3',
    'other_var4', 'var_exp4', 'other_var5', 'var_exp5'
]
