from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
import sys
from urlparse import urlparse

from django_adelaidex.test import UserSetUp, InactiveUserSetUp, TestOverrideSettings
from artwork.models import Artwork


class LTIEntryViewTest(UserSetUp, TestCase):
    """LTI Login view tests."""

    def test_public_get(self):

        '''Unauthenticated GET users get redirected to basic login page'''
        client = Client()
        lti_login_path = reverse('lti-entry')
        response = client.get(lti_login_path)

        login_path = '%s?next=%s' % (reverse('login'), lti_login_path)
        self.assertRedirects(response, login_path, status_code=302, target_status_code=200)

    def test_auth_get(self):

        '''Authenticated GET users are shown the lti-entry page'''
        client = Client()
        lti_login_path = reverse('lti-entry')
        response = self.assertLogin(client, lti_login_path)

        self.assertEqual(self.user, response.context['user'])
        self.assertEqual(2, len(response.context['form'].fields))
        self.assertIn('first_name', response.context['form'].fields)
        self.assertIn('time_zone', response.context['form'].fields)
        self.assertEqual(self.user, response.context['form'].instance)

    def test_auth_post(self):

        '''Authenticated POST users, without a nickname set, are shown the lti-entry page'''
        client = Client()
        self.assertLogin(client, reverse('home'))

        lti_login_path = reverse('lti-entry')
        response = client.post(lti_login_path)

        self.assertEqual(self.user, response.context['user'])
        self.assertEqual(2, len(response.context['form'].fields))
        self.assertIn('first_name', response.context['form'].fields)
        self.assertIn('time_zone', response.context['form'].fields)
        self.assertEqual(self.user, response.context['form'].instance)

    def test_nickname_post(self):

        '''Authenticated POST users, with a nickname set, are redirected to home'''
        self.user.first_name = "MyNickname"
        self.user.save()

        client = Client()
        home_path = reverse('home')
        self.assertLogin(client, home_path)

        lti_login_path = reverse('lti-entry')
        response = client.post(lti_login_path)
        self.assertRedirects(response, home_path, status_code=302, target_status_code=200)

    def test_nickname_post_custom_next(self):

        '''Authenticated POST users, with a nickname set, are redirected to the
           path resolved by the custom_next post parameter.'''
        self.user.first_name = "MyNickname"
        self.user.save()

        client = Client()
        home_path = reverse('home')
        self.assertLogin(client, reverse('home'))

        lti_login_path = reverse('lti-entry')
        list_path = reverse('exhibition-list')
        response = client.post(lti_login_path, {'custom_next': list_path})
        self.assertRedirects(response, list_path, status_code=302, target_status_code=200)

    def test_set_nickname(self):

        '''Update the authenticated user's nickname from the LTI login page'''
        self.user.first_name = "MyNickname"
        self.user.save()

        client = Client()
        home_path = reverse('home')
        self.assertLogin(client, home_path)

        lti_login_path = reverse('lti-entry')
        form_data = {'first_name': 'AnotherNickname'}
        response = client.post(lti_login_path, form_data)

        self.assertRedirects(response, home_path, status_code=302, target_status_code=200)

        # Ensure the nickname was updated
        user = get_user_model().objects.get(username=self.user.username)
        self.assertEqual(user.first_name, form_data['first_name'])

    def test_set_empty_nickname(self):

        '''Non-empty nickname is required.'''
        client = Client()
        home_path = reverse('home')
        self.assertLogin(client, home_path)

        lti_login_path = reverse('lti-entry')

        form_data = {'first_name': ''}
        response = client.post(lti_login_path, form_data)

        self.assertEqual(2, len(response.context['form'].fields))
        self.assertEquals(u'This field is required.', response.context['form']['first_name'].errors[0])
        self.assertEquals([], response.context['form']['time_zone'].errors)

        form_data = {'first_name': '   '}
        response = client.post(lti_login_path, form_data)

        self.assertEqual(2, len(response.context['form'].fields))
        self.assertEquals(u'Please enter a valid nickname.', response.context['form']['first_name'].errors[0])
        self.assertEquals([], response.context['form']['time_zone'].errors)

    def test_set_is_staff(self):

        '''Update the authenticated user's is_staff setting via the LTI POST parameters'''
        self.assertFalse(self.user.is_staff)

        client = Client()
        self.assertLogin(client, reverse('home'))

        # Fake the LTI session roles
        session = client.session
        session['LTI_LAUNCH'] = {
            'roles': ['Instructor',]
        }
        session.save()

        post_data = {
            'first_name': 'NickName',
        }
        lti_login_path = reverse('lti-entry')
        response = client.post(lti_login_path, post_data)

        # Ensure the updated user is a staff member
        user = get_user_model().objects.get(username=self.user.username)
        self.assertTrue(user.is_staff)

    def test_set_is_student(self):

        '''Ensure the authenticated user remains non-staff even with LTI_LAUNCH roles'''
        self.assertFalse(self.user.is_staff)

        client = Client()
        self.assertLogin(client, reverse('home'))

        # Fake the LTI session roles
        session = client.session
        session['LTI_LAUNCH'] = {
            'roles': ['Student',]
        }
        session.save()

        post_data = {
            'first_name': 'NickName',
        }
        lti_login_path = reverse('lti-entry')
        response = client.post(lti_login_path, post_data)

        # Ensure the updated user is still a student
        user = get_user_model().objects.get(username=self.user.username)
        self.assertFalse(user.is_staff)


class LTIInactiveEntryViewTest(InactiveUserSetUp, TestCase):
    """LTI Login view tests for inactive user"""

    def test_inactive_auth_get(self):

        '''Authenticated, inactive GET users are shown the lti-inactive page'''
        client = Client()
        self.assertLogin(client, user='inactive')

        # Ensure lti-entry GET is redirected to lti-inactive
        lti_login_path = reverse('lti-entry')
        inactive_path = reverse('lti-inactive')
        response = client.get(lti_login_path)
        self.assertRedirects(response, inactive_path, status_code=302, target_status_code=200)

        # Ensure active status is not updated
        user = get_user_model().objects.get(username=self.inactive_user.username)
        self.assertFalse(user.is_active)

    def test_inactive_auth_post(self):

        '''Authenticated, inactive POST users, without a nickname set, are shown the lti-entry page'''
        client = Client()
        self.assertLogin(client, user='inactive')

        # Ensure lti-entry POST is redirected to lti-inactive
        lti_login_path = reverse('lti-entry')
        inactive_path = reverse('lti-inactive')
        response = client.post(lti_login_path)
        self.assertRedirects(response, inactive_path, status_code=302, target_status_code=200)

        # Ensure active status is not updated
        user = get_user_model().objects.get(username=self.inactive_user.username)
        self.assertFalse(user.is_active)

    def test_inactive_set_nickname(self):

        '''Inactive users are not allowed to update their nicknames.'''
        self.inactive_user.first_name = "MyNickname"
        self.inactive_user.save()

        client = Client()
        self.assertLogin(client, user='inactive')

        # Ensure lti-entry POST with form data is redirected to lti-inactive
        lti_login_path = reverse('lti-entry')
        inactive_path = reverse('lti-inactive')
        form_data = {'first_name': 'AnotherNickname'}
        response = client.post(lti_login_path, form_data)
        self.assertRedirects(response, inactive_path, status_code=302, target_status_code=200)

        # Ensure the nickname and active status are not updated
        user = get_user_model().objects.get(username=self.inactive_user.username)
        self.assertEqual(user.first_name, "MyNickname")
        self.assertFalse(user.is_active)

    def test_inactive_staff(self):

        '''Ensure that even inactive staff are redirected to lti-inactive'''
        self.inactive_user.first_name = "MyNickname"
        self.inactive_user.save()

        self.assertFalse(self.inactive_user.is_staff)

        client = Client()
        self.assertLogin(client, user='inactive')

        # Fake the LTI session roles
        session = client.session
        session['LTI_LAUNCH'] = {
            'roles': ['Instructor',]
        }
        session.save()

        post_data = {
            'first_name': 'NickName',
        }
        lti_login_path = reverse('lti-entry')
        inactive_path = reverse('lti-inactive')
        response = client.post(lti_login_path, post_data)

        # Ensure the user is redirected
        self.assertRedirects(response, inactive_path, status_code=302, target_status_code=200)

        # Staff status, nickname, and inactive status remain unchanged
        user = get_user_model().objects.get(username=self.inactive_user.username)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.first_name, "MyNickname")
        self.assertFalse(user.is_active)


class LTILoginViewTest(TestOverrideSettings, TestCase):

    # Set the LTI Login Url, and use lti-403 as the login URL
    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL':'https://www.google.com.au', 
        'PERSIST_NAME': 'adelaidex', 
        'PERSIST_PARAMS': ['next'],
    })
    @override_settings(LOGIN_URL='lti-403')
    def test_view(self):

        self.reload_urlconf()

        client = Client()

        # ensure no cookies set
        cookie = client.cookies.get(settings.ADELAIDEX_LTI['PERSIST_NAME'])
        self.assertIsNone(cookie)

        # get login view, with next param set
        target = reverse('artwork-studio')
        querystr = '?next=' + target
        lti_login = reverse('lti-login') + querystr
        response = client.get(lti_login)

        # ensure it redirects to the ADELAIDEX_LTI LOGIN_URL
        self.assertRedirects(response, settings.ADELAIDEX_LTI['LOGIN_URL'], status_code=302, target_status_code=200)

        # ensure cookie was set
        response = client.get(target)
        cookie = client.cookies.get(settings.ADELAIDEX_LTI['PERSIST_NAME'])
        self.assertIsNotNone(cookie)


class LTIEnrolViewTest(TestOverrideSettings, TestCase):

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL':'https://www.google.com.au', 
        'ENROL_URL':'https://www.edx.org', 
        'PERSIST_NAME': 'adelaidex', 
        'PERSIST_PARAMS': ['next'],
    })
    def test_view(self):

        self.reload_urlconf()
        client = Client()

        # ensure no cookies set
        cookie = client.cookies.get(settings.ADELAIDEX_LTI['PERSIST_NAME'])
        self.assertIsNone(cookie)

        # get enrol view, with next param set
        target = reverse('artwork-studio')
        querystr = '?next=' + target
        lti_enrol = reverse('lti-enrol') + querystr
        response = client.get(lti_enrol)

        # ensure it redirects to the ADELAIDEX_LTI ENROL_URL
        self.assertRedirects(response, settings.ADELAIDEX_LTI['ENROL_URL'], status_code=302, target_status_code=200)

        # ensure cookie was set
        response = client.get(target)
        cookie = client.cookies.get(settings.ADELAIDEX_LTI['PERSIST_NAME'])
        self.assertIsNotNone(cookie)


class LTIPermissionDeniedViewTest(TestOverrideSettings, TestCase):

    # Set the LTI Login Url, and use lti-403 as the login URL
    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL':'https://www.google.com.au', 
        'LINK_TEXT': 'Course name Here',
    })
    @override_settings(LOGIN_URL='lti-403')
    def test_view(self):

        self.reload_urlconf()

        # ensure we're logged out
        client = Client()
        client.logout()

        # ensure login-required URL redirects to lti-403
        target = reverse('artwork-studio')
        querystr = '?next=' + target
        lti_403 = reverse('lti-403') + querystr
        response = client.get(target)
        self.assertRedirects(response, lti_403, status_code=302, target_status_code=200)

        # visit lti-403
        response = client.get(lti_403)
        self.assertEquals(response.context['ADELAIDEX_LTI_LINK_TEXT'], settings.ADELAIDEX_LTI['LINK_TEXT'])
        self.assertEquals(response.context['ADELAIDEX_LTI_QUERY_STRING'], querystr)


class LTILoginEntryViewTest(TestOverrideSettings, UserSetUp, TestCase):
    '''Test the full LTI Login/Entry redirect cycle'''

    # Set the LTI Login Url, and use lti-403 as the login URL
    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL':'https://www.google.com.au', 
        'PERSIST_NAME': 'adelaidex', 
        'PERSIST_PARAMS': ['next'],
    })
    @override_settings(LOGIN_URL='lti-403')
    def _performRedirectTest(self, target, target_status_code=200):

        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        client = Client()

        # ensure we're logged out
        client.logout()

        # ensure we've got no LTI cookie set
        cookie = client.cookies.get(settings.ADELAIDEX_LTI['PERSIST_NAME'])
        self.assertIsNone(cookie)

        # visit the lti login redirect url, with the target in the querystring
        querystr = '?next=' + target
        lti_login = reverse('lti-login') + querystr
        response = client.get(lti_login)
        self.assertRedirects(response, settings.ADELAIDEX_LTI['LOGIN_URL'], status_code=302, target_status_code=200)

        # ensure cookies were set
        cookie = client.cookies.get(settings.ADELAIDEX_LTI['PERSIST_NAME'])
        self.assertIsNotNone(cookie)

        # login, to bypass the LTI auth
        client.login(username=self.get_username(), password=self.get_password())

        # post to lti-entry, and ensure we're redirected back to target
        lti_entry = reverse('lti-entry')
        lti_post_param = {'first_name': 'Username'}
        response = client.post(lti_entry, lti_post_param)
        self.assertRedirects(response, target, status_code=302, target_status_code=target_status_code)
        
        # ensure the cookie has cleared by revisiting lti-entry, and ensuring
        # we're redirected properly
        for custom_next in (reverse('artwork-add'), None):
            if custom_next:
                lti_post_param['custom_next'] = custom_next
            else:
                del lti_post_param['custom_next']

            response = client.post(lti_entry, lti_post_param)
            self.assertRedirects(response, custom_next or reverse('home'), status_code=302, target_status_code=200)

        return True

    def test_my_studio(self):
        path = reverse('artwork-studio') # redirects to artwork-author-list
        ok = self._performRedirectTest(path, 302)
        self.assertTrue(ok)

    def test_artwork_add(self):
        path = reverse('artwork-add')
        ok = self._performRedirectTest(path)
        self.assertTrue(ok)

    def test_private_artwork(self):
        private_artwork = Artwork.objects.create(title='Private Artwork', code='// code goes here', author=self.user)
        path = reverse('artwork-view', kwargs={'pk': private_artwork.id})
        ok = self._performRedirectTest(path)
        self.assertTrue(ok)


class UserProfileViewTest(UserSetUp, TestCase):

    def test_anon_view(self):
        '''Profile View requires login'''
        client = Client()
        profile_path = reverse('lti-user-profile')
        response = client.get(profile_path)

        login_path = '%s?next=%s' % (reverse('login'), profile_path)
        self.assertRedirects(response, login_path, status_code=302, target_status_code=200)

    def test_student_view(self):
        '''Students can login'''
        client = Client()
        profile_path = reverse('lti-user-profile')
        response = self.assertLogin(client, next_path=profile_path, user='student')
        self.assertEqual(response.context['object'], self.user)

    def test_staff_view(self):
        '''Staff can login'''
        client = Client()
        profile_path = reverse('lti-user-profile')
        response = self.assertLogin(client, next_path=profile_path, user='staff')
        self.assertEqual(response.context['object'], self.staff_user)

    def test_super_view(self):
        '''Superuser can login'''
        client = Client()
        profile_path = reverse('lti-user-profile')
        response = self.assertLogin(client, next_path=profile_path, user='super')
        self.assertEqual(response.context['object'], self.super_user)

    def test_post_username_required(self):
        '''Username required'''
        client = Client()
        profile_path = reverse('lti-user-profile')
        home_path = reverse('home')
        form_data = {}

        self.assertLogin(client, next_path=profile_path, user='student')
        response = client.post(profile_path, form_data)
        self.assertEqual(self.user, response.context['user'])
        self.assertEqual(self.user, response.context['form'].instance)
        self.assertEqual(2, len(response.context['form'].fields))
        self.assertIn('first_name', response.context['form'].fields)
        self.assertEquals(u'This field is required.', response.context['form']['first_name'].errors[0])
        self.assertIn('time_zone', response.context['form'].fields)
        self.assertEquals([], response.context['form']['time_zone'].errors)

        form_data = {'first_name':'MyNickName'}
        response = client.post(profile_path, form_data)
        self.assertRedirects(response, home_path, status_code=302, target_status_code=200)

        # should have set user nickname, left timezone empty
        user = get_user_model().objects.get(username=self.get_username('student'))
        self.assertEqual(user.first_name, form_data['first_name'])
        self.assertEqual(user.time_zone, '')

    def test_post_timezone(self):
        '''Username required, timezone optional'''
        client = Client()
        profile_path = reverse('lti-user-profile')
        home_path = reverse('home')
        form_data = {'first_name':'MyNickname', 'time_zone': 'Australia/Adelaide'}

        self.assertLogin(client, next_path=profile_path, user='student')
        response = client.post(profile_path, form_data)
        self.assertRedirects(response, home_path, status_code=302, target_status_code=200)

        # should have set user nickname, timezone
        user = get_user_model().objects.get(username=self.get_username('student'))
        self.assertEqual(user.first_name, form_data['first_name'])
        self.assertEqual(user.time_zone, form_data['time_zone'])

    def test_post_default_next(self):
        '''Default next path is home'''
        client = Client()
        profile_path = reverse('lti-user-profile')
        home_path = reverse('home')
        form_data = {'first_name':'MyNickName'}

        self.assertLogin(client, next_path=profile_path, user='student')
        response = client.post(profile_path, form_data)
        self.assertRedirects(response, home_path, status_code=302, target_status_code=200)

    def test_post_with_next(self):
        '''Default next path is home'''
        client = Client()
        next_path = reverse('help')
        profile_path = '%s?next=%s' % (reverse('lti-user-profile'), next_path)
        form_data = {'first_name':'MyNickName'}

        self.assertLogin(client, next_path=profile_path, user='student')
        response = client.post(profile_path, form_data)
        self.assertRedirects(response, next_path, status_code=302, target_status_code=200)

