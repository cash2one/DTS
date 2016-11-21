from django.conf.urls import patterns, url

from django.contrib.auth.decorators import login_required

from account.views import LoginView, LogoutView, PasswdView, VerifyView

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Mapping.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^login/$', LoginView.as_view()),
    url(r'^logout/$', LogoutView.as_view()),
    url(r'^re_passwd/$', PasswdView.as_view()),
    url(r'^verify/$', VerifyView.as_view())
)
