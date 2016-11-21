#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


class Member(models.Model):

    CHECKER = 0
    CUSTOM = 1
    ANALYSTS = 2
    DATATRANS = 3
    SINGLE = 4
    PHONE = 5
    MEAL = 6
    CODER = 7
    MEMBER_TYPE = (
        (CUSTOM, 'Custom'),
        (ANALYSTS, 'Analysts'),
        (DATATRANS, 'DataTrans'),
        (CHECKER, 'Checker'),
        (SINGLE, 'Single'),
        (PHONE, 'Phone'),
        (MEAL, 'Meal'),
        (CODER, 'Coder'),
    )

    user = models.OneToOneField(User)
    analyst_custom = models.ForeignKey('self', related_name='analycus', limit_choices_to={'mem_type': ANALYSTS }, null=True, blank=True)
    datatran_custom = models.ForeignKey('self', related_name='datatrancus', limit_choices_to={'mem_type': DATATRANS }, null = True, blank=True)
    checker_custom = models.OneToOneField('self', related_name='checker', limit_choices_to={'mem_type': CHECKER }, null = True, blank=True)
    name = models.CharField(max_length=100, verbose_name='名称')
    is_has_new_report = models.BooleanField(default=False)
    b_done_over = models.BooleanField(default=False)
    b_first_modify_passwd = models.BooleanField(default=False)
    mem_type = models.IntegerField(max_length=4, choices=MEMBER_TYPE, default=CUSTOM)
    thread_num = models.IntegerField(max_length=4, default=5)
    passwd_wrong_count = models.IntegerField(max_length=4, default=0)
    allow_ips = models.TextField(max_length=800, null=True, blank=True)
    last_login_ip = models.CharField(max_length=20, null=True, blank=True)
    block_reason = models.CharField(max_length=100, null=True, blank=True)
    last_login_time = models.DateTimeField(null=True, blank=True)
    email  = models.CharField(max_length=100, null= True, blank=True)
    out_in_member = models.IntegerField(max_length=4, default=1, help_text='内部人员为1,外部人员为0')
    permission = models.TextField(max_length=800, default='null', verbose_name='接口权限', help_text='接口请求名称：1为开通')
    permission2 = models.CharField(max_length=10, default='0000000000', verbose_name='新接口权限', help_text='作废')
    portrait_permission = models.CharField(max_length=10,default='1000',verbose_name="画像权限", help_text='作废')
    credit_permission = models.CharField(max_length=10,default='1000',verbose_name="信贷权限", help_text='作废')
    portrait3_permission = models.TextField(max_length=800,default='null',verbose_name='通用版3.0权限')
    credit3_permission = models.TextField(max_length=800,default="null",verbose_name="信贷3.0权限")
    credit3_permission2 = models.CharField(max_length=12,default='000000000',verbose_name="信贷3.0权限2", help_text='月度收支等级/手机有效性/银行客群评分/p2p客群评分/消费金融客群评分')
    custom_num = models.CharField(max_length=15,null=True,blank=True)
    sampling_sort = models.IntegerField(max_length=5, default=01, verbose_name='数据集市中文件个数')
    custom_city = models.CharField(max_length=50, null=True, blank=True, verbose_name='客户总部所在城市')
    taskid = models.CharField(max_length=200, null=True, blank=True, verbose_name='taskid')
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("email", "mem_type"),)
        verbose_name = "系统成员"
        verbose_name_plural = "系统成员列表"
        ordering = ['-id']

    def __unicode__(self):
        return '%s' % str(self.user)


class Queryer(models.Model):
    constom = models.OneToOneField(Member, limit_choices_to={'mem_type': Member.ANALYSTS}, null=True, blank=True)
    name = models.CharField(max_length=50)
    passwd = models.CharField(max_length=20)
    apicode = models.CharField(max_length=20)
    extra_info = models.CharField(max_length=200, null=True, blank=True)
    is_busy = models.BooleanField(default=False)
    do_on_file = models.CharField(max_length=100, null=True, blank=True)
    start_match = models.DateTimeField(null=True, blank=True)
    end_match = models.DateTimeField(null=True, blank=True)
    mapping_files = models.CharField(max_length=1700, null=True, blank=True, verbose_name='近期匹配的文件记录')
    real_name = models.CharField(max_length=50, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "画像查询帐号"
        verbose_name_plural = "画像查询帐号列表"
        ordering = ['-id']

    def __unicode__(self):
        return '%s' % self.name


class Filter(models.Model):
    ip_list = models.TextField(max_length=65535, null=True, blank=True, verbose_name='客户白名单')
    api_list = models.TextField(max_length=65535, null=True, blank=True, verbose_name='apicode', help_text='格式：分析师账户:apicode1,apicode2;')

    class Meta:
        verbose_name = "过滤名单"
        verbose_name_plural = "过滤名单列表"

    def __unicode__(self):
        return '%s' % self.ip_list

