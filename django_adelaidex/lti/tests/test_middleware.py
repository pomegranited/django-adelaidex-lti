from django.test import TestCase
from django.utils import timezone
from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from django.test.client import Client
from django.test.utils import override_settings
import pytz
from mock import Mock

from django_adelaidex.lti.middleware import TimezoneMiddleware, AnonymousCohortMiddleware


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


class AnonymousCohortMiddlewareTest(TestCase):

    def setUp(self):
        super(AnonymousCohortMiddlewareTest, self).setUp()
        self.acm = AnonymousCohortMiddleware()
        self.request = Mock()

    def test_anonymous_no_cohort(self):
        self.request.user = AnonymousUser()
        self.assertFalse(hasattr(self.request.user, 'cohort'))
        self.assertIsNone(self.acm.process_request(self.request))
        self.assertTrue(hasattr(self.request.user, 'cohort'))
        self.assertIsNone(self.request.user.cohort)

    @override_settings(ADELAIDEX_LTI={'LINK_TEXT': 'Hi there'})
    def test_anonymous_default_cohort(self):
        self.request.user = AnonymousUser()
        self.assertFalse(hasattr(self.request.user, 'cohort'))
        self.assertIsNone(self.acm.process_request(self.request))
        self.assertTrue(hasattr(self.request.user, 'cohort'))
        self.assertIsNotNone(self.request.user.cohort)
        self.assertEquals(self.request.user.cohort.title, 'Hi there')

    def test_authenticated_no_cohort(self):
        self.request.user = AnonymousUser()
        self.request.user.is_authenticated = lambda : True
        setattr(self.request.user, 'cohort', None)
        self.assertTrue(hasattr(self.request.user, 'cohort'))
        self.assertIsNone(self.acm.process_request(self.request))
        self.assertIsNone(self.request.user.cohort)

    def test_authenticated_own_cohort(self):
        self.request.user = AnonymousUser()
        self.request.user.is_authenticated = lambda : True
        own_cohort = Mock()
        setattr(self.request.user, 'cohort', own_cohort)
        self.assertTrue(hasattr(self.request.user, 'cohort'))
        self.assertIsNone(self.acm.process_request(self.request))
        self.assertIsNotNone(self.request.user.cohort)
        self.assertEquals(self.request.user.cohort, own_cohort)

    @override_settings(ADELAIDEX_LTI={'LINK_TEXT': 'Hi there'})
    def test_authenticated_default_cohort(self):
        self.request.user = AnonymousUser()
        self.request.user.is_authenticated = lambda : True
        setattr(self.request.user, 'cohort', None)
        self.assertTrue(hasattr(self.request.user, 'cohort'))
        self.assertIsNone(self.acm.process_request(self.request))
        self.assertIsNone(self.request.user.cohort)

    @override_settings(ADELAIDEX_LTI={'LINK_TEXT': 'Hi there'})
    def test_authenticated_default_own_cohort(self):
        self.request.user = AnonymousUser()
        self.request.user.is_authenticated = lambda : True
        own_cohort = Mock()
        setattr(self.request.user, 'cohort', own_cohort)
        self.assertTrue(hasattr(self.request.user, 'cohort'))
        self.assertIsNone(self.acm.process_request(self.request))
        self.assertIsNotNone(self.request.user.cohort)
        self.assertEquals(self.request.user.cohort, own_cohort)

