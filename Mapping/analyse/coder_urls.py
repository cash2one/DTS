from django.conf.urls import patterns, url

from django.contrib.auth.decorators import login_required

from analyse.coder import CodeListView,CreateCode,DeleteCode,DeleteThisCode,ToUser,DataCodeList,MarkCodeList,CollCodeList

urlpatterns = patterns('',
    url(r'^code_list/$', login_required(CodeListView.as_view())),
    url(r'^create_code/$', login_required(CreateCode.as_view())),
    url(r'^delete_all/$', login_required(DeleteCode.as_view())),
    url(r'^delete_this/$', login_required(DeleteThisCode.as_view())),
    url(r'^to_user/$', login_required(ToUser.as_view())),
    url(r'^datacode_list/$', login_required(DataCodeList.as_view())),
    url(r'^markcode_list/$', login_required(MarkCodeList.as_view())),
    url(r'^collcode_list/$', login_required(CollCodeList.as_view())),
)
