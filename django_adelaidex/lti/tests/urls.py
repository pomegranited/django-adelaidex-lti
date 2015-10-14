from django.conf.urls import patterns, url, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.core.urlresolvers import reverse_lazy

from django_adelaidex.lti.views import LTIPermissionDeniedView
from django_adelaidex.lti.tests.views import TestDisqusSSOView


urlpatterns = patterns('',
    url(r'^/?$', LTIPermissionDeniedView.as_view(), name='home'),
    url(r'^lti/', include('django_adelaidex.lti.urls')),

    # Decide whether to use auth login or django_adelaidex.lti as the 'login' url
    url(r'^login/$',
        LTIPermissionDeniedView.as_view(),
        name='login') if getattr(settings, 'ADELAIDEX_LTI', {}).get('LOGIN_URL') 
    else
    url(r'^login/$', auth_views.login,
        {'template_name': 'login.html'},
        name='login'),

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
