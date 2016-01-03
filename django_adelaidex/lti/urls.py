from django.conf.urls import url
from django_adelaidex.lti import views
from django.conf import settings

urlpatterns = [
    url(r'^profile', views.UserProfileView.as_view(),
        name='lti-user-profile'),
    url(r'^$', views.LTIEntryView.as_view(),
        name='lti-entry'),
    url(r'^403', views.LTIPermissionDeniedView.as_view(),
        name='lti-403'),
    url(r'^login', views.LTIRedirectView.as_view(),
        kwargs={'redirect_url': getattr(settings, 'ADELAIDEX_LTI', {}).get('LOGIN_URL')},
        name='lti-login'),
    url(r'^enrol', views.LTIRedirectView.as_view(),
        kwargs={'redirect_url': getattr(settings, 'ADELAIDEX_LTI', {}).get('ENROL_URL')},
        name='lti-enrol'),
    url(r'^inactive', views.LTIInactiveView.as_view(),
        name='lti-inactive'),
]
