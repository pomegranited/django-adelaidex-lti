from django.conf.urls import patterns, url, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.core.urlresolvers import reverse_lazy

from django_adelaidex.lti.views import LTIPermissionDeniedView
from django_adelaidex.lti.tests.views import TestDisqusSSOView, TestOauthPostView
from django_adelaidex.lti.models import Cohort

from django.contrib import admin
admin.autodiscover()

default_cohort = Cohort.objects.get_current()

urlpatterns = patterns('',
    url(r'^/?$', LTIPermissionDeniedView.as_view(), name='home'),
    url(r'^lti/', include('django_adelaidex.lti.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # Decide whether to use auth login or django_adelaidex.lti as the 'login' url
    url(r'^login/$',
        LTIPermissionDeniedView.as_view(),
        name='login') if default_cohort and default_cohort.login_url
    else
    url(r'^login/$', auth_views.login,
        {'template_name': 'login.html'},
        name='login'),

    # Mock OAUTH post params
    url(r'^oauth/$', TestOauthPostView.as_view(),
        name='test_oauth'),
    url(r'^oauth/u/(?P<uid>[^/]+)/$', TestOauthPostView.as_view(),
        name='test_oauth_user'),
    url(r'^oauth/k/(?P<key>[^/]+)/$', TestOauthPostView.as_view(),
        name='test_oauth_key'),
    url(r'^oauth/u/(?P<uid>[^/]+)/(?P<key>[^/]+)$', TestOauthPostView.as_view(),
        name='test_oauth_user_key'),

    url(r'^auth/login/$', auth_views.login,
        {'template_name': 'login.html'},
        name='auth-login'),
    url(r'^logout/$', auth_views.logout,
        {'next_page': reverse_lazy('home')},
        name='logout'),

    # Used by unit tests
    url(r'^test/disqus_sso', TestDisqusSSOView.as_view(),
        name='test-disqus-sso'),
)
