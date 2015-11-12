from django.test import TestCase
from django.utils import timezone
from django.contrib import auth
from django.test.client import Client
from django.test.utils import override_settings
import pytz
from mock import Mock

from django_adelaidex.lti.middleware import TimezoneMiddleware, CurrentCohortMiddleware


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


class CurrentCohortMiddlewareTest(TestCase):

    def setUp(self):
        super(CurrentCohortMiddlewareTest, self).setUp()
        self.ccm = CurrentCohortMiddleware()
        self.request = Mock()
        self.request.user = None
        self.response = Mock()
        self.cohort = Mock()

    def test_no_cohort(self):
        self.assertIsNone(self.ccm.process_request(self.request))
        self.assertIsNone(self.ccm.get_cohort())
        self.assertEquals(self.ccm.process_response(self.request, self.response), self.response)
        self.assertIsNone(self.ccm.get_cohort())

    def test_set_cohort(self):
        self.assertIsNone(self.ccm.process_request(self.request))
        self.assertIsNone(self.ccm.get_cohort())

        self.ccm.set_cohort(self.cohort)
        self.assertEquals(self.ccm.get_cohort(), self.cohort)

        self.assertEquals(self.ccm.process_response(self.request, self.response), self.response)
        self.assertIsNone(self.ccm.get_cohort())

    def test_del_cohort(self):
        self.assertIsNone(self.ccm.process_request(self.request))
        self.assertIsNone(self.ccm.get_cohort())

        self.ccm.set_cohort(self.cohort)
        self.assertEquals(self.ccm.get_cohort(), self.cohort)

        self.ccm.del_cohort()
        self.assertIsNone(self.ccm.get_cohort())

    def test_process_exception(self):
        self.assertIsNone(self.ccm.process_request(self.request))
        self.assertIsNone(self.ccm.get_cohort())

        self.ccm.set_cohort(self.cohort)
        self.assertEquals(self.ccm.get_cohort(), self.cohort)

        self.assertIsNone(self.ccm.process_exception(self.request))
        self.assertIsNone(self.ccm.get_cohort())

    @override_settings(ADELAIDEX_LTI={'LINK_TEXT': 'Hi there'})
    def test_cohort(self):
        self.assertIsNone(self.ccm.process_request(self.request))
        cohort = self.ccm.get_cohort()
        self.assertIsNotNone(cohort)
        self.assertEquals(cohort.title, 'Hi there')
        self.assertEquals(self.ccm.process_response(self.request, self.response), self.response)
        self.assertIsNone(self.ccm.get_cohort())
