from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',
    url(r'custom/', include('analyse.custom_urls')),
    url(r'analyst/', include('analyse.analyst_urls')),
    url(r'datatrans/', include('analyse.datatrans_urls')),
    url(r'manage/', include('analyse.manage_urls')),
    url(r'single/',include('analyse.single_urls')),
    url(r'phone/',include('analyse.phone_urls')),
    url(r'meal/', include('analyse.meal_urls')),
    url(r'coder/', include('analyse.coder_urls')),
)
