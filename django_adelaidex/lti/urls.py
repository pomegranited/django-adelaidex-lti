from django.conf.urls import patterns, url
from django_adelaidex.lti import views
from django.conf import settings

urlpatterns = patterns('',
    url(r'^profile', views.UserProfileView.as_view(),
        name='lti-user-profile'),
    url(r'^$', views.LTIEntryView.as_view(),
        name='lti-entry'),
    url(r'^403', views.LTIPermissionDeniedView.as_view(),
        name='lti-403'),
    url(r'^login', views.LTILoginRedirectView.as_view(),
        name='lti-login'),
    url(r'^enrol', views.LTIEnrolRedirectView.as_view(),
        name='lti-enrol'),
    url(r'^inactive', views.LTIInactiveView.as_view(),
        name='lti-inactive'),
)
