from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from analyse.phone import UpFileView, FileListView, NumInSqlView, GetResultView

urlpatterns = patterns('',
    url(r'^file_list/$', login_required(FileListView.as_view())),
    url(r'^up_file/$', login_required(UpFileView.as_view())),
    url(r'^put_in_db/$', login_required(NumInSqlView.as_view())),
    url(r'^get_result/$', login_required(GetResultView.as_view())),
)
