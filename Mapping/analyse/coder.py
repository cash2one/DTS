#-*- coding: utf-8 -*-
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.views.generic import View
from django.http import Http404, HttpResponse, JsonResponse
from uuid import uuid4
import traceback
import logging
import json
from account.models import Member
from analyse.models import Coder

behaviorlog = logging.getLogger('behavior')
errlog = logging.getLogger('daserr')


class CodeListView(View):
    def get(self, request):
        if request.user.member.mem_type != Member.CODER:
            raise Http404
        page_num = request.GET.get('page', 1)
        coder = request.user.member
        code = Coder.objects.filter(member = coder).order_by('-permission')
        p = Paginator(code, 15)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'coder/code_list.html', {'page': page})


class DataCodeList(View):
	def get(self, request):
		if request.user.member.mem_type != Member.CODER:
			raise Http404
		page_num = request.GET.get('page', 1)
		code = Coder.objects.filter(permission = 'loss_data')
		p = Paginator(code, 15)
		try:
			page = p.page(int(page_num))
		except:
			page = p.page(1)
		return render(request, 'coder/code_list.html', {'page': page})


class MarkCodeList(View):
	def get(self, request):
		if request.user.member.mem_type != Member.CODER:
			raise Http404
		page_num = request.GET.get('page', 1)
		# coder = request.user.member
		code = Coder.objects.filter(permission = 'loss_mark')
		p = Paginator(code, 15)
		try:
			page = p.page(int(page_num))
		except:
			page = p.page(1)
		return render(request, 'coder/code_list.html', {'page': page})


class CollCodeList(View):
	def get(self, request):
		if request.user.member.mem_type != Member.CODER:
			raise Http404
		page_num = request.GET.get('page', 1)
		code = Coder.objects.filter(permission = 'loss_collect')
		p = Paginator(code, 15)
		try:
			page = p.page(int(page_num))
		except:
			page = p.page(1)
		return render(request, 'coder/code_list.html', {'page': page})


class CreateCode(View):
	def get(self, request):
		if request.user.member.mem_type != Member.CODER:
			raise Http404
		else :
			member = request.user.member

		results = []
		for per in ['data','mark','coll']:
			for i in xrange(1,31):
				uuid = ''.join(str(uuid4()).split('-'))
				code = uuid + per
				results.append(code)
		try:
			for code in results:
				if code[-4:] == 'data':
					Coder.objects.create(
						member = member,
						code = code[:-4],
						permission = 'loss_data'
						)
				if code[-4:] == 'mark':
					Coder.objects.create(
						member = member,
						code = code[:-4],
						permission = 'loss_mark'
						)
				if code[-4:] == 'coll':
					Coder.objects.create(
						member = member,
						code = code[:-4],
						permission = 'loss_collect'
						)

		except Exception, e:
			print traceback.format_exc()
		
		return redirect("/als/coder/code_list/")


class DeleteCode(View):
	def get(self,request):
		Coder.objects.filter(is_outdate='True').delete()
		return redirect("/als/coder/code_list/")


class DeleteThisCode(View):
	def get(self, request):
		try:
			codeid = request.GET.get("codeid","")
			if not codeid:
				return HttpResponse("缺少id")
			code = Coder.objects.get(pk=codeid)
			if code.to_user == True:
				code.delete()
				return JsonResponse({"msg":0})
			else:
				return JsonResponse({"msg":"删除失败"})
		except Exception, e:
			print traceback.format_exc()
		

class ToUser(View):
	def get(self, request):
		codeid = request.GET.get("codeid","")
		if not codeid:
			return HttpResponse("缺少id")
		code = Coder.objects.get(pk=codeid)
		if code.to_user == False:
			code.to_user = True
			code.save()
			return JsonResponse({'msg':0})
		else :
			return JsonResponse({'msg':"标注失败"})
