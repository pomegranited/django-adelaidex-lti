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


class CurrentCohortMiddleware(object):
    '''Cache Cohort.objects.get_current() for the current thread,
       so it needn't be calculated more than once.
       
       Modeled on django-cuser: https://github.com/Alir3z4/django-cuser/
    '''

    __cohorts = {}

    def process_request(self, request):
        '''Store current cohort'''
        cohort = Cohort.objects.get_current(request)
        self.__class__.set_cohort(cohort)

    def process_response(self, request, response):
        '''Delete current cohort'''
        self.__class__.del_cohort()
        return response

    def process_exception(self, request, *args, **kwargs):
        '''Delete current cohort'''
        self.__class__.del_cohort()

    @classmethod
    def get_cohort(cls, default=None):
        '''Retrieve current cohort'''
        return cls.__cohorts.get(threading.current_thread(), default)

    @classmethod
    def set_cohort(cls, cohort):
        '''Store current cohort'''
        cls.__cohorts[threading.current_thread()] = cohort

    @classmethod
    def del_cohort(cls):
        '''Delete current cohort'''
        cls.__cohorts.pop(threading.current_thread(), None)
