from django.conf.urls import patterns, url

from django.contrib.auth.decorators import login_required

from analyse.views import UpSourceFileView, SourceFileListView, MappingedFileView
from analyse.views import ReportFileView, FirstModifyPasswd, DeleteFileView
from analyse.views import create_user
from analyse.get_mail import deal_mail

urlpatterns = patterns('',

    url(r'^up_file/$', login_required(UpSourceFileView.as_view())),
    url(r'^first_modify_passwd/$', login_required(FirstModifyPasswd.as_view())),
    url(r'^source_files/$', login_required(SourceFileListView.as_view())),
    url(r'^mappinged_files/$', login_required(MappingedFileView.as_view())),
    url(r'^report_files/$', login_required(ReportFileView.as_view())),
    url(r'^delete_files/$', login_required(DeleteFileView.as_view())),
    url(r'^mail/$', deal_mail),
    url(r'^create_user/$', create_user)
)
