from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth.decorators import login_required

from account.views import IndexView
from .views import CheckDownloads, ManageDownView, CreateValid

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Mapping.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', login_required(IndexView.as_view())),
    url(r'^accounts/', include('account.urls')),
    url(r'^als/', include('analyse.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^validate/', CreateValid.as_view()),
    url(r'^downloads/(?P<ft>\d+)/(?P<fid>\d+)/$', login_required(CheckDownloads.as_view())),
    url(r'^manage_down/(?P<ft>\d+)/(?P<fid>\d+)/$', login_required(ManageDownView.as_view())),
)
#)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
