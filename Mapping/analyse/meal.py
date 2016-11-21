#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.views.generic import View
from django.http import Http404, HttpResponse
from django.conf import settings
from django.core.servers.basehttp import FileWrapper

import os
import time
import subprocess
import xlrd
import traceback
import logging
import MySQLdb
import json
from account.models import Member
from models import MealHead, Meal, MealSort
from util import readtxtfile

behaviorlog = logging.getLogger('behavior')
errlog = logging.getLogger('daserr')

class MealList(View):
    def get(self, request):
        if request.user.member.mem_type != Member.MEAL:
            raise Http404
        page_num = request.GET.get('page', 1)
        #member = request.user.member
        meals = Meal.objects.filter().order_by('-create_time')
        p = Paginator(meals, 25)
        try:
            page = p.page(int(page_num))
        except:
            page = p.page(1)
        return render(request, 'meal/meal_list.html', {'page': page})

class MealUpFile(View):
    def get(self, request):
        if request.user.member.mem_type != Member.MEAL:
            raise Http404
        return render(request, 'meal/up_file.html')

    def post(self, request):
        meal_name = request.POST.get('meal_name', '')
        chinese_name = request.POST.get('chinese_name', '')
        interface = request.POST.get('interface', '')
        file = request.FILES.get('file', '')
        for key, item in {meal_name: '套餐接口请求名称', chinese_name: '套餐中文显示名称', interface: '所属接口'}.items():
            if not key:
                return render(request, 'meal/up_file.html',{'err': '\n 缺少：' + item})
        if not file:
            return render(request, 'meal/up_file.html', {'err': '\n 请选择表头文件'})
        else:
            _, file_ext = os.path.splitext(file.name)
            if file_ext[1:] not in  ['txt', 'csv']:
                return render(request, 'meal/up_file.html', {'err': '\n 只允许上传txt, csv格式的文件'})
        meal_is = Meal.objects.filter(name=meal_name, interface=interface)
        if meal_is:
            return render(request, 'meal/up_file.html', {'err': '\n 该套餐已存在'})
        meal = Meal(name=meal_name, chinese_name=chinese_name, interface=interface, head_status=True)
        meal.save()
        if interface == '通用版接口3.0':
            sort = MealSort.objects.get(name='sort')
            sort_head = MealSort.objects.get(name='sort_head')
        elif interface == '信贷版接口3.0':
            sort = MealSort.objects.get(name='xd_sort')
            sort_head = MealSort.objects.get(name='xd_sort_head')
        elif interface == '海纳api':
            lines = readtxtfile(file.temporary_file_path())
            for line in lines:
                heads = line.split(':')
                if len(heads) == 2:
                    meal_head = MealHead(meal=meal, name=heads[0], head=heads[1])
                    meal_head.save()
            return redirect('/als/meal/meal_list/')

        sort.sort = sort.sort + ',' + meal_name
        sort_head.sort = sort_head.sort + ',' + meal_name
        sort.save()
        sort_head.save()
        lines = readtxtfile(file.temporary_file_path())
        for line in lines:
            heads = line.split(':')
            if len(heads) == 2:
                meal_head = MealHead(meal=meal, name=heads[0], head=heads[1])
                meal_head.save()
        return redirect('/als/meal/meal_list/')

class DeleteMeal(View):
    def get(self, request):
        fileid = request.GET.get('fileid', '')
        if not fileid:
            return HttpResponse(json.dumps("缺少文件id"), content_type="application/json")
        meal = Meal.objects.get(pk=fileid)
        meal_heads = MealHead.objects.filter(meal=meal)
        meal_heads.delete()
        meal.delete()
        return HttpResponse(json.dumps('删除成功'), content_type='application/json')

class ChangeHead(View):
    def get(self, request):
        meal_id = request.GET.get('meal_id', '')
        if not meal_id:
            return HttpResponse(json.dump('缺套餐id'), content_type='application/json')
        meal = Meal.objects.get(pk=meal_id)
        if meal:
            return render(request, 'meal/up_heads.html', {'meal_name': meal.name})
        else:
            return HttpResponse(json.dumps('套餐不存在'), content_type='application/json')

    def post(self, request):
        meal_name = request.POST.get('meal_name')
        file = request.FILES.get('file', '')
        meal = Meal.objects.get(name=meal_name)
        meal_heads = MealHead.objects.filter(meal=meal).order_by('id')
        meal_heads.delete()
        if not file:
            return render(request, 'meal/up_heads.html', {'err': '\n 请选择表头文件'})
        else:
            _, file_ext = os.path.splitext(file.name)
            if file_ext[1:] not in  ['txt', 'csv']:
                return render(request, 'meal/up_heads.html', {'err': '\n 只允许上传txt, csv格式的文件'})
        lines = readtxtfile(file.temporary_file_path())
        for line in lines:
            heads = line.split(':')
            if len(heads) == 2:
                meal_head = MealHead(meal=meal, name=heads[0], head=heads[1])
                meal_head.save()
        return redirect('/als/meal/meal_list/')


class GetHeads(View):
    def get(self, request):
        meal_id = request.GET.get('meal_id', '')
        meal = Meal.objects.get(pk=meal_id)
        meal_heads = MealHead.objects.filter(meal = meal).order_by('id')
        if meal_heads:
            return render(request, 'meal/meal_heads.html', {'heads': meal_heads})
        else:
            return render(request, 'meal/meal_heads.html', {'err': 'nothing'})

class MealSortView(View):
    def get(self, request):
        try:
            sort = MealSort.objects.get(name='sort')
            sort_head = MealSort.objects.get(name='sort_head')
            xd_sort = MealSort.objects.get(name='xd_sort')
            xd_sort_head = MealSort.objects.get(name='xd_sort_head')
            if '|' in xd_sort.sort:
                xd_sort_qz, xd_sort_xy, xd_sort_score = xd_sort.sort.split('|')
            else:
                xd_sort_qz = xd_sort_xy = xd_sort_score = ''
            return render(request, 'meal/sort.html', {'sort': sort.sort, 'xd_sort_qz': xd_sort_qz, 'xd_sort_xy': xd_sort_xy, 'xd_sort_score': xd_sort_score,'sort_head': sort_head.sort, 'xd_sort_head': xd_sort_head.sort})
        except Exception, e:
            return render(request, 'meal/sort.html', {'sort': '', 'xd_sort': '', 'sort_head': '', 'xd_sort_head': ''})

    def post(self, request):
        sort = request.POST.get('sort', '')
        sort_head = request.POST.get('sort_head', '')
        xd_sort_head = request.POST.get('xd_sort_head', '')
        xd_sort_qz = request.POST.get('xd_sort_qz', '')
        xd_sort_xy = request.POST.get('xd_sort_xy', '')
        xd_sort_score = request.POST.get('xd_sort_score', '')
        xd_sort = xd_sort_qz + '|' + xd_sort_xy + '|' + xd_sort_score

        for key, item in {'sort': sort, 'xd_sort': xd_sort, 'sort_head': sort_head, 'xd_sort_head': xd_sort_head}.items():
            meal_sort = MealSort.objects.get(name=key)
            meal_sort.sort = item
            meal_sort.save()
        return redirect('/als/meal/meal_list/')
