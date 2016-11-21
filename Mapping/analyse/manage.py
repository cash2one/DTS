#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import View
from django.http import HttpResponse, Http404, JsonResponse
from django.db import transaction
from django.conf import settings


import os
import time
import subprocess
import json
import xlrd
import logging
import traceback

from account.models import Member
from analyse.models import SourceFile, MappingedFile, ReportFile
from analyse.views import UP_FILE_MAX_LINES
from analyse.analy import PER_PAGE_NUM
import util
import mapping

SOURCE_TYPE = {'BANK_CREDIT_CARD': '银行信用卡', 'BANK_RETAIL': '银行零售', 'BANK_TO_PUBLIC': '银行对公', 'P2P_LOAN': 'P2P借贷', 'P2P_FINANCING': 'P2P理财', 'CONSUMER_FINANCE_COMPANY': '消费金融公司', 'SMALL_LOAN_AGENCY': '小贷机构', 'CAR_FINANCE': '汽车金融', 'GUARANTEE': '担保', 'INSURANCE': '保险', 'FILE_SOURCE_TYPES_OTHER': '其他'}
behaviorlog = logging.getLogger('behavior')
BIAOZHU = ['cus_num', 'id', 'cell', 'email', 'qq_num', 'name', 'home_addr', 'home_tel', 'biz_addr', 'biz_tel', 'other_addr', 'bank_card1', 'bank_card2', 'flag1', 'flag2', 'flag', 'def_days', 'def_times', 'amount', 'notes', 'apply_date', 'observe_date', 'apply_channel', 'apply_id', 'apply_addr', 'apply_amount', 'apply_product', 'approval_status', 'approval_date', 'custApiCode', 'approval_amount', 'collateral', 
                'loan_date', 'loan_purpose', 'loan_status', 'repayment_periods', 'loan_info', 'age', 'race', 'gender', 'birthday', 'marriage', 'edu', 'wechat_city', 'wechat_name', 'wechat_province', 'providentfund', 'social_security', 'id_ps', 'id_start', 'id_end', 'id_city', 'id_type', 'civic_addr', 'civic_status', 'postalcode', 'city', 'province', 'basic_info', 'contact_name_1', 'contact_relation_1', 
                'contact_cell_1', 'contact_name_2', 'contact_relation_2', 'contact_cell_2', 'contact_name_3', 'contact_relation_3', 'contact_cell_3', 'contact_name_4', 'contact_relation_4', 'contact_cell_4', 'contact_name_5', 'contact_relation_5', 'contact_cell_5', 'contact_info', 'if_house', 'if_vehicle', 'housing_cate', 'vehicle_id', 'vehicle_type', 'biz_name', 'biz_size', 'industry', 'company_cate', 
                'salary', 'position', 'working_period', 'worth_info', 'acc_open_date', 'card_level', 'branch', 'currency', 'ins_balance', 'update_balance', 'updaet_capital', 'update_date', 'update_overduepayment', 'update_interest', 'update_overlimitfee', 'update_servicefee', 'bill_day', 'bill_post', 'bill_addr', 'credit_info', 'ins_amount', 'ins_date_claims', 'ins_firstlogindate', 'ins_newvehicleprice', 
                'ins_period', 'ins_yearly_claims_num', 'ins_info', 'imei', 'imsi','event', 'af_swift_number', 'mobile_type', 'gid', 'other_var1', 'var_exp1', 'other_var2', 'var_exp2', 'other_var3', 'var_exp3', 'other_var4', 'var_exp4', 'other_var5', 'var_exp5', 'oth_info', 'org_num', 'reg_num', 'driver_number', 'car_code']

class SourceFileView(View):
    def get(self, request):
        if request.user.member.mem_type != Member.CHECKER:
            raise Http404
        query_custom = request.GET.get('cus_id', '')
        query_time1 = request.GET.get('time1', '')
        query_time2 = request.GET.get('time2', '')
        query_filename = request.GET.get("file_name", '')
        page_num = request.GET.get('page', 1)
        manage = request.user.member
        analy = manage.analyst_custom
        if analy == None:
            analy = Member.objects.get(mem_type=Member.ANALYSTS, checker_custom= manage)

        custom_ids = []
        customs = Member.objects.filter(analyst_custom=analy, mem_type=1)
        for custom in customs:
            custom_ids.append(custom.id)
        custom_ids.append(analy.id)
        query_custom_id ='ALL'
        if query_custom == 'ALL':
            files = SourceFile.objects.filter(custom_id__in=custom_ids, is_delete=False).exclude(extra_info='抽样文件').order_by('-create_time')
        elif query_custom:
            query_custom = Member.objects.get(pk=query_custom)
            query_custom_id = query_custom.id
            files = SourceFile.objects.filter(custom_id=query_custom, is_delete=False).exclude(extra_info='抽样文件').order_by('-create_time')
        else:
            files = SourceFile.objects.filter(custom_id__in=custom_ids, is_delete=False).exclude(extra_info='抽样文件').order_by('-create_time')
        if query_time1:
            query_time = query_time1[-4:] + '-' + query_time1[:2] + '-' + query_time1[3:5]
            files = files.filter(create_time__gte=query_time)
        if query_time2:
            query_time = query_time2[-4:] + '-' + query_time2[:2] + '-' + query_time2[3:5]
            files = files.filter(create_time__lte=query_time)
        if query_filename:
            files = files.filter(filename__contains=query_filename)
        p = Paginator(files, 15)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'manage/source_file.html', {'page': page, 'customs': customs,'cus_id': query_custom, 'file_name': query_filename, 'query_custom_id': query_custom_id, 'time1': query_time1, 'time2': query_time2})     


class UpSourceFileView(View):
    def get(self, request):
        if request.user.member.mem_type != Member.CHECKER:
            raise Http404

        manage = request.user.member
        analy = manage.analyst_custom
        if analy == None:
            analy = Member.objects.get(mem_type=Member.ANALYSTS, checker_custom= manage)
        customs = Member.objects.filter(mem_type=Member.CUSTOM, analyst_custom=analy, b_done_over=False).order_by('-id')
        return render(request, 'manage/up_source_file.html',
                {'customs': customs,
                'file_source_type': SourceFile.FILE_SOURCE_TYPES,
                'guarantee_type': SourceFile.GUARANTEE_TYPE,
                'user_type': SourceFile.USER_TYPE})

    def post(self, request):
        if request.user.member.mem_type != Member.CHECKER:
            raise Http404
        file = request.FILES.get('file', '')
        extra_info = request.POST.get('extra_info', '')
        cus_id = request.POST.get('cus_id', '')
        file_source_type = request.POST.get('file_source_type')
        guarantee_type = request.POST.get('guarantee_type')
        user_type = request.POST.get('user_type')
        loan_deadline = request.POST.get('loan_deadline', None)
        loan_amount = request.POST.get("loan_amount", None)
        if loan_deadline:
            loan_deadline = loan_deadline.strip()
        if loan_amount:
            loan_amount = loan_amount.strip()

        err = []
        if not file:
            err.append('请选择一个文件')
        elif not file_source_type:
            err.append('选择文件客户群')
        elif not file_source_type or not guarantee_type:
            err.append('请选择客户群和担保类型')
        elif not user_type:
            err.append('请选择用户对象')
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
                err.append('文件行数不得超过40万')
        if err:
            manage = request.user.member
            analy = manage.analyst_custom
            if analy == None:
                analy = Member.objects.get(mem_type=Member.ANALYSTS, checker_custom= manage)
            customs = Member.objects.filter(mem_type=Member.CUSTOM, analyst_custom=analy, b_done_over=False).order_by('-id')
            return render(request, 'manage/up_source_file.html',
                    {'err': '\n'.join(err),'customs': customs,
                        'file_source_type': SourceFile.FILE_SOURCE_TYPES,
                        'guarantee_type': SourceFile.GUARANTEE_TYPE,
                        'user_type': SourceFile.USER_TYPE})

        guarantee_type = guarantee_type.replace('CREDIT_LOAD', '信用贷款').replace('MORTGAGE_LOAN', '抵押贷款').replace('BOTH', '兼有').replace('GUARANTEE_TYPE_OTHER', '其他')
        user_type = user_type.replace('USUAL', '普通个人').replace('WONER', '小业主').replace('COMPANY', '企业').replace('OTHER_USER', '其他')
        if file_source_type:
            file_source_type = SOURCE_TYPE[file_source_type]

        cus = get_object_or_404(Member, pk=int(cus_id))
        sf = SourceFile(custom=cus, extra_info=extra_info,
                file_size=file.size, file_from=cus.name,
                file_source_type=file_source_type,
                guarantee_type=guarantee_type,
                user_type=user_type,
                loan_deadline=loan_deadline,
                loan_amount=loan_amount)
        sf.total_lines = total_lines
        lines = util.readtxtfile(file.temporary_file_path())
        splitor_status = True # 是否可以直接被标注
        items = lines[0].split(',')
        for line in  items:
            if line in BIAOZHU:
                continue
            else:
                splitor_status = False
                break
        if 'observe_date' not in items:
                splitor_status = False
        if 'id' in items or 'cell' in items or 'email' in items:
            pass
        else:
            splitor_status = False
        basename, ext = os.path.splitext(file.name)
        filename = '_'.join([cus.name, basename, time.strftime('%Y%m%d-%H%M')]) + ext
        sf.filename.save(filename, file)
        sf.can_down.add(cus)
        sf.can_down.add(cus.datatran_custom)
        sf.can_delete = True
        sf.save()
        if splitor_status:
            sf.fields = lines[0]
            sf.splitor = ','
            sf.is_checked = True
            sf.skip_lines = 1
        sf.save()
        manage = request.user.member
        behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + 'checker名为：' + manage.name + ' 上传了' + filename + '文件')
        return redirect('/als/manage/source_file/')


class DelSourceFile(View):
    def get(self, request):
        file_id = request.GET.get('fileid')
        member =request.user.member
        file = SourceFile.objects.get(pk=int(file_id))
        behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') + 'checker名为：' + str(member.name) + '删除了文件：' + str(file.filename))
        file.delete()
        return redirect('/als/manage/source_file/')

class SourceFileHeadView(View):
    def get(self, request):
        if request.user.member.mem_type != Member.CHECKER:
            raise Http404
        try:
            file = SourceFile.objects.get(pk=int(request.GET['fileid']), is_delete=False)
        except:
            raise Http404
        res, content = util.readfilelines(settings.MEDIA_ROOT + file.filename.name, 7)
        return HttpResponse(json.dumps(content), content_type='application/json')

class SaveSourceTagView(View):

    def get(self, request):
        if request.user.member.mem_type != Member.CHECKER:
            raise Http404
        fields = request.GET.get('field', '')
        fileid = request.GET.get('header', 'a')
        splitor = request.GET.get('splitor', '').decode('string_escape')
        skip_num = request.GET.get('skip', '')
        if not all([fields, fileid, splitor]):
            return HttpResponse(json.dumps({'msg': '缺少必要参数!'}), content_type="application/json")
        try:
            skip_num = int(skip_num)
        except:
            return HttpResponse(json.dumps({'msg': '跳过行数值错误!'}), content_type="application/json")
        try:
            fileid = int(fileid)
        except:
            return HttpResponse(json.dumps({'msg': '文件id不为整数!'}), content_type="application/json")
        if not mapping.check_fields_valid(fields.split(',')):
            return HttpResponse(json.dumps({'msg': '标注错误!'}), content_type="application/json")
        try:
            file = SourceFile.objects.get(pk=fileid)
        except:
            return HttpResponse(json.dumps({'msg': '该文件不存在!'}), content_type="application/json")
        #if not file.is_checked or file.fields != fields or file.splitor != splitor or file.skip_lines != skip_num:
        res, msg = mapping.check_before_mapping(settings.MEDIA_ROOT + file.filename.name, fields, splitor, skip_num)
        if not res:
            return HttpResponse(json.dumps({'msg': msg}), content_type="application/json")
        file.fields = fields
        file.splitor = splitor
        file.skip_lines = skip_num
        file.is_checked = True
        file.save()
        return JsonResponse({'msg': msg})


class MappedFileListView(View):
    def get(self, request):
        try:
            file_id = request.GET['fileid']
            page_num = request.GET.get('page', 1)
            source_file = SourceFile.objects.get(pk=file_id)
            if source_file.is_delete:
                raise Http404
            if not page_num :
                page_num = 1
            files = MappingedFile.objects.filter(source_file=file_id, is_crypt=False).order_by('-create_time')
            p = Paginator(files, 15)
        except:
            raise Http404
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'manage/mapped_files.html', {'page': page, 'fileid':file_id})
