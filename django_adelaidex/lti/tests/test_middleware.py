from django.test import TestCase
from django.utils import timezone
from django.contrib import auth
from django.test.client import Client
from django.conf import settings
from django.test.utils import override_settings
import pytz
from mock import Mock

from django_adelaidex.lti.middleware import TimezoneMiddleware, CohortLTIOAuthMiddleware
from django_adelaidex.lti.models import Cohort
from django_adelaidex.util.test import TestOverrideSettings


class CohortLTIOauthCredentialsTest(TestOverrideSettings, TestCase):

    def setUp(self):
        super(CohortLTIOauthCredentialsTest, self).setUp()
        self.cm = CohortLTIOAuthMiddleware()
        self.request = Mock()
        self.request.user = None
        # reset any credentials changes from previous tests
        setattr(settings, 'LTI_OAUTH_CREDENTIALS', None)
        setattr(settings, '_LTI_COHORTS', None)

    def test_no_oauth_credentials(self):
        '''Ensure that the credentials gets initialised by default to an empty hash.'''
        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), None)
        self.assertEqual(self.cm.process_request(self.request), None)
        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), {})

    def test_add_cohort(self):
        '''Ensure we can set the credentials from cohorts in the database'''
        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), None)

        cohort = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
        )

        self.assertEqual(self.cm.process_request(self.request), None)
        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), 
                         {'mykey': 'mysecret'})

    def test_two_cohorts(self):
        '''Ensure we can have more than one set of credentials.'''
        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), None)

        cohort1 = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
        )
        cohort2 = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey2',
            oauth_secret='mysecret2',
            login_url='http://google.com',
        )

        self.assertEqual(self.cm.process_request(self.request), None)
        oauth_creds = getattr(settings, 'LTI_OAUTH_CREDENTIALS', {})
        self.assertEqual(oauth_creds.get('mykey'), 'mysecret')
        self.assertEqual(oauth_creds.get('mykey2'), 'mysecret2')

    @override_settings(LTI_OAUTH_CREDENTIALS = {
        'mykey': 'anothersecret'
    })
    def test_settings(self):
        '''Ensure it works with base settings.'''

        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), 
            {'mykey': 'anothersecret'})
        self.assertEqual(self.cm.process_request(self.request), None)
        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), 
            {'mykey': 'anothersecret'})

    @override_settings(LTI_OAUTH_CREDENTIALS = {
        'mykey': 'anothersecret'
    })
    def test_no_override(self):
        '''Ensure that we don't override an explicitly set secret.'''
        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), 
            {'mykey': 'anothersecret'})
        self.assertEqual(self.cm.process_request(self.request), None)
        self.assertEqual(getattr(settings, 'LTI_OAUTH_CREDENTIALS', None), 
            {'mykey': 'anothersecret'})

        cohort = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
        )
        cohort2 = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey2',
            oauth_secret='mysecret2',
            login_url='http://google.com',
        )

        self.assertEqual(self.cm.process_request(self.request), None)
        oauth_creds = getattr(settings, 'LTI_OAUTH_CREDENTIALS', {})
        self.assertEqual(oauth_creds.get('mykey'), 'anothersecret')
        self.assertEqual(oauth_creds.get('mykey2'), 'mysecret2')


class TimezoneMiddlewareTest(TestCase):

    def setUp(self):
        super(TimezoneMiddlewareTest, self).setUp()
        self.tzm = TimezoneMiddleware()
        self.request = Mock()
        self.request.user = None
        self.UTC = timezone.get_default_timezone()

        # reset to default timezone
        timezone.deactivate()

    def test_no_user_process_request(self):
        self.assertEqual(self.request.user, None)
        self.assertEqual(timezone.get_current_timezone(), self.UTC)
        self.assertEqual(self.tzm.process_request(self.request), None)
        self.assertEqual(timezone.get_current_timezone(), self.UTC)

    def test_anon_process_request(self):
        self.request.user = auth.get_user(Client())
        self.assertTrue(self.request.user.is_anonymous())
        self.assertFalse(self.request.user.is_authenticated())
        self.assertEqual(timezone.get_current_timezone(), self.UTC)

        self.assertEqual(self.tzm.process_request(self.request), None)
        self.assertEqual(timezone.get_current_timezone(), self.UTC)

    def test_no_tz_process_request(self):
        self.request.user = auth.get_user_model().objects.create(username='new_user')
        self.assertFalse(self.request.user.is_anonymous())
        self.assertTrue(self.request.user.is_authenticated())
        self.assertEqual(self.request.user.time_zone, None)

        self.assertEqual(timezone.get_current_timezone(), self.UTC)
        self.assertEqual(self.tzm.process_request(self.request), None)
        self.assertEqual(timezone.get_current_timezone(), self.UTC)

    def test_custom_tz_process_request(self):
        self.request.user = auth.get_user_model().objects.create(username='new_user', time_zone='Australia/Adelaide')
        self.assertFalse(self.request.user.is_anonymous())
        self.assertTrue(self.request.user.is_authenticated())
        self.assertEqual(timezone.get_current_timezone(), self.UTC)

        self.assertEqual(self.tzm.process_request(self.request), None)
        self.assertEqual(timezone.get_current_timezone(), pytz.timezone(self.request.user.time_zone))


