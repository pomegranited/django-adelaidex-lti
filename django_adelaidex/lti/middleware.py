# https://docs.djangoproject.com/en/1.7/topics/i18n/timezones/#selecting-the-current-time-zone
import pytz
import threading
from django.utils import timezone
from django_adelaidex.lti.models import Cohort

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


class AnonymousCohortMiddleware(object):
    '''Give anonymous users the default cohort, 
       to avoid fetching it many times from the database.'''

    def process_request(self, request):
        user = request.user
        if user and not user.is_authenticated():
            '''Store current, default cohort against the user'''
            cohort = Cohort.objects.get_current(user)
            setattr(user, 'cohort', cohort)
