#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User

from account.models import Member, Filter
from analyse.mail import send_mail
import random
import json
import traceback
import time


class LoginView(View):
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request):
        if request.META.get('HTTP_HOST') == 'dts.100credit.com':
            ip = self.get_client_ip(request)
            ip_list = Filter.objects.all()[0].ip_list.split(',')
            if ip in ip_list:
                return render(request, 'login.html')
            else:
                return HttpResponse('您的IP是:%s,不在授权范围以内，请联系与您沟通的工作人员'%(ip))
        else:
            return render(request, 'login.html')
        
    def post(self, request):
        uname = request.POST.get('uname', '')
        passwd = request.POST.get('passwd', '')
        validate = request.POST.get('validate', '').lower()
        validate2 = request.session.get('validate', '').lower()
        if not validate or not validate2 or validate != validate2:
            return render(request, 'login.html', {'err': '验证码不正确', 'uname': uname})

        user = authenticate(username=uname, password=passwd)
        err = ''
        if user:
            if user.is_active:
                ip = self.get_client_ip(request)
                try:
                    ips = user.member.allow_ips.split(',')
                except Exception:
                    err = '您的IP是:%s,你还没有添加IP白名单。'%(ip)
                    return render(request, 'login.html', {'err': err, 'uname': uname})
                
                
                if ip in ips:
                    login(request, user)
                    return redirect('/')
                else:
                    err = '您的IP是:%s,与账号绑定IP不一致，请联系与您沟通的工作人员'%(ip)
            else:
                #Todo 帐号冻结原因说明
                err = '帐号被冻结，请联系管理员'
        else:
            err = '用户名或密码错误'
        return render(request, 'login.html', {'err': err, 'uname': uname})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('/')

class IndexView(View):
    def get(self, request):
        user = request.user
        m = user.member
        name = user.username
        if m.mem_type == Member.CUSTOM and m.b_first_modify_passwd == False:
            return redirect('als/custom/first_modify_passwd/')
        return render_to_response('include/base.html',{'m': m, 'user': user}, context_instance=RequestContext(request))

class PasswdView(View):
    def get(self, request):
        return render(request, 're_passwd.html')


class VerifyView(View):

    def get(self, request):
        mail = request.GET.get('mail', '')
        mail = mail.strip()
        data = {mail: '邮箱'}
        try:
            for key, value in data.items():
                if not key:
                    return HttpResponse(json.dumps({'err': '请输入邮箱'}), content_type='application/json')
            try:
                member = Member.objects.get(email= mail)
                user = member.user
            except Exception, e:
                return HttpResponse(json.dumps({'err': '系统没有检测到与该邮箱对应的账号'}), content_type='application/json')
            member = Member.objects.get(user=user)
            words = random.randint(1000,9999)
            user.email = str(words) + time.strftime('%H%M%S')
            user.save()
            content = '您好，您的验证码为：' + str(words) + '。您正在申请重置您的DTS账号密码，如非本人操作，请忽视！'
            send_mail(mail,'百融数据测试系统DTS修改密码' , content)
        except Exception, e:
            print traceback.format_exc()
        return HttpResponse(json.dumps({'success': '验证码60秒内有效', 'verify_num': content}), content_type='application/json')

    def post(self, request):
        verify = request.POST.get('verify' '')
        mail = request.POST.get('mail', '')
        if not mail:
            return HttpResponse('请输入邮箱')
        member = Member.objects.get(email=mail)
        user = member.user
        verify_num = user.email
        if len(verify_num) == 10:
            time1 = int(verify_num[4:])
            verify_num = verify_num[:4]
        else:
            return HttpResponse('验证码不匹配，请重新确认')
        time_now = int(time.strftime('%H%M%S'))
        time1 = time_now - time1
        if time1 > 60:
             return HttpResponse('验证码超时，请重新发送验证码')
        if verify_num != verify:
            return HttpResponse('验证码不匹配，请重新确认')
        user.email = ''
        user.set_password('123456')
        user.save()

        user = authenticate(username=user.username, password='123456')
        login(request, user)
        return render_to_response('custom/first_modify_passwd.html',{'m': member}, context_instance=RequestContext(request))
