from django.conf.urls import patterns, url
from analyse.single import SingleMapView, CreateCustomView
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('',

    url(r'single_map/$', login_required(SingleMapView.as_view())),
    url(r'create_custom/$', login_required(CreateCustomView.as_view())),
)
