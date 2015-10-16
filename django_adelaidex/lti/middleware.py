# https://docs.djangoproject.com/en/1.7/topics/i18n/timezones/#selecting-the-current-time-zone
import pytz
from django.utils import timezone
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from django_adelaidex.lti.models import Cohort


class CohortLTIOAuthMiddleware(object):
    '''Load the Cohorts from the database, and merge their oauth credentials
       with any existing settings.LTI_OAUTH_CREDENTIALS.

       Will not override an existing settings.LTI_OAUTH_CREDENTIALS key:secret.
       Changes to the Cohort instances will be reflected in the next request.
        
       To be useful, CohortLTIOAuthMiddleware must be included in
       settings.MIDDLEWARE_CLASSES prior to
       django_auth_lti.middleware.LTIAuthMiddleware.
    '''
    def process_request(self, request):
        oauth_creds = getattr(settings, 'LTI_OAUTH_CREDENTIALS', None)
        if not oauth_creds:
            oauth_creds = {}

        cohorts = Cohort.objects.all()
        for cohort in cohorts:
            # Take care not to override explicit oauth settings
            if not cohort.oauth_key in oauth_creds:
                oauth_creds[cohort.oauth_key] = cohort.oauth_secret

        setattr(settings, 'LTI_OAUTH_CREDENTIALS', oauth_creds)


class TimezoneMiddleware(object):
    '''Use the currently-authenticated user's configured timezone
       as the current timezone to display all dates/times.
      
       If no timezone configured, use the default.'''
    def process_request(self, request):
        timezone.deactivate()
        if request.user and request.user.is_authenticated():
            tzname = request.user.time_zone
            if tzname:
                timezone.activate(pytz.timezone(tzname))
        return None
