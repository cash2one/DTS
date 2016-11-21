from django.conf.urls import patterns, url

from django.contrib.auth.decorators import login_required

from analyse.datatrans import SourceFilesView, SourceFileHeadView
from analyse.datatrans import PickFileView, ThirdMapedFileView, UpMappedFileView
from analyse.datatrans import SaveTagView, ListSourceFileView, ThirdMappedHeadView
from analyse.datatrans import StartDistributeView, ChildFilesView, DelChildView
from analyse.datatrans import SaveSourceTagView

urlpatterns = patterns('',

    url(r'^cus_files/$', login_required(SourceFilesView.as_view())),
    url(r'sourcefile_head/$', login_required(SourceFileHeadView.as_view())),
    url(r'thirdmapped_head/$', login_required(ThirdMappedHeadView.as_view())),
    url(r'pick_file/$', login_required(PickFileView.as_view())),
    url(r'third_mapedfile/$', login_required(ThirdMapedFileView.as_view())),
    url(r'up_mappedfile/$', login_required(UpMappedFileView.as_view())),
    url(r'save_tag/$', login_required(SaveTagView.as_view())),
    url(r'get_sourcefiles/$', login_required(ListSourceFileView.as_view())),
    url(r'start_distribute/$', login_required(StartDistributeView.as_view())),
    url(r'child_files/$', login_required(ChildFilesView.as_view())),
    url(r'del_child/$', login_required(DelChildView.as_view())),
    url(r'save_source_tag/$', login_required(SaveSourceTagView.as_view())),
)
