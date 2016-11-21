#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.core.servers.basehttp import FileWrapper
from django.views.generic import View
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction

import logging
import os
import json
import traceback
import cStringIO as StringIO

from analyse.analy import PER_PAGE_NUM
from analyse.models import SourceFile, ThirdMappedFile, MappingedFile

from util import readfilelines, iter_txt
import combine_file
import mapping

errlog = logging.getLogger('daserr')


class SourceFilesView(View):
    def get(self, request):
        page_num = request.GET.get('page', 1)
        files = SourceFile.objects.filter(custom__datatran_custom=request.user.member).order_by('-create_time')
        p = Paginator(files, PER_PAGE_NUM)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'datatrans/cus_files.html', {'page': page})


class PickFileView(View):
    @never_cache
    def get(self, request):
        try:
            fileid = int(request.GET.get('fileid'))
            columns = request.GET.get('columns').split(',')[:-1]
            coln = len(columns)
            splitor = request.GET.get('splitor')
        except:
            return HttpResponse('参数错误！')
        file = []
        sfile = get_object_or_404(SourceFile, custom__datatran_custom=request.user.member, pk=fileid)
        filepath = settings.MEDIA_ROOT + sfile.filename.name
        for line in iter_txt(filepath):
            line = line.strip().split(splitor)
            if len(line) != coln:
                continue
            tline = []
            for i in range(coln):
                if columns[i] == 'check':
                    tline.append(line[i])
            file.append(','.join(tline))
        data = StringIO.StringIO()
        data.write('\n'.join(file))
        data.seek(0)
        response = HttpResponse(FileWrapper(data), content_type='application/zip')
        response['Content-Disposition'] = 'attachemt; filename=' + os.path.basename(str(sfile))
        return response


class ThirdMappedHeadView(View):
    def get(self, request):
        fileid = int(request.GET.get('fileid'))
        file = get_object_or_404(ThirdMappedFile, uploader=request.user.member, pk=fileid)
        res, content = readfilelines(settings.MEDIA_ROOT + file.file.name, 7)
        splitor = file.splitor
        n_content = []
        for line in content:
            n_content.append(splitor.join(line.split(splitor)[:5]))
        return HttpResponse(json.dumps(n_content), content_type='application/json')


class SourceFileHeadView(View):
    def get(self, request):
        fileid = int(request.GET.get('fileid'))
        file = get_object_or_404(SourceFile, custom__datatran_custom=request.user.member, pk=fileid)
        res, content = readfilelines(settings.MEDIA_ROOT + file.filename.name, 7)
        return HttpResponse(json.dumps(content), content_type='application/json')


class ThirdMapedFileView(View):
    def get(self, request):
        page_num = request.GET.get('page', 1)
        files = ThirdMappedFile.objects.filter(uploader=request.user.member).order_by('-create_time')
        p = Paginator(files, PER_PAGE_NUM)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'datatrans/mapped_files.html', {'page': page})


class UpMappedFileView(View):
    def get(self, request):
        return render(request, 'datatrans/up_mappedfile.html', {'companys': ThirdMappedFile.Third_Company})

    @transaction.atomic
    def post(self, request):
        file_desc = request.POST.get('file_desc').strip()
        file = request.FILES.get('file')
        file_from = request.POST.get('file_from')

        if not file:
            return render(request, 'datatrans/up_mappedfile.html', {'err': '必须选择文件！', 'companys': ThirdMappedFile.Third_Company})
        if ThirdMappedFile.objects.filter(file='thirdmapped_file/' + file.name).exists():
            return render(request, 'datatrans/up_mappedfile.html', {'err': '此文件已存在，请换个文件名！', 'companys': ThirdMappedFile.Third_Company})
        if os.path.splitext(file.name)[1][1:] != 'txt':
            return render(request, 'datatrans/up_mappedfile.html', {'err': '只允许上传txt文件！', 'companys': ThirdMappedFile.Third_Company})
        member = request.user.member
        tmf = ThirdMappedFile(uploader=member, file_from=file_from, file=file,
                file_desc=file_desc, file_size=file.size, splitor=',')
        tmf.save()
        tmf.can_down.add(member)
        tmf.save()
        return redirect('/als/datatrans/third_mapedfile/')


class SaveTagView(View):
    @transaction.atomic
    @never_cache
    def get(self, request):
        try:
            fields = request.GET['field']
            fileid = int(request.GET['header'])
            #splitor = request.GET['splitor'].decode('string_escape')
            skip = int(request.GET['skip'])
        except:
            return HttpResponse(json.dumps({'msg': '解析参数错误！'}), content_type='application/json')
        if not fields or not fileid:
            return HttpResponse(json.dumps({'msg': '参数错误！'}), content_type='application/json')
        tmp = fields.split(',')
        fields = [x.strip() for x in tmp]
        i = -1
        j = -1
        for m in range(len(fields)):
            if fields[m]:
                i = m
            else:
                if j == -1:
                    j = m
        if (j-i) <= 0:
            return HttpResponse(json.dumps({'msg':'标注失败，key必须在最前面！'}), content_type='application/json')
        fields = [x.strip() for x in tmp if x.strip()]
        third_file = get_object_or_404(ThirdMappedFile, uploader=request.user.member, pk=fileid)
        third_file.fields = ','.join(fields)
        #third_file.splitor = splitor
        third_file.skip_lines = skip
        third_file.save()
        return HttpResponse(json.dumps({'msg':'标注成功！'}), content_type='application/json')


class ListSourceFileView(View):
    def get(self, request):
        files = SourceFile.objects.filter(custom__datatran_custom=request.user.member).order_by('-create_time')[:40]
        res = {}
        for file in files:
            #if not file.fields:
                #fields = 'NULL'
            #else:
                #fields = file.fields
            #res[file.pk] = os.path.basename(file.filename.name) + ' : ' + fields
            res[file.pk] = os.path.basename(file.filename.name)
        return HttpResponse(json.dumps(res), content_type='application/json')


class StartDistributeView(View):
    def check_valid(self, third_file, source_files):
        third_fields = [x for x in third_file.fields.split(',') if x]
        if not third_fields:
            return False
        for file in source_files:
            fields = [x for x in file.fields.split(',') if x]
            for t in third_fields:
                if t not in fields:
                    return False
        return True

    def get(self, request):
        try:
            fileid = int(request.GET.get('fileid'))
            fileids = [int(x) for x in request.GET.get('fileids').split(',')]
            third_file = ThirdMappedFile.objects.get(uploader=request.user.member, pk=fileid)
        except:
            return HttpResponse(json.dumps('出错！'), content_type='application/json')
        source_files = SourceFile.objects.filter(custom__datatran_custom=request.user.member, pk__in=fileids)

        if len(fileids) != source_files.count():
            return HttpResponse(json.dumps('源文件个数出错,通知同志管理员！'), content_type='application/json')
        #检查本身和关联文件
        if not self.check_valid(third_file, source_files):
            return HttpResponse(json.dumps('某个源文件标注缺少值必要key！'), content_type='application/json')
        third_file.trans_status = '分配中...'
        third_file.save()
        try:
            combine_file.third_to_source(third_file, source_files, request.user.member)
        except:
            errlog.error('分配第三方结果出错！第三方文件：' + str(third_file) + '\n')
            errlog.error(traceback.format_exc())
        finally:
            third_file.trans_status = '分配结束'
            third_file.save()
        return HttpResponse(json.dumps('分配结束！'), content_type='application/json')


class ChildFilesView(View):
    def get(self, request):
        page_num = int(request.GET.get('fileid'))
        parent_file = get_object_or_404(ThirdMappedFile, uploader=request.user.member, pk=page_num)
        files = MappingedFile.objects.filter(parent_file=parent_file).order_by('-create_time')[:50]
        return render(request, 'datatrans/child_files.html', {'page': files, 'parentid': page_num})


class DelChildView(View):
    def get(self, request):
        page_num = int(request.GET.get('parentid'))
        fileid = int(request.GET.get('fileid'))
        parent_file = get_object_or_404(ThirdMappedFile, uploader=request.user.member, pk=page_num)
        file = get_object_or_404(MappingedFile,parent_file=parent_file, pk=fileid)
        file.delete()
        return redirect('/als/datatrans/child_files/?fileid='+str(page_num))


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
            return HttpResponse(json.dumps({'msg': '通知管理员!'}), content_type="application/json")
        if not mapping.check_fields_valid(fields.split(',')):
            return HttpResponse(json.dumps({'msg': '标注错误!'}), content_type="application/json")
        try:
            file = SourceFile.objects.get(custom__datatran_custom=request.user.member, pk=fileid)
        except:
            return HttpResponse(json.dumps({'msg': '该文件存在!'}), content_type="application/json")
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
