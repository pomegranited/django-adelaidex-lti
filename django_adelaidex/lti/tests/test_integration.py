import re
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from django_auth_lti.backends import LTIAuthBackend

from django_adelaidex.util.test import SeleniumTestCase, InactiveUserSetUp, TestOverrideSettings, wait_for_page_load
from django_adelaidex.lti.models import Cohort


class LTILoginViewTest(TestOverrideSettings, SeleniumTestCase):

    def test_not_set(self):
        # ensure no cookies set
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 0)

        # get login view, with next param set
        target = reverse('lti-user-profile')
        target_url = '%s%s' % (self.live_server_url, target)
        querystr = '?next=' + target
        lti_login = reverse('lti-login')
        lti_login_url = '%s%s%s' % (self.live_server_url, lti_login, querystr)

        self.selenium.get(lti_login_url)

        # ensure it hasn't redirected
        self.assertEqual(self.selenium.current_url, lti_login_url)

        # ensure only csrf cookie set
        self.selenium.get(target_url)
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0]['name'], 'csrftoken')


    # Set the LTI Login Url, and use lti-403 as the login URL
    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL':'https://www.google.com.au', 
    }, LTI_OAUTH_CREDENTIALS={
        'adelaidex': 'mysecret'
    })
    def test_view(self):

        self.reload_urlconf()

        # ensure no cookies set
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0]['name'], 'csrftoken')

        # get login view, with next param set
        target = reverse('lti-user-profile')
        target_url = '%s%s' % (self.live_server_url, target)
        querystr = '?next=' + target
        lti_login = reverse('lti-login')
        lti_login_url = '%s%s%s' % (self.live_server_url, lti_login, querystr)

        self.selenium.get(lti_login_url)

        # ensure it redirects to the ADELAIDEX_LTI LOGIN_URL
        login_regex = re.compile('^%s' % settings.ADELAIDEX_LTI['LOGIN_URL'])
        self.assertRegexpMatches(self.selenium.current_url, login_regex)

        # ensure cookie was set
        self.selenium.get(target_url)
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 2)
        self.assertEqual(cookies[0]['name'], 'csrftoken')
        self.assertEqual(cookies[1]['name'], 'adelaidex')


class LTIEnrolViewTest(TestOverrideSettings, SeleniumTestCase):

    def test_not_set(self):

        # ensure no cookies set (other than csrf, possibly)
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 0)

        # get enrol view, with next param set
        target = reverse('lti-user-profile')
        target_url = '%s%s' % (self.live_server_url, target)
        querystr = '?next=' + target
        lti_enrol = reverse('lti-enrol')
        lti_enrol_url = '%s%s%s' % (self.live_server_url, lti_enrol, querystr)

        self.selenium.get(lti_enrol_url)

        # ensure it redirects nowhere
        self.assertRegexpMatches(self.selenium.current_url, '')

        # ensure no lti cookies set
        self.selenium.get(target_url)
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0]['name'], 'csrftoken')


    @override_settings(ADELAIDEX_LTI={
        'ENROL_URL':'https://www.google.com.au', 
    }, LTI_OAUTH_CREDENTIALS={
        'adelaidex': 'mysecret'
    })
    def test_view(self):

        self.reload_urlconf()

        # ensure no cookies set
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0]['name'], 'csrftoken')

        # get enrol view, with next param set
        target = reverse('lti-user-profile')
        target_url = '%s%s' % (self.live_server_url, target)
        querystr = '?next=' + target
        lti_enrol = reverse('lti-enrol')
        lti_enrol_url = '%s%s%s' % (self.live_server_url, lti_enrol, querystr)

        self.selenium.get(lti_enrol_url)

        # ensure it redirects to the ADELAIDEX_LTI['ENROL_URL']
        enrol_regex = re.compile(r'^%s' % settings.ADELAIDEX_LTI['ENROL_URL'])
        self.assertRegexpMatches(self.selenium.current_url, enrol_regex)

        # ensure cookie was set
        self.selenium.get(target_url)
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 2)
        self.assertEqual(cookies[0]['name'], 'adelaidex')


class LTIEntryViewTest(SeleniumTestCase):

    def test_default_view(self):

        # ensure we're logged out
        self.performLogout()

        lti_entry_path = reverse('lti-entry')
        lti_entry = '%s%s' % (self.live_server_url, lti_entry_path)
        home_url = '%s%s' % (self.live_server_url, reverse('home'))

        # lti-entry redirects to login
        self.selenium.get(lti_entry)
        self.assertLogin(lti_entry_path)

        # then shows form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)

        first_name.send_keys('Username')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # Ensure we're redirected to home
        self.assertEqual(self.selenium.current_url, home_url)

    def test_custom_next_view(self):

        # ensure we're logged out
        self.performLogout()

        lti_path = reverse('lti-entry')
        lti_entry = '%s%s' % (self.live_server_url, lti_path)
        redirect_path = reverse('lti-user-profile')
        redirect_url = '%s%s' % (self.live_server_url, redirect_path)

        # lti-entry redirects to login
        self.selenium.get(lti_entry)
        self.assertLogin(lti_path)

        # then shows form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)

        first_name.send_keys('Username')

        custom_next = self.selenium.find_element_by_id('id_custom_next')
        self.selenium.execute_script('''
            var elem = arguments[0];
            var value = arguments[1];
            elem.value = value;
        ''', custom_next, redirect_path)

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # Ensure we're redirected to the redirect url
        self.assertEqual(self.selenium.current_url, redirect_url)


class LTIInactiveEntryViewTest(InactiveUserSetUp, SeleniumTestCase):

    @override_settings(LTI_OAUTH_CREDENTIALS={
        'adelaidex': 'mysecret'
    })
    def test_default_view(self):

        lti_entry_path = reverse('lti-entry')
        lti_entry = '%s%s' % (self.live_server_url, lti_entry_path)
        inactive_url = '%s%s' % (self.live_server_url, reverse('lti-inactive'))

        # login inactive user
        self.performLogin(user="inactive")

        # lti-entry redirects inactive users to lti-inactive
        self.selenium.get(lti_entry)

        # should have redirected to lti-inactive
        self.assertEqual(self.selenium.current_url, inactive_url)


class LTIPermissionDeniedViewTest(TestOverrideSettings, SeleniumTestCase):

    # Set the LTI Login Url, and use lti-403 as the login URL
    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL':'https://www.google.com.au',
        'LINK_TEXT': 'Course name',
    })
    def test_view(self):

        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        target_path = reverse('lti-user-profile')
        target_url = '%s%s' % (self.live_server_url, target_path)

        querystr = '?next=' + target_path
        lti_403 = '%s%s%s' % (self.live_server_url, reverse('login'), querystr)
        lti_login = '%s%s%s' % (self.live_server_url, reverse('lti-login'), querystr)
        lti_enrol = '%s%s%s' % (self.live_server_url, reverse('lti-enrol'), querystr)

        # ensure login-required URL redirects to configured login page (lti-403)
        self.selenium.get(target_url)
        self.assertEqual(self.selenium.current_url, lti_403)

        # visit lti-403
        course_link = self.selenium.find_element_by_link_text(settings.ADELAIDEX_LTI['LINK_TEXT'])
        self.assertEqual(course_link.get_attribute('href'), lti_login)

        login_link = self.selenium.find_element_by_link_text('Go to %s' % settings.ADELAIDEX_LTI['LINK_TEXT'])
        self.assertEqual(login_link.get_attribute('href'), lti_login)

        enrol_link = self.selenium.find_element_by_link_text('Enrol in %s' % settings.ADELAIDEX_LTI['LINK_TEXT'])
        self.assertEqual(enrol_link.get_attribute('href'), lti_enrol)


class LTILoginEntryViewTest(TestOverrideSettings, SeleniumTestCase):
    '''Test the full LTI Login/Entry redirect cycle'''

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    },
    LTI_OAUTH_CREDENTIALS = {})
    def test_no_oauth_key(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, when no oauth credentials are available
        login_url = '%s%s' % (self.live_server_url, reverse('test_oauth'))
        self.selenium.get(login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that no key was used
        post_key = self.selenium.find_elements_by_name('oauth_consumer_key')
        self.assertEquals(len(post_key), 0)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should fail login and redirect to lti-403
        lti_403 = reverse('lti-403')
        lti_403_url = '%s%s' % (self.live_server_url, lti_403)
        self.assertEqual(self.selenium.current_url, lti_403_url)

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    },
    LTI_OAUTH_CREDENTIALS = { 'mykey': None })
    def test_no_oauth_secret(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, when no oauth credentials are available
        login_url = '%s%s' % (self.live_server_url, reverse('test_oauth'))
        self.selenium.get(login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure no key was found
        post_key = self.selenium.find_elements_by_name('oauth_consumer_key')
        self.assertEquals(len(post_key), 0)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should fail login and redirect to lti-403
        lti_403 = reverse('lti-403')
        lti_403_url = '%s%s' % (self.live_server_url, lti_403)
        self.assertEqual(self.selenium.current_url, lti_403_url)

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    },
    LTI_OAUTH_CREDENTIALS = { 'mykey': 'mysecret' })
    def test_bad_oauth_secret(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, when no oauth credentials are available
        login_url = '%s%s' % (self.live_server_url, reverse('test_oauth'))
        self.selenium.get(login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the key was found
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), 'mykey')

        # And signature
        post_sig = self.selenium.find_elements_by_name('oauth_signature')
        self.assertEquals(len(post_sig), 1)

        # Change the secret to something else
        self.selenium.execute_script("document.getElementsByName('oauth_signature')[0].setAttribute('value', 'badsignature')");

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should fail login and redirect to lti-403
        lti_403 = reverse('lti-403')
        lti_403_url = '%s%s' % (self.live_server_url, lti_403)
        self.assertEqual(self.selenium.current_url, lti_403_url)

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    },
    LTI_OAUTH_CREDENTIALS = { 'mykey': 'mysecret' })
    def test_bad_oauth_timestamp(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, when no oauth credentials are available
        login_url = '%s%s' % (self.live_server_url, reverse('test_oauth'))
        self.selenium.get(login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the key was found
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), 'mykey')

        # And timestamp
        post_timestamp = self.selenium.find_elements_by_name('oauth_timestamp')
        self.assertEquals(len(post_timestamp), 1)

        # Change the timestamp to something else
        self.selenium.execute_script("document.getElementsByName('oauth_timestamp')[0].setAttribute('value', '1')");

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should fail login and redirect to lti-403
        lti_403 = reverse('lti-403')
        lti_403_url = '%s%s' % (self.live_server_url, lti_403)
        self.assertEqual(self.selenium.current_url, lti_403_url)

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    },
    LTI_OAUTH_CREDENTIALS = { 'mykey': 'mysecret' })
    def test_remove_oauth_key(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, when no oauth credentials are available
        login_url = '%s%s' % (self.live_server_url, reverse('test_oauth'))
        self.selenium.get(login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the key was found
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), 'mykey')

        # Remove the key
        self.selenium.execute_script("var child = document.getElementsByName('oauth_consumer_key')[0]; child.parentNode.removeChild(child);");

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should fail login and redirect to lti-403
        lti_403 = reverse('lti-403')
        lti_403_url = '%s%s' % (self.live_server_url, lti_403)
        self.assertEqual(self.selenium.current_url, lti_403_url)

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    },
    LTI_OAUTH_CREDENTIALS = { 'mykey': 'mysecret' })
    def test_change_key(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, when no oauth credentials are available
        login_url = '%s%s' % (self.live_server_url, reverse('test_oauth'))
        self.selenium.get(login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the key was found
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), 'mykey')

        # Change the key to something else
        self.selenium.execute_script("document.getElementsByName('oauth_consumer_key')[0].setAttribute('value', '1')");

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should fail login and redirect to lti-403
        lti_403 = reverse('lti-403')
        lti_403_url = '%s%s' % (self.live_server_url, lti_403)
        self.assertEqual(self.selenium.current_url, lti_403_url)

    # Set the LTI Login Url, and use lti-403 as the login URL
    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL':'https://www.google.com.au', 
    }, LTI_OAUTH_CREDENTIALS={
        'adelaidex': 'mysecret'
    })
    def test_user_profile_redirect(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # ensure we've got no LTI cookie set
        self.selenium.delete_all_cookies()
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 0)

        # visit the lti login redirect url, with the target in the querystring
        target = reverse('lti-user-profile')
        querystr = '?next=' + target
        target_url = '%s%s' % (self.live_server_url, target)

        lti_login = reverse('lti-login') + querystr
        lti_login_url = '%s%s' % (self.live_server_url, lti_login)
        self.selenium.get(lti_login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # ensure cookie was set
        self.selenium.get(target_url)
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0]['name'], 'adelaidex')

        # lti-entry redirects to login
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)

        # need to force auth real login here to get past lti-entry auth
        self.performLogin(login='auth-login')
        self.selenium.get(lti_entry_url)

        # fill in form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('Username')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to target
        self.assertEqual(self.selenium.current_url, target_url)

        # ensure cookie was cleared
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 2, cookies)
        self.assertEqual(cookies[0]['name'], 'sessionid')
        self.assertEqual(cookies[1]['name'], 'csrftoken')

        # double-check the cookie has cleared by revisiting lti-entry, and
        # ensuring we're redirected properly
        for custom_next in (reverse('lti-user-profile'), None):
            self.selenium.get(lti_entry_url)

            # fill in form
            first_name = self.selenium.find_element_by_id('id_first_name')
            self.assertIsNotNone(first_name)
            first_name.send_keys('Username')

            if custom_next:
                custom_next_url = '%s%s' % (self.live_server_url, custom_next)
                custom_next_field = self.selenium.find_element_by_id('id_custom_next')
                self.selenium.execute_script('''
                    var elem = arguments[0];
                    var value = arguments[1];
                    elem.value = value;
                ''', custom_next_field, custom_next)
            else:
                custom_next_url = '%s%s' % (self.live_server_url, reverse('home'))

            save = self.selenium.find_element_by_id('save_user')
            with wait_for_page_load(self.selenium):
                save.click()

            # Ensure we're redirected to the redirect url
            self.assertEqual(self.selenium.current_url, custom_next_url)

        self.assertTrue(True)

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    }, LTI_OAUTH_CREDENTIALS = { 
        'adelaidex': 'mysecret' 
    })
    def test_oauth(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # ensure we've got no LTI cookie set
        self.selenium.delete_all_cookies()
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 0)

        # visit the lti login redirect url, with the target in the querystring
        target = reverse('lti-user-profile')
        querystr = '?next=' + target
        target_url = '%s%s' % (self.live_server_url, target)

        # lti-login redirects to LOGIN_URL (test_oauth)
        lti_login = reverse('lti-login') + querystr
        lti_login_url = '%s%s' % (self.live_server_url, lti_login)
        self.selenium.get(lti_login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('Username')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to target
        self.assertEqual(self.selenium.current_url, target_url)

        # ensure cookie was cleared
        cookies = self.selenium.get_cookies()
        self.assertEqual(len(cookies), 2, cookies)
        self.assertEqual(cookies[0]['name'], 'sessionid')
        self.assertEqual(cookies[1]['name'], 'csrftoken')

        # double-check the cookie has cleared by revisiting lti-entry, and
        # ensuring we're redirected properly
        for custom_next in (reverse('lti-user-profile'), None):
            self.selenium.get(lti_entry_url)

            # fill in form
            first_name = self.selenium.find_element_by_id('id_first_name')
            self.assertIsNotNone(first_name)
            first_name.send_keys('Username')

            if custom_next:
                custom_next_url = '%s%s' % (self.live_server_url, custom_next)
                custom_next_field = self.selenium.find_element_by_id('id_custom_next')
                self.selenium.execute_script('''
                    var elem = arguments[0];
                    var value = arguments[1];
                    elem.value = value;
                ''', custom_next_field, custom_next)
            else:
                custom_next_url = '%s%s' % (self.live_server_url, reverse('home'))

            save = self.selenium.find_element_by_id('save_user')
            with wait_for_page_load(self.selenium):
                save.click()

            # Ensure we're redirected to the redirect url
            self.assertEqual(self.selenium.current_url, custom_next_url)

        self.assertTrue(True)

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    }, LTI_OAUTH_CREDENTIALS = { 
        'adelaidex': 'mysecret' 
    })
    def test_oauth_user(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account.
        # lti-login redirects to LOGIN_URL (test_oauth)
        lti_login = reverse('lti-login')
        lti_login_url = '%s%s' % (self.live_server_url, lti_login)
        self.selenium.get(lti_login_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMAUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to home
        home_url = '%s%s' % (self.live_server_url, reverse('home'))
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we've added a user
        self.assertEqual(num_users+1, get_user_model().objects.count())

        # 2. Re-authenticate as the same user
        current_user = get_user_model().objects.get(first_name='IMAUSER')
        user_id = current_user.username
        # remove the user prefix
        prefix = LTIAuthBackend.unknown_user_prefix
        user_id = user_id[user_id.startswith(prefix) and len(prefix):] 
        self.performLogout()

        login_user_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_user', kwargs={'uid': user_id}))
        self.selenium.get(login_user_url)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # ensure we're redirected back to home
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we haven't added any more users.
        self.assertEqual(num_users+1, get_user_model().objects.count())

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    },
    LTI_OAUTH_CREDENTIALS = { 
        'mykey': 'mysecret', 
        'mykey2': 'mysecret2',
    })
    def test_oauth_key(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, using the specified key
        oauth_key = 'mykey2'
        login_key_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_key', kwargs={'key': oauth_key}))
        self.selenium.get(login_key_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the correct key was used
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), oauth_key)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMAUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to home
        home_url = '%s%s' % (self.live_server_url, reverse('home'))
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we've added a user
        self.assertEqual(num_users+1, get_user_model().objects.count())

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    },
    LTI_OAUTH_CREDENTIALS = { 
        'mykey': 'mysecret', 
        'mykey2': 'mysecret2',
    })
    def test_oauth_user_key(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, using the specified key
        oauth_key = 'mykey2'
        login_key_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_key', kwargs={'key': oauth_key}))
        self.selenium.get(login_key_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the correct key was used
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), oauth_key)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMAUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to home
        home_url = '%s%s' % (self.live_server_url, reverse('home'))
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we've added a user
        self.assertEqual(num_users+1, get_user_model().objects.count())

        # 2. Re-authenticate as the same user
        current_user = get_user_model().objects.get(first_name='IMAUSER')
        user_id = current_user.username
        # remove the user prefix
        prefix = LTIAuthBackend.unknown_user_prefix
        user_id = user_id[user_id.startswith(prefix) and len(prefix):] 
        self.performLogout()

        login_user_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_user_key', 
                    kwargs={'uid': user_id, 'key': oauth_key}))
        self.selenium.get(login_user_url)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # ensure we're redirected back to home
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we haven't added any more users.
        self.assertEqual(num_users+1, get_user_model().objects.count())


class LTILoginEntryCohortTest(TestOverrideSettings, SeleniumTestCase):
    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    }, LTI_OAUTH_CREDENTIALS={
        'adelaidex': 'mysecret'
    })
    def test_oauth_cohort_key(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # create two cohorts
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

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, using the specified key
        login_key_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_key', kwargs={'key': cohort.oauth_key}))
        self.selenium.get(login_key_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the correct key was used
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), cohort.oauth_key)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMAUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to home
        home_url = '%s%s' % (self.live_server_url, reverse('home'))
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we've added a user
        self.assertEqual(num_users+1, get_user_model().objects.count())

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    }, LTI_OAUTH_CREDENTIALS={
        'adelaidex': 'mysecret'
    })
    def test_oauth_cohort_user_key(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # create two cohorts
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

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, using the specified key
        login_key_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_key', kwargs={'key': cohort2.oauth_key}))
        self.selenium.get(login_key_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the correct key was used
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), cohort2.oauth_key)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMAUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to home
        home_url = '%s%s' % (self.live_server_url, reverse('home'))
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we've added a user
        self.assertEqual(num_users+1, get_user_model().objects.count())

        # Ensure the new user gets a cohort
        current_user = get_user_model().objects.get(first_name='IMAUSER')
        self.assertEqual(current_user.cohort, cohort2)

        # 2. Re-authenticate as the same user
        user_id = current_user.username
        # remove the user prefix
        prefix = LTIAuthBackend.unknown_user_prefix
        user_id = user_id[user_id.startswith(prefix) and len(prefix):] 
        self.performLogout()

        login_user_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_user_key', 
                    kwargs={'uid': user_id, 'key': cohort2.oauth_key}))
        self.selenium.get(login_user_url)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # ensure we're redirected back to home
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we haven't added any more users.
        self.assertEqual(num_users+1, get_user_model().objects.count())


class UserProfileViewTest(TestOverrideSettings, SeleniumTestCase):

    def test_anon_view(self):
        '''Profile View requires login'''
        profile_path = reverse('lti-user-profile')
        profile_url = '%s%s' % (self.live_server_url, profile_path)

        login_path = reverse('login')
        login_url = '%s%s?next=%s' % (self.live_server_url, login_path, profile_path)

        self.selenium.get(profile_url)
        self.assertEqual(self.selenium.current_url, login_url)

    def test_student_view(self):
        '''Students can login'''
        profile_path = reverse('lti-user-profile')
        profile_url = '%s%s' % (self.live_server_url, profile_path)

        self.selenium.get(profile_url)
        self.assertLogin(profile_path, user="student")
        self.assertEqual(self.selenium.current_url, profile_url)

        labels = self.selenium.find_elements_by_tag_name('label')
        self.assertEqual(len(labels), 4)
        self.assertEqual(labels[0].text, 'Nickname:')
        self.assertEqual(labels[1].text, '')
        self.assertEqual(labels[1].get_attribute('class'), 'error')
        self.assertEqual(labels[2].text, 'Timezone:')
        self.assertEqual(labels[3].text, '')
        self.assertEqual(labels[3].get_attribute('class'), 'error')

    def test_staff_view(self):
        '''Staff can login'''
        profile_path = reverse('lti-user-profile')
        profile_url = '%s%s' % (self.live_server_url, profile_path)

        self.selenium.get(profile_url)
        self.assertLogin(profile_path, user="staff")
        self.assertEqual(self.selenium.current_url, profile_url)

        labels = self.selenium.find_elements_by_tag_name('label')
        self.assertEqual(len(labels), 5)
        self.assertEqual(labels[0].text, 'Staff access:')
        self.assertEqual(labels[1].text, 'Nickname:')
        self.assertEqual(labels[2].text, '')
        self.assertEqual(labels[2].get_attribute('class'), 'error')
        self.assertEqual(labels[3].text, 'Timezone:')
        self.assertEqual(labels[4].text, '')
        self.assertEqual(labels[4].get_attribute('class'), 'error')

    def test_super_view(self):
        '''Superuser can login'''
        profile_path = reverse('lti-user-profile')
        profile_url = '%s%s' % (self.live_server_url, profile_path)

        self.selenium.get(profile_url)
        self.assertLogin(profile_path, user="super")
        self.assertEqual(self.selenium.current_url, profile_url)

        labels = self.selenium.find_elements_by_tag_name('label')
        self.assertEqual(len(labels), 5)
        self.assertEqual(labels[0].text, 'Staff access:')
        self.assertEqual(labels[1].text, 'Nickname:')
        self.assertEqual(labels[2].text, '')
        self.assertEqual(labels[2].get_attribute('class'), 'error')
        self.assertEqual(labels[3].text, 'Timezone:')
        self.assertEqual(labels[4].text, '')
        self.assertEqual(labels[4].get_attribute('class'), 'error')

    def test_post_username_required(self):
        profile_path = reverse('lti-user-profile')
        profile_url = '%s%s' % (self.live_server_url, profile_path)

        home_path = reverse('home')
        home_url = '%s%s' % (self.live_server_url, home_path)

        self.selenium.get(profile_url)
        self.assertLogin(profile_path, user="student")
        self.assertEqual(self.selenium.current_url, profile_url)

        labels = self.selenium.find_elements_by_tag_name('label')
        self.assertEqual(len(labels), 4)
        self.assertEqual(labels[0].text, 'Nickname:')
        self.assertEqual(labels[1].text, '')
        self.assertEqual(labels[1].get_attribute('class'), 'error')
        self.assertEqual(labels[2].text, 'Timezone:')
        self.assertEqual(labels[3].text, '')
        self.assertEqual(labels[3].get_attribute('class'), 'error')

        with wait_for_page_load(self.selenium):
            self.selenium.find_element_by_id('save_user').click()

        labels = self.selenium.find_elements_by_tag_name('label')
        self.assertEqual(len(labels), 4)
        self.assertEqual(labels[0].text, 'Nickname:')
        self.assertEqual(labels[1].text, 'This field is required.')
        self.assertEqual(labels[1].get_attribute('class'), 'error')
        self.assertEqual(labels[2].text, 'Timezone:')
        self.assertEqual(labels[3].text, '')
        self.assertEqual(labels[3].get_attribute('class'), 'error')

        form_data = {'first_name': 'MyNickname'}
        for field, value in form_data.iteritems():
            self.selenium.find_element_by_id('id_' + field).send_keys(value)
        with wait_for_page_load(self.selenium):
            self.selenium.find_element_by_id('save_user').click()

        # should be redirected to home
        self.assertEqual(self.selenium.current_url, home_url)

        # POST should have set user nickname, used default timezone
        user = get_user_model().objects.get(username=self.get_username('student'))
        self.assertEqual(user.first_name, form_data['first_name'])
        self.assertEqual(user.time_zone, 'UTC')

    def test_post_timezone(self):
        profile_path = reverse('lti-user-profile')
        profile_url = '%s%s' % (self.live_server_url, profile_path)

        home_path = reverse('home')
        home_url = '%s%s' % (self.live_server_url, home_path)

        self.selenium.get(profile_url)
        self.assertLogin(profile_path, user="student")

        form_data = {'first_name': 'MyNickname', 'time_zone': 'Australia/Adelaide'}
        for field, value in form_data.iteritems():
            self.selenium.find_element_by_id('id_' + field).send_keys(value)
        with wait_for_page_load(self.selenium):
            self.selenium.find_element_by_id('save_user').click()

        # should be redirected to home
        self.assertEqual(self.selenium.current_url, home_url)

        # POST should have set user nickname, timezone
        user = get_user_model().objects.get(username=self.get_username('student'))
        self.assertEqual(user.first_name, form_data['first_name'])
        self.assertEqual(user.time_zone, form_data['time_zone'])

    def test_post_with_next(self):
        next_path = reverse('lti-inactive')
        next_url = '%s%s' % (self.live_server_url, next_path)

        profile_path = '%s?next=%s' % (reverse('lti-user-profile'), next_path)
        profile_url = '%s%s' % (self.live_server_url, profile_path)

        self.selenium.get(profile_url)
        self.assertLogin(profile_path, user="student")

        form_data = {'first_name': 'MyNickname'}
        for field, value in form_data.iteritems():
            self.selenium.find_element_by_id('id_' + field).send_keys(value)
        with wait_for_page_load(self.selenium):
            self.selenium.find_element_by_id('save_user').click()

        # should be redirected to next_path
        self.assertEqual(self.selenium.current_url, next_url)

        # POST should have set user nickname, used default timezone
        user = get_user_model().objects.get(username=self.get_username('student'))
        self.assertEqual(user.first_name, form_data['first_name'])
        self.assertEqual(user.time_zone, 'UTC')

    @override_settings(LTI_OAUTH_CREDENTIALS={
        'adelaidex': 'mysecret'
    })
    def test_cancel_post_custom_next(self):
        next_path = reverse('lti-inactive')
        next_url = '%s%s' % (self.live_server_url, next_path)

        profile_path = '%s?next=%s' % (reverse('lti-user-profile'), next_path)
        profile_url = '%s%s' % (self.live_server_url, profile_path)

        self.selenium.get(profile_url)
        self.assertLogin(profile_path, user="student")

        form_data = {'first_name': 'MyNickname', 'time_zone': 'Australia/Adelaide'}
        for field, value in form_data.iteritems():
            self.selenium.find_element_by_id('id_' + field).send_keys(value)

        with wait_for_page_load(self.selenium):
            self.selenium.find_element_by_id('cancel_user').click()

        # should be redirected to next_path
        self.assertEqual(self.selenium.current_url, next_url)

        # POST should not have set user nickname, used default timezone
        user = get_user_model().objects.get(username=self.get_username('student'))
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.time_zone, None)

    @override_settings(ADELAIDEX_LTI={
        'LOGIN_URL': reverse('test_oauth'),
    }, LTI_OAUTH_CREDENTIALS={
        'adelaidex': 'mysecret'
    })
    def test_unique_nickname_in_cohort(self):
        # url config is dependent on app settings, so reload
        self.reload_urlconf()

        # ensure we're logged out
        self.performLogout()

        # create two cohorts
        cohort = Cohort.objects.create(
            title='Test Cohort',
            oauth_key='mykey',
            oauth_secret='mysecret',
            login_url='http://google.com',
        )
        cohort2 = Cohort.objects.create(
            title='Test Cohort2',
            oauth_key='mykey1',
            oauth_secret='mysecret1',
            login_url='http://google.com',
        )

        # get current user count
        num_users = get_user_model().objects.count()

        # 1. Login and create a new user account, using the specified key
        login_key_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_key', kwargs={'key': cohort.oauth_key}))
        self.selenium.get(login_key_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the correct key was used
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), cohort.oauth_key)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMAUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to home
        home_url = '%s%s' % (self.live_server_url, reverse('home'))
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we've added a user
        self.assertEqual(num_users+1, get_user_model().objects.count())

        # Ensure the new user gets a cohort
        current_user = get_user_model().objects.get(first_name='IMAUSER')
        self.assertEqual(current_user.cohort, cohort)


        # 2. Login a second new user, using the same cohort, and same nickname
        self.performLogout()
        self.selenium.get(login_key_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the correct key was used
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), cohort.oauth_key)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMAUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # Ensure error is shown
        lis = self.selenium.find_elements_by_css_selector('.errorlist li')
        self.assertEqual(len(lis), 1)
        self.assertEqual(lis[0].text, 'Someone with this nickname already exists in your cohort. '
                                      'Please try a different nickname.')

        # Try a different username
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMANOTHERUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to home
        home_url = '%s%s' % (self.live_server_url, reverse('home'))
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we've added a second user
        self.assertEqual(num_users+2, get_user_model().objects.count())


        # 3. Login and create a third user account, using the other cohort key
        self.performLogout()
        login_key_url = '%s%s' % (self.live_server_url,
                reverse('test_oauth_key', kwargs={'key': cohort2.oauth_key}))
        self.selenium.get(login_key_url)
        self.assertRegexpMatches(self.selenium.current_url, settings.ADELAIDEX_LTI['LOGIN_URL'])

        # Ensure that the correct key was used
        post_key = self.selenium.find_element_by_name('oauth_consumer_key')
        self.assertEquals(post_key.get_attribute('value'), cohort2.oauth_key)

        # Post oauth credentials to test_oauth by clicking 'Post' button
        post_button = self.selenium.find_element_by_id('post_oauth')
        post_button.click()

        # Should login and redirect to lti-entry
        lti_entry = reverse('lti-entry')
        lti_entry_url = '%s%s' % (self.live_server_url, lti_entry)
        self.assertEqual(self.selenium.current_url, lti_entry_url)

        # fill in welcome form, using the same username as the first user
        first_name = self.selenium.find_element_by_id('id_first_name')
        self.assertIsNotNone(first_name)
        first_name.send_keys('IMAUSER')

        save = self.selenium.find_element_by_id('save_user')
        with wait_for_page_load(self.selenium):
            save.click()

        # and ensure we're redirected back to home
        home_url = '%s%s' % (self.live_server_url, reverse('home'))
        self.assertEqual(self.selenium.current_url, home_url)

        # verify that we've added a third user
        self.assertEqual(num_users+3, get_user_model().objects.count())

        # Ensure there's two users with the same first_name
        imausers = get_user_model().objects.filter(first_name='IMAUSER')
        self.assertEqual(len(imausers), 2)
        self.assertEqual(imausers[0].cohort, cohort)
        self.assertEqual(imausers[1].cohort, cohort2)
