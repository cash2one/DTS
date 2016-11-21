#!/usr/bin/python
# -*- coding: utf-8 -*-


from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.views.generic import View
from django.http import HttpResponse, Http404
from django.db import transaction


import logging
import time
import os
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from account.models import Member
from account.views import LoginView
from analyse.models import SourceFile, ThirdMappedFile, MappingedFile, ReportFile
from analyse.util import create_validate_code

errlog = logging.getLogger('daserr')
behaviorlog = logging.getLogger('behavior')

#FileTypeCod:
    #SourceFile         :1
    #ThirdMappedFile    :2
    #MappingedFile      :3
    #ReportFile         :4

class CheckDownloads(View):
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    def get(self, request, ft, fid):
        ft = int(ft)
        fid = int(fid)
        member = request.user.member

        if ft == 1:
            sf = get_object_or_404(SourceFile, pk=fid, can_down__pk=member.pk)
            file = sf.filename
        elif ft == 2:
            tmf = get_object_or_404(ThirdMappedFile, pk=fid, can_down__pk=member.pk)
            file = tmf.file
        elif ft == 3:
            mf = get_object_or_404(MappingedFile, pk=fid, can_down__pk=member.pk)
            file = mf.file
        elif ft == 4:
            rf = get_object_or_404(ReportFile, pk=fid, can_down__pk=member.pk)
            file = rf.report_file
        else:
            raise Http404
        path = file.name
        file_path = os.path.basename(path)
        res = HttpResponse()
        if path[-3:] == 'txt':
            res['Content-type'] = 'text/plain'
        elif path[-3:] == 'xls' or path[-4:] == 'xlsx':
            res['Content-type'] = 'application/vnd.ms-excel'
        elif path[-3:] == 'rar' or path[-3:] == 'zip':
            res['Content-type'] = 'application/x-zip-compressed'
        else:
            res['Content-type'] = 'application/octet-stream'
        clientSystem = request.META['HTTP_USER_AGENT']
        if clientSystem.find('Windows') > -1:
            filename = file_path.encode('cp936')
        else:
            filename = file_path.encode('utf-8')
	    ip = self.get_client_ip(request)
        behaviorlog.error(time.strftime('%Y%m%d-%H%M%S') +' IP :'+ ip +'用户 : ' + member.name + '下载了文件：' + file_path)
        res['Content-Disposition'] = 'attachment; filename=' + filename
        #res['Content-Disposition'] = 'attachment; filename=' + os.path.basename(path).encode('utf-8')
        res['X-Accel-Redirect'] = '/protected/' + path.strip().replace('\n', '').encode('utf-8')
        return res


class ManageDownView(View):
    def get(self, request, ft, fid):
        ft = int(ft)
        fid = int(fid)
        if request.user.member.mem_type != Member.CHECKER:
            raise Http404

        if ft == 1:
            sf = get_object_or_404(SourceFile, pk=fid)
            file = sf.filename
        elif ft == 2:
            tmf = get_object_or_404(ThirdMappedFile, pk=fid)
            file = tmf.file
        elif ft == 3:
            mf = get_object_or_404(MappingedFile, pk=fid)
            file = mf.file
        elif ft == 4:
            rf = get_object_or_404(ReportFile, pk=fid)
            file = rf.report_file
        else:
            raise Http404
        path = file.name
        res = HttpResponse()
        if path[-3:] == 'txt':
            res['Content-type'] = 'text/plain'
        else:
            res['Content-type'] = 'application/octet-stream'
        res['Content-Disposition'] = 'filename=' + os.path.basename(path).encode('utf-8')
        #res['Content-Disposition'] = 'attachment; filename=' + os.path.basename(path).encode('utf-8')
        res['X-Accel-Redirect'] = '/protected/' + path.strip().replace('\n', '').encode('utf-8')
        return res

class CreateValid(View):
    def get(self, request):
        mstream = StringIO.StringIO()

        img, code = create_validate_code()
        img.save(mstream, 'GIF')
        request.session['validate'] = code.strip()
        return HttpResponse(mstream.getvalue(), 'image/gif')
