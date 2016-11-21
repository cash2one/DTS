from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from analyse.analy import CusFilesView, SourceFileHeadView, StartMappingView
from analyse.analy import UpReportView, CusMappingedFilesView, CusReportFilesView
from analyse.analy import MappingProgressView, DownSourceView, MyCus
from analyse.analy import SendCusMappingFileView, GetMapFilePasswd, LetCustomGetView, SendMailToCoder
from analyse.analy import SelectModelView, SamplingView, CollectDateView
from analyse.analy import make_file, sampling_condition, delete_report, loginfo
from analyse.analy import OperatorModelView, GetCustomNumView, GetFileNumView
from analyse.analy import BcjqModelView, CompanyModelView, LossModelView, ShutDown, choice


urlpatterns = patterns('',
    url(r'cus_files/$', login_required(CusFilesView.as_view())),
    url(r'my_cus/$', login_required(MyCus.as_view())),
    url(r'cus_mappinged_files/$', login_required(CusMappingedFilesView.as_view())),
    url(r'sourcefile_head/$', login_required(SourceFileHeadView.as_view())),
    url(r'start_mapping/$', login_required(StartMappingView.as_view())),
    url(r'up_report/$', login_required(UpReportView.as_view())),
    url(r'cus_report_files/$', login_required(CusReportFilesView.as_view())),
    url(r'mapping_progress/$', login_required(MappingProgressView.as_view())),
    url(r'down_sourcefile/$', login_required(DownSourceView.as_view())),
    url(r'send_email/$', login_required(SendCusMappingFileView.as_view())),
    url(r'mail_to_coder/$', login_required(SendMailToCoder.as_view())),
    url(r'get_mappingfile_passwd/$', login_required(GetMapFilePasswd.as_view())),
    url(r'let_cus_get/$',login_required(LetCustomGetView.as_view())),
    url(r'get_select_model/$',login_required(SelectModelView.as_view())),
    url(r'to_collect/$',login_required(CollectDateView.as_view())),
    url(r'sampling/$', login_required(SamplingView.as_view())),
    url(r'make_file/$', make_file),
    url(r'loginfo/$', loginfo),
    url(r'sampling_condition/$', sampling_condition),
    url(r'operator_model/$', login_required(OperatorModelView.as_view())),
    url(r'delete_report/$', delete_report),
    url(r'get_custom_num/$', login_required(GetCustomNumView.as_view())),
    url(r'get_file_num/$', login_required(GetFileNumView.as_view())),
    url(r'bcjq_model/$', login_required(BcjqModelView.as_view())),
    url(r'loss_model/$', login_required(LossModelView.as_view())),
    url(r'qy_model/$', login_required(CompanyModelView.as_view())),
    url(r'shutdown/$', login_required(ShutDown.as_view())),    
    url(r'choice/$', choice),    

)
