from django.conf.urls import patterns, url

from django.contrib.auth.decorators import login_required

from analyse.manage import SourceFileView, UpSourceFileView, DelSourceFile
from analyse.manage import SourceFileHeadView, SaveSourceTagView, MappedFileListView

urlpatterns = patterns('',

    url(r'^source_file/$', login_required(SourceFileView.as_view())),
    url(r'^up_source_file/$', login_required(UpSourceFileView.as_view())),
    url(r'^del_source_file/$', login_required(DelSourceFile.as_view())),
    url(r'^sourcefile_head/$', login_required(SourceFileHeadView.as_view())),
    url(r'^save_source_tag/$', login_required(SaveSourceTagView.as_view())),
    url(r'^mapped_file_list/$', login_required(MappedFileListView.as_view())),
)
