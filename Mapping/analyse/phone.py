#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.views.generic import View
from django.http import Http404, HttpResponse
from django.conf import settings
from django.core.servers.basehttp import FileWrapper

import os
import csv
import time
import subprocess
import xlrd
import traceback
import logging
import MySQLdb
import json
import csv
import cStringIO as StringIO
from account.models import Member
from analyse.models import PhoneFile
from analyse.views import UP_FILE_MAX_LINES
from util import readtxtfile
from ddm import upload_phone_number
from ddm import download_result


SOURCE_TYPE = {'BANK_CREDIT_CARD': '银行信用卡', 'BANK_RETAIL': '银行零售', 'BANK_TO_PUBLIC': '银行对公', 'P2P_LOAN': 'P2P借贷', 'P2P_FINANCING': 'P2P理财', 'CONSUMER_FINANCE_COMPANY': '消费金融公司', 'SMALL_LOAN_AGENCY': '小贷机构', 'CAR_FINANCE': '汽车金融', 'GUARANTEE': '担保', 'INSURANCE': '保险', 'FILE_SOURCE_TYPES_OTHER': '其他'}
behaviorlog = logging.getLogger('behavior')
errlog = logging.getLogger('daserr')



class UpFileView(View):
    def get(self, request):
        if request.user.member.mem_type != Member.PHONE:
            raise Http404
        return render(request, 'phone/up_file.html')

    def post(self, request):
        if request.user.member.mem_type != Member.PHONE:
            raise Http404
        file = request.FILES.get('file', '')
        extra_info = request.POST.get('extra_info', '')

        err = []
        if not file:
            err.append('请选择一个文件')
        else:
            _, file_ext = os.path.splitext(file.name)
            if file_ext[1:] not in  ['txt', 'csv','xlsx','xls']:
                err.append('只允许上传txt, csv,xlsx ,xls格式的文件')
            total_lines = int(subprocess.check_output('cat %s | wc -l' % file.temporary_file_path(), shell=True))
            if file_ext[1:] in ['xlsx','xls']:
                excel = xlrd.open_workbook(file.temporary_file_path())
                sheet = excel.sheet_by_index(0)
                total_lines = sheet.nrows
            if total_lines > UP_FILE_MAX_LINES:
                err.append('文件行数不得超过20万')
        if err:
            return render(request, 'phone/up_file.html',
                    {'err': '\n'.join(err)})
        member = request.user.member
        pf = PhoneFile(member=member, extra_info=extra_info,
                file_size=file.size, file_from=member.name)
        pf.total_lines = total_lines
        basename, ext = os.path.splitext(file.name)
        filename = '_'.join([member.name, basename, time.strftime('%Y%m%d-%H%M')]) + ext
        pf.filename.save(filename, file)
        pf.save()
        behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + 'checker名为：' + member.name + ' 上传了' + filename + '文件')
        return redirect('/als/phone/file_list/')


class FileListView(View):
    def get(self, request):
        if request.user.member.mem_type != Member.PHONE:
            raise Http404
        page_num = request.GET.get('page', 1)
        phone = request.user.member
        phone_files = PhoneFile.objects.filter(member = phone).order_by('-create_time')
        p = Paginator(phone_files, 15)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'phone/file_list.html', {'page': page})


class NumInSqlView(View):
    def get(self, request):
        file_id = request.GET.get('fileid', '')
        if not file_id:
            return HttpResponse(json.dumps("缺少文件id"), content_type="application/json")
        file = PhoneFile.objects.get(pk=file_id)
        try:
            with open(settings.MEDIA_ROOT + file.filename.name,'r') as f:
                lines = f.readlines()
                for idx, line in enumerate(lines):
                    check = line.strip()
                    if check == '':
                        return HttpResponse(json.dumps("文件错误"), content_type="application/json")
        except Exception, e:
            print traceback.format_exc()

        if file.task_id:
            return HttpResponse(json.dumps("已添加过，请不要重复操作"), content_type="application/json")
        try:
            lines = readtxtfile(settings.MEDIA_ROOT + file.filename.name)
        except :
            print traceback.format_exc()
        line_head = {}
        phones = []
        phones_ = []
        line_num = 0
        cell_index = 0
        for line in lines:
            print 'line',line
            line_num = line_num + 1
            line = line.split(',')
            if line_num == 1:
                for x in range(len(line)):
                    if line[x] == 'phone':
                        cell_index = x
                    line_head.update({x: line[x]})
                continue
            phones_.append(line[cell_index])
        phones_ = list(set(phones_))
        for phone in phones_:
            phone = phone.replace('\r\n', '').replace('\r', '')
            phones.append(phone)
        results = []
        try:
            up_results = upload_phone_number('1',phones)
        except Exception, e:
            errlog.error("Ice Server error :" + traceback.format_exc())
        if isinstance(up_results, dict) :
            message = up_results['message']
            task_id = up_results['data']['taskId']

            file.task_id = task_id
            total_lines =  len(phones)
            file.total_lines = total_lines
            file.save()
            return HttpResponse(json.dumps("上传成功"), content_type="application/json")
        else:
            return HttpResponse(json.dumps('ICE服务器异常'), content_type="application/json")


class GetResultView(View):
    def get(self, request):
        try:
            csv_write = ['phone,status']
            file_id = request.GET.get('fileid', '')
            if not file_id:
                return HttpResponse('缺少文件id')
            file = PhoneFile.objects.get(pk=file_id)
            task_id = file.task_id
            try:
                results = download_result(task_id, mode = '1')
            except Exception, e:
                errlog.error("Phone_SERVER_ERROR :" + traceback.format_exc())
            if  not isinstance(results, dict):
                csv_write.append(json.dumps({"msg":"time out"}))

            res_code = results["code"]
            if res_code == 3:
                return  HttpResponse('号码正在识别，请等待')
            if res_code in [2,4,5,6,7,8,9]:
                return HttpResponse(results['message'])
            if res_code == 1:
                if results['data']['phoneList']:
                    for every in results['data']['phoneList']:
                        phone = every["phone"]+','+str(every["status"])
                        csv_write.append(phone)
            # csv_write = ['phone,status','13213243214,1','1234435,2']
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            file.applied_done_time = now
            file.save()
            file_name = os.path.basename(str(file))
            file_name, _ = os.path.splitext(file_name)
            filename=' + file_name + ".csv; filename*=utf-8''"+file_name+".csv" '
            response = HttpResponse(content_type = 'text/csv')
            response['Content-Disposition'] = 'attachment; filename='+file_name+".csv"';filename*=utf-8'''+file_name+".csv"' '
            writer = csv.writer(response)
            for data in csv_write:
                writer.writerow(data.split(',')) 
            return response
        except UnboundLocalError:
            return HttpResponse("请先添加到队列再下载")

        
    
