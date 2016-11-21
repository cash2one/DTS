#!/usr/bin/python
# -*- coding: utf-8 -*-


from django.db import models
from django.dispatch import receiver
from account.models import Member

from datetime import datetime
import time
import os

#FileTypeCod:
    #SourceFile         :1
    #ThirdMappedFile    :2
    #MappingedFile      :3
    #ReportFile         :4

#def update_upload_filename():
    #pass

class SourceFile(models.Model):

    TO_INPUT = ''

    FILE_SOURCE_TYPES_OTHER = 'FILE_SOURCE_TYPES_OTHER'
    BANK_CREDIT_CARD = 'BANK_CREDIT_CARD'
    BANK_RETAIL = 'BANK_RETAIL'
    BANK_TO_PUBLIC = 'BANK_TO_PUBLIC'
    P2P_LOAN = 'P2P_LOAN'
    P2P_FINANCING = 'P2P_FINANCING'
    CONSUMER_FINANCE_COMPANY = 'CONSUMER_FINANCE_COMPANY'
    SMALL_LOAN_AGENCY= 'SMALL_LOAN_AGENCY'
    GUARANTEE = 'GUARANTEE'
    INSURANCE = 'INSURANCE'
    CAR_FINANCE = 'CAR_FINANCE'

    FILE_SOURCE_TYPES = (
        (TO_INPUT, '请选择'),
        (BANK_CREDIT_CARD, '银行信用卡'),
        (BANK_RETAIL, '银行零售'),
        (BANK_TO_PUBLIC, '银行对公'),
        (P2P_LOAN, 'P2P借贷'),
        (P2P_FINANCING, 'P2P理财'),
        (CONSUMER_FINANCE_COMPANY, '消费金融公司'),
        (SMALL_LOAN_AGENCY, '小贷机构'),
        (CAR_FINANCE, '汽车金融'),
        (GUARANTEE, '担保'),
        (INSURANCE, '保险'),
        (FILE_SOURCE_TYPES_OTHER, '其他'),
        )

    GUARANTEE_TYPE_OTHER = 'GUARANTEE_TYPE_OTHER'
    CREDIT_LOAD = 'CREDIT_LOAD'
    MORTGAGE_LOAN = 'MORTGAGE_LOAN'
    BOTH = 'BOTH'

    GUARANTEE_TYPE = (
        (TO_INPUT, '请选择'),
        (CREDIT_LOAD, '信用贷款'),
        (MORTGAGE_LOAN, '抵押贷款'),
        (BOTH, '兼有'),
        (GUARANTEE_TYPE_OTHER, '其他'),
        )

    USUAL = 'USUAL'
    WONER = 'WONER'
    COMPANY = 'COMPANY'
    OTHER_USER = 'OTHER_USER'
    USER_TYPE = (
        (TO_INPUT,'请选择'),
        (USUAL, '普通个人'),
        (WONER, '小业主'),
        (COMPANY, '企业'),
        (OTHER_USER, '其他'),
    )

    custom = models.ForeignKey(Member)
    can_down = models.ManyToManyField(Member, related_name='down_sourcefile')
    file_source_type = models.CharField(max_length=40, null=True, blank=True, choices=FILE_SOURCE_TYPES)
    guarantee_type = models.CharField(max_length=40, null=True, blank=True, choices=GUARANTEE_TYPE)
    user_type = models.CharField(max_length=40, null=True, blank=True, choices=USER_TYPE)
    filename = models.FileField(max_length=500, upload_to='source_file/%Y/%m')
    file_from = models.CharField(max_length=100)
    extra_info = models.CharField(max_length=300, null=True, blank=True)
    is_done = models.BooleanField(default=False)
    fields = models.CharField(max_length=1000, null=True, blank=True)
    skip_lines = models.IntegerField(max_length=4, null=True, blank=True)
    splitor = models.CharField(max_length=10, null=True, blank=True)
    is_checked = models.BooleanField(default=False)
    is_saved_db = models.BooleanField(default=False)
    total_lines = models.IntegerField(max_length=8, null=True, blank=True)
    file_size = models.IntegerField(max_length=4, null=True, blank=True)
    id_num = models.IntegerField(max_length=4, null=True, blank=True)
    is_sampling = models.BooleanField(default=False, verbose_name='是否已加入数据集市')
    is_delete = models.BooleanField(default=False, verbose_name="是否被删除")
    mail_num = models.IntegerField(max_length=4, null=True, blank=True)
    is_applied = models.BooleanField(default=False)
    applied_done_time = models.DateTimeField(null=True, blank=True)
    is_has_new = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    sampling_sort = models.CharField(max_length=20, null=True, blank=True, verbose_name='该客户在数据集市的文件个数')
    loan_amount = models.CharField(max_length=200, null=True, blank=True, verbose_name='贷款产品额度')
    loan_deadline = models.CharField(max_length=200, null=True, blank=True, verbose_name="贷款产品期限")
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '源文件'
        verbose_name_plural = '源文件列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.filename.name)

    def delete(self, *args, **kwargs):
        storage, path = self.filename.storage, self.filename.path
        super(SourceFile, self).delete(*args, **kwargs)
        if os.path.isfile(path):
            storage.delete(path)


class LineModel(models.Model):
    source_file = models.ForeignKey(SourceFile)
    line = models.CharField(max_length=800)
    openid = models.IntegerField(max_length=14)
    is_applyed = models.BooleanField(default=False)


class ThirdMappedFile(models.Model):
    MinHang = 'MinHang'
    Bank_Data = 'Bank_data'
    Account_Change = 'Account_change'
    Third_Company =  (
        (MinHang, '民航信息'),
        (Bank_Data, '银行卡数据'),
        (Account_Change, '帐户变动'),
    )
    source_file = models.ManyToManyField(SourceFile)
    can_down = models.ManyToManyField(Member, related_name='down_thirdfile')
    #child_file = models.ManyToManyField(MappingedFile)
    is_distribute = models.BooleanField(default=False)
    distribute_time = models.DateTimeField(null=True, blank=True)
    fields = models.CharField(max_length=500)
    skip_lines = models.IntegerField(max_length=4, null=True, blank=True)
    splitor = models.CharField(max_length=10)
    uploader = models.ForeignKey(Member)
    file = models.FileField(upload_to='thirdmapped_file/%Y/%m')
    file_desc = models.CharField(max_length=200, null=True, blank=True)
    file_size = models.IntegerField(max_length=4)
    file_from = models.CharField(max_length=100, null=True, choices=Third_Company)
    trans_status = models.CharField(max_length=20, null=True, blank=True)
    id_num = models.IntegerField(max_length=4, null=True, blank=True)
    cell_num = models.IntegerField(max_length=4, null=True, blank=True)
    mail_num = models.IntegerField(max_length=4, null=True, blank=True)

    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '第三方输出文件'
        verbose_name_plural = '第三方输出文件列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.file.name)

    def delete(self, *args, **kwargs):
        storage, path = self.file.storage, self.file.path
        super(ThirdMappedFile, self).delete(*args, **kwargs)
        if os.path.isfile(path):
            storage.delete(path)


class MappingedFile(models.Model):
    source_file = models.ForeignKey(SourceFile, null=True)
    can_down = models.ManyToManyField(Member, related_name='down_mappedfile')
    uploader = models.ForeignKey(Member, related_name='mappingedfile_uploaders', null=True, blank=True)
    customer = models.ForeignKey(Member, related_name='mappingedfile_customs', null=True, blank=True)
    parent_file = models.ForeignKey(ThirdMappedFile, null=True, blank=True)
    file = models.FileField(max_length=500, upload_to='mappinged_file/%Y/%m')
    file_size = models.IntegerField(max_length=4)
    file_from = models.CharField(max_length=300, null = True)
    is_cus_visible = models.BooleanField(default=True, verbose_name='客户是否可见')
    is_third_file = models.BooleanField(default=False, verbose_name='是否为第三方文件')
    is_csv = models.BooleanField(default=False, verbose_name='是否为csv文件')
    is_crypt = models.BooleanField(default=False)
    id_num = models.IntegerField(max_length=4, null=True, blank=True)
    cell_num = models.IntegerField(max_length=4, null=True, blank=True)
    mail_num = models.CharField(max_length=40, null=True, blank=True)
    password = models.CharField(max_length=50, null =True, blank=True)
    is_haina = models.BooleanField(default=False, verbose_name='是否画像接口匹配')
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mapping输出文件'
        verbose_name_plural = 'Mapping输出文件列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.file.name)

    def get_base_name(self):
        return os.path.basename(self.file.name)

    def delete(self, *args, **kwargs):
        storage, path = self.file.storage, self.file.path
        super(MappingedFile, self).delete(*args, **kwargs)
        if os.path.isfile(path):
            storage.delete(path)


class ReportFile(models.Model):
    report_file = models.FileField(upload_to='report_file/%Y/%m')
    can_down = models.ManyToManyField(Member, related_name='down_reportfile')
    mappinged_files = models.ManyToManyField(MappingedFile, null=True, blank=True)
    source_file = models.ForeignKey(SourceFile, null=True)
    uploader = models.ForeignKey(Member, related_name='reportfile_uploaders')
    customer = models.ForeignKey(Member, related_name='reportfile_customs', null=True, blank=True)
    file_desc = models.CharField(max_length=300, null=True, blank=True)
    file_size = models.IntegerField(max_length=4)
    passwd = models.CharField(max_length=10)

    create_time = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        storage, path = self.report_file.storage, self.report_file.path
        super(ReportFile, self).delete(*args, **kwargs)
        if os.path.isfile(path):
            storage.delete(path)

    class Meta:
        verbose_name = '报告文件'
        verbose_name_plural = '报告文件列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.report_file.name)


class LogInfo(models.Model):
    username = models.CharField(max_length=100, null=True, blank=True)
    ip = models.CharField(max_length=30, null=True, blank=True)
    filename = models.CharField(max_length=100, null=True, blank=True)
    query_interface = models.CharField(max_length=500, null=True, blank=True)
    num = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '日志'
        verbose_name_plural = '日志'
        ordering = ['-create_time']

    def __unicode__(self):
        return username


class ColletDate(models.Model):
    source_file = models.ForeignKey(SourceFile, null=True)
    user_type = models.CharField(max_length=20)
    guarantee_type = models.CharField(max_length=20) # 抵押类型
    file_source_type = models.CharField(max_length=20) # 公司类别
    analyst = models.CharField(max_length=200, default='')
    up_time = models.DateTimeField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    id_num = models.CharField(max_length=50, null=True, blank = True)
    cell = models.CharField(max_length=50, null=True, blank = True)
    email = models.CharField(max_length=50, null=True, blank = True)
    name = models.CharField(max_length=50, null=True, blank = True)
    home_addr = models.CharField(max_length=200, null=True, blank = True)
    home_tel = models.CharField(max_length=50, null=True, blank = True)
    biz_addr = models.CharField(max_length=200, null=True, blank = True)
    biz_tel = models.CharField(max_length=50, null=True, blank = True)
    other_addr = models.CharField(max_length=200, null=True, blank = True)
    bank_card1 = models.CharField(max_length=20, null=True, blank = True)
    bank_card2 = models.CharField(max_length=20, null=True, blank = True)
    flag1 = models.CharField(max_length=50, null=True, blank = True)
    flag2 = models.CharField(max_length=50, null=True, blank = True)
    flag = models.CharField(max_length=50, null=True, blank = True)
    def_days = models.IntegerField(max_length=10, null=True, blank = True)
    def_times = models.CharField(max_length=100, null=True, blank = True)
    amount = models.CharField(max_length=50, null=True, blank=True)
    notes = models.CharField(max_length=50, null=True, blank = True)
    apply_date = models.CharField(max_length=50, null=True, blank = True)
    observe_date = models.CharField(max_length=20, null=True, blank = True)
    apply_channel = models.CharField(max_length=50, null=True, blank = True)
    apply_id = models.CharField(max_length=100, null=True, blank = True)
    apply_addr = models.CharField(max_length=200, null=True, blank = True)
    apply_amount = models.IntegerField(max_length=24, null=True, blank = True)
    apply_product = models.CharField(max_length=20, null=True, blank = True)
    approval_status = models.CharField(max_length=50, null=True, blank = True)
    approval_date = models.CharField(max_length=20, null=True, blank = True)
    approval_amount = models.IntegerField(max_length=20, null=True, blank = True)
    device_type = models.CharField(max_length=50, null=True, blank = True)
    device_id = models.CharField(max_length=50, null=True, blank = True)
    apply_type = models.CharField(max_length=50, null=True, blank = True)
    type_vehicle_id = models.CharField(max_length=50, null=True, blank = True)
    af_swift_number = models.CharField(max_length=50, null=True, blank = True)
    custApiCode = models.CharField(max_length=50, null=True, blank = True)
    envent = models.CharField(max_length=50, null=True, blank = True)
    collateral = models.CharField(max_length=50, null=True, blank = True)
    loan_date = models.CharField(max_length=20, null=True, blank = True)
    loan_purpose = models.CharField(max_length=50, null=True, blank = True)
    loan_status = models.CharField(max_length=50, null=True, blank = True)
    repayment_periods = models.CharField(max_length=10, null=True, blank = True)
    age = models.CharField(max_length=10, null=True, blank = True)
    race = models.CharField(max_length=10, null=True, blank = True)
    gender = models.CharField(max_length=10, null=True, blank = True)
    birthday = models.CharField(max_length=20, null=True, blank = True)
    marriage = models.CharField(max_length=20, null=True, blank = True)
    edu = models.CharField(max_length=50, null=True, blank = True)
    wechat_city = models.CharField(max_length=50, null=True, blank = True)
    wechat_name = models.CharField(max_length=50, null=True, blank = True)
    wechat_province = models.CharField(max_length=50, null=True, blank = True)
    providentfund = models.CharField(max_length=20, null=True, blank = True)
    socialsecurity = models.CharField(max_length=50, null=True, blank = True)
    id_ps = models.CharField(max_length=50, null=True, blank = True)
    id_start = models.CharField(max_length=20, null=True, blank = True)
    id_end = models.CharField(max_length=20, null=True, blank = True)
    id_city = models.CharField(max_length=30, null=True, blank = True)
    id_type = models.CharField(max_length=30, null=True, blank = True)
    civic_addr = models.CharField(max_length=200, null=True, blank = True)
    civic_status = models.CharField(max_length=50, null=True, blank = True)
    postalcode = models.CharField(max_length=14, null=True, blank = True)
    city = models.CharField(max_length=50, null=True, blank = True)
    province = models.CharField(max_length=50, null=True, blank = True)
    contact_name_1 = models.CharField(max_length=50, null=True, blank = True)
    contact_relation_1 = models.CharField(max_length=50, null=True, blank = True)
    contact_cell_1 = models.CharField(max_length=50, null=True, blank = True)
    contact_name_2 = models.CharField(max_length=50, null=True, blank = True)
    contact_relation_2 = models.CharField(max_length=50, null=True, blank = True)
    contact_cell_2 = models.CharField(max_length=50, null=True, blank = True)
    contact_name_3 = models.CharField(max_length=50, null=True, blank = True)
    contact_relation_3 = models.CharField(max_length=50, null=True, blank = True)
    contact_cell_3 = models.CharField(max_length=50, null=True, blank = True)
    contact_name_4 = models.CharField(max_length=50, null=True, blank = True)
    contact_relation_4 = models.CharField(max_length=50, null=True, blank = True)
    contact_cell_4 = models.CharField(max_length=50, null=True, blank = True)
    contact_name_5 = models.CharField(max_length=50, null=True, blank = True)
    contact_relation_5 = models.CharField(max_length=50, null=True, blank = True)
    contact_cell_5 = models.CharField(max_length=50, null=True, blank = True)
    if_house = models.CharField(max_length=20, null=True, blank = True)
    if_vehicle = models.CharField(max_length=20, null=True, blank = True)
    housing_cate = models.CharField(max_length=50, null=True, blank = True)
    vehicle_id = models.CharField(max_length=50, null=True, blank = True)
    vehicle_type = models.CharField(max_length=50, null=True, blank = True)
    biz_name = models.CharField(max_length=50, null=True, blank = True)
    biz_size = models.CharField(max_length=50, null=True, blank = True)
    industry = models.CharField(max_length=50, null=True, blank = True)
    company_cate = models.CharField(max_length=50, null=True, blank = True)
    salary = models.CharField(max_length=50, null=True, blank = True)
    position = models.CharField(max_length=50, null=True, blank = True)
    working_period = models.CharField(max_length=50, null=True, blank = True)
    acc_open_date = models.CharField(max_length=20, null=True, blank = True)
    card_level = models.CharField(max_length=15, null=True, blank = True)
    branch = models.CharField(max_length=15, null=True, blank = True)
    currency = models.CharField(max_length=15, null=True, blank = True)
    ins_balance = models.CharField(max_length=24, null=True, blank = True)
    update_balance = models.CharField(max_length=24, null=True, blank = True)
    update_capital = models.CharField(max_length=24, null=True, blank = True)
    update_date = models.CharField(max_length=20, null=True, blank = True)
    update_interest = models.CharField(max_length=24, null=True, blank = True)
    update_overduepayment = models.CharField(max_length=24, null=True, blank = True)
    update_overlimitfee = models.CharField(max_length=24, null=True, blank = True)
    update_servicefee = models.CharField(max_length=24, null=True, blank = True)
    bill_day = models.CharField(max_length=20, null=True, blank = True)
    bill_post = models.CharField(max_length=20, null=True, blank = True)
    bill_addr = models.CharField(max_length=200, null=True, blank = True)
    ins_amount = models.CharField(max_length=24, null=True, blank = True)
    ins_date_claims = models.CharField(max_length=20, null=True, blank = True)
    ins_firstlogindate = models.CharField(max_length=20, null=True, blank = True)
    ins_newvehicleprice = models.CharField(max_length=24, null=True, blank = True)
    ins_period = models.CharField(max_length=10, null=True, blank = True)
    ins_yearly_claims_num = models.CharField(max_length=10, null=True, blank = True)
    imei = models.CharField(max_length=50, null=True, blank = True)
    imsi = models.CharField(max_length=50, null=True, blank = True)
    mobil_type = models.CharField(max_length=50, null=True, blank = True)
    gid = models.CharField(max_length=50, null=True, blank = True)
    other_var1 = models.CharField(max_length=50, null=True, blank = True)
    var_exp1 = models.CharField(max_length=200, null=True, blank = True)
    other_var2 = models.CharField(max_length=50, null=True, blank = True)
    var_exp2 = models.CharField(max_length=200, null=True, blank = True)
    other_var3 = models.CharField(max_length=50, null=True, blank = True)
    var_exp3 = models.CharField(max_length=200, null=True, blank = True)
    other_var4 = models.CharField(max_length=50, null=True, blank = True)
    var_exp4 = models.CharField(max_length=200, null=True, blank = True)
    other_var5 = models.CharField(max_length=50, null=True, blank = True)
    var_exp5 = models.CharField(max_length=200, null=True, blank = True)

    def save(self, *args, **kwargs):
        super (ColletDate, self).save (*args, **kwargs)

    def __unicode__(self):
        return '%s' % str(self.source_file)


class Coder(models.Model):
    member = models.ForeignKey(Member)
    code = models.CharField(max_length=300)
    create_time = models.DateTimeField(auto_now_add=True)
    is_outdate = models.BooleanField(default=False)
    to_user = models.BooleanField(default=False)
    permission = models.CharField(max_length=500)
    extra_info = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        verbose_name = '授权码'
        verbose_name_plural = "授权码列表"
        ordering = ["-create_time"]

    def __unicode__(self):
        return u'%s' % str(self.code)


class PhoneFile(models.Model):
    member = models.ForeignKey(Member)
    filename = models.FileField(upload_to='phone_file/%Y/%m')
    file_from = models.CharField(max_length=100)
    extra_info = models.CharField(max_length=300, null=True, blank=True)
    total_lines = models.IntegerField(max_length=8, null=True, blank=True)     #upfailphonenumber
    file_size = models.IntegerField(max_length=4, null=True, blank=True)
    is_bingo = models.BooleanField(default=False)
    applied_done_time = models.DateTimeField(null=True, blank=True)
    task_id = models.IntegerField(max_length=8, null=True, blank=True)

    create_time = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = '号码文件'
        verbose_name_plural = '号码文件列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.filename.name)


class Meal(models.Model):
    name = models.CharField(max_length=100)
    chinese_name = models.CharField(max_length=120)
    head_status = models.BooleanField(default=False, verbose_name='是否有表头')
    interface = models.CharField(max_length=50)
    create_time = models.DateTimeField(auto_now_add=True)
    max_map = models.IntegerField(max_length=10, null=True, blank =True)

    class Meta:
        verbose_name = '套餐名称'
        verbose_name_plural = '套餐名称列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.name)


class MealHead(models.Model):
    meal = models.ForeignKey(Meal)
    name = models.CharField(max_length=100)
    head = models.CharField(max_length=100)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '套餐表头对照'
        verbose_name_plural = '套餐表头对照列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.name)


class MealSort(models.Model):
    name = models.CharField(max_length=100)
    sort = models.CharField(max_length=500)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '套餐顺序对照'
        verbose_name_plural = '套餐套餐顺序列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.name)


class Interface(models.Model):
    name = models.CharField(max_length=100)
    chinese_name = models.CharField(max_length=120)
    create_time = models.DateTimeField(auto_now_add=True)
    thread_num = models.IntegerField(default=10, verbose_name='并发数')
    max_map = models.IntegerField(default=0, verbose_name='最大匹配量')

    class Meta:
        verbose_name = '接口名称'
        verbose_name_plural = '接口名称列表'
        ordering = ['-create_time']

    def __unicode__(self):
        return u'%s' % os.path.basename(self.name)
