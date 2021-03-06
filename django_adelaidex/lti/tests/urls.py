from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.core.urlresolvers import reverse_lazy

from django_adelaidex.lti.views import LTIPermissionDeniedView
from django_adelaidex.lti.tests.views import TestDisqusSSOView, TestOauthPostView

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^$', LTIPermissionDeniedView.as_view(), name='home'),
    url(r'^lti/', include('django_adelaidex.lti.urls')),
    url(r'^admin/', include(admin.site.urls)),

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
        kwargs={'template_name': 'login.html'},
        name='auth-login'),
    url(r'^logout/$', auth_views.logout,
        kwargs={'next_page': reverse_lazy('home')},
        name='logout'),

    # Used by unit tests
    url(r'^test/disqus_sso', TestDisqusSSOView.as_view(),
        name='test-disqus-sso'),
]

# Decide whether to use auth login or django_adelaidex.lti as the 'login' url
if getattr(settings, 'ADELAIDEX_LTI', {}).get('LOGIN_URL'):
    urlpatterns.append(url(r'^login/$',
                       LTIPermissionDeniedView.as_view(),
                       name='login'))
else:
    urlpatterns.append(url(r'^login/$',
                       auth_views.login,
                       kwargs={'template_name': 'login.html'},
                       name='login'))
