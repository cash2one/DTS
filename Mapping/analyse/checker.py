#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import View
from django.http import HttpResponse, Http404
from django.db import transaction
from django.conf import settings


import os
import time
import subprocess
import json

from account.models import Member
from analyse.models import SourceFile, MappingedFile, ReportFile
from analyse.views import UP_FILE_MAX_LINES
import util
import mapping


class SourceFileView(View):
    def get(self, request):
        page_num = request.GET.get('page', 1)
        source_files = SourceFile.objects.filter(custom__checker_custom=request.user.member).order_by('-create_time')
        p = Paginator(source_files, 15)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'checker/source_file.html', {'page': page})


class UpSourceFileView(View):
    def get(self, request):
        customs = Member.objects.filter(checker_custom=request.user.member, b_done_over=False).order_by('-id')
        return render(request, 'checker/up_source_file.html',
                {'customs': customs, 'file_source_type': SourceFile.FILE_SOURCE_TYPES})

    def post(self, request):
        file = request.FILES.get('file', '')
        extra_info = request.POST.get('extra_info', '')
        cus_id = request.POST.get('cus_id', '')

        err = []
        if not file:
            err.append('请选择一个文件！')
            return render(request, 'checker/up_source_file.html', {'err': '\n'.join(err)})
        _, file_ext = os.path.splitext(file.name)
        if file_ext[1:] != 'txt':
            err.append('只允许上传txt格式的文件')
        total_lines = int(subprocess.check_output('cat %s | wc -l' % file.temporary_file_path(), shell=True))
        if total_lines > UP_FILE_MAX_LINES:
            err.append('文件行数不得超过40万')
        if err:
            return render(request, 'checker/up_source_file.html', {'err': '<br>'.join(err)})
        cus = get_object_or_404(Member, pk=int(cus_id))
        sf = SourceFile(custom=cus, extra_info=extra_info,
                file_size=file.size, file_from=cus.name)
        sf.total_lines = total_lines
        basename, ext = os.path.splitext(file.name)
        filename = '_'.join([cus.name, basename, time.strftime('%Y%m%d-%H%M')]) + ext
        sf.filename.save(filename, file)
        sf.can_down.add(cus)
        sf.can_down.add(request.user.member)
        sf.can_down.add(cus.datatran_custom)
        sf.save()
        return redirect('/als/checker/source_file/')


class DelSourceFile(View):
    def get(self, request):
        try:
            file = SourceFile.objects.get(pk=int(request.GET['fileid']))
        except:
            raise Http404
        file.delete()
        return redirect('/als/checker/source_file/')


class SourceFileHeadView(View):
    def get(self, request):
        try:
            file = SourceFile.objects.get(pk=int(request.GET['fileid']))
        except:
            raise Http404
        res, content = util.readfilelines(settings.MEDIA_ROOT + file.filename.name, 7)
        return HttpResponse(json.dumps(content), content_type='application/json')


class SaveSourceTagView(View):
    @transaction.atomic
    def get(self, request):
        fields = request.GET.get('field','')
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
        if not file.is_checked or file.fields != fields or file.splitor != splitor or file.skip_lines != skip_num:
            res, msg = mapping.check_before_mapping(settings.MEDIA_ROOT + file.filename.name, fields, splitor, skip_num)
            if not res:
                return HttpResponse(json.dumps({'msg': msg}), content_type="application/json")
            file.fields = fields
            file.splitor = splitor
            file.skip_lines = skip_num
            file.is_checked = True
            file.save()
        return HttpResponse(json.dumps({'msg': '标注成功!'}), content_type="application/json")
