from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
import re

from django_adelaidex.util.test import UserSetUp


class LTILinkTextTest(TestCase):

    def test_lti_link_text_not_set(self):
        client = Client()
        response = client.get(reverse('home'))
        self.assertEquals(response.context['ADELAIDEX_LTI_LINK_TEXT'], '')

    @override_settings(ADELAIDEX_LTI={'LINK_TEXT': 'Hi there'})
    def test_lti_link_text_set(self):
        client = Client()
        response = client.get(reverse('home'))
        self.assertEquals(response.context['ADELAIDEX_LTI_LINK_TEXT'], 'Hi there')


class LTIQueryStringTest(TestCase):

    def test_lti_query_string_not_set(self):
        client = Client()
        response = client.get(reverse('home'))
        self.assertEquals(response.context['ADELAIDEX_LTI_QUERY_STRING'], '')

    def test_lti_link_text_set(self):
        client = Client()
        response = client.get('%s?query=hi+there' % reverse('home'))
        self.assertEquals(response.context['ADELAIDEX_LTI_QUERY_STRING'], '?query=hi+there')


class DisqusSettingsTest(TestCase):

    def test_not_set(self):
        client = Client()
        response = client.get(reverse('test-disqus-sso'))
        self.assertEquals(response.context['DISQUS_SHORTNAME'], '')

    @override_settings(ADELAIDEX_LTI_DISQUS={'SHORTNAME':'notarealshortname'})
    def test_override(self):
        client = Client()
        response = client.get(reverse('test-disqus-sso'))
        self.assertEquals(response.context['DISQUS_SHORTNAME'], settings.ADELAIDEX_LTI_DISQUS['SHORTNAME'])


class DisqusSsoTest(UserSetUp, TestCase):

    def disqus_regex_text(self):
        disqus_settings = getattr(settings, 'ADELAIDEX_LTI_DISQUS', {})
        return '<script type="text/javascript">var disqus_config=function\(\){this.page.remote_auth_s3="[a-zA-Z0-9=]{96}\\s[a-f0-9]{40}\\s[0-9]{10}";this.page.api_key="%s";}</script>' % disqus_settings.get('PUBLIC_KEY', '')

    def test_unauth(self):
        client = Client()
        response = client.get(reverse('test-disqus-sso'))
        self.assertEquals(response.context['DISQUS_SSO'], '')

    def test_no_default_email(self):
        client = Client()
        self.assertEquals(self.user.email, '')
        response = self.assertLogin(client, reverse('test-disqus-sso'))
        self.assertEquals(response.context['DISQUS_SSO'], '')

    @override_settings(ADELAIDEX_LTI_DISQUS={
        'DEFAULT_EMAIL':'{user.username}@edx.org',
    })
    def test_default_email(self):
        client = Client()
        self.assertEquals(self.user.email, '')
        response = self.assertLogin(client, reverse('test-disqus-sso'))
        disqus_regex = re.compile('^%s$' % self.disqus_regex_text())
        self.assertRegexpMatches(response.context['DISQUS_SSO'], disqus_regex)

    @override_settings(ADELAIDEX_LTI_DISQUS={
        'SECRET_KEY':'QksEbQJ4y0AeJSFvzOY43PkSV2fPkhjbXXUtp4uRwQwU0DAbHQnaG6X6JIk83ZHy',
        'PUBLIC_KEY':'jbXXUtp4uRwQwU0DAbHQnaG6X6JIk83ZHyQksEbQJ4y0AeJSFvzOY43PkSV2fPkh',
    })
    def test_set_disqus_keys(self):
        client = Client()
        self.user.email = 'someone@somewhere.net'
        self.user.save()
        response = self.assertLogin(client, reverse('test-disqus-sso'))
        disqus_regex = re.compile('^%s$' % self.disqus_regex_text())
        self.assertRegexpMatches(response.context['DISQUS_SSO'], disqus_regex)

    def test_user_email(self):
        client = Client()
        self.user.email = 'someone@somewhere.net'
        self.user.save()
        response = self.assertLogin(client, reverse('test-disqus-sso'))
        disqus_regex = re.compile('^%s$' % self.disqus_regex_text())
        self.assertRegexpMatches(response.context['DISQUS_SSO'], disqus_regex)

    def test_safe_encoding(self):
        client = Client()
        self.user.email = 'someone@somewhere.net'
        self.user.save()
        response = self.assertLogin(client, reverse('test-disqus-sso'))
        disqus_regex = re.compile('''^Vary: Cookie\r\nContent-Type: text/html; charset=utf-8\r\n\r\n%s\n$''' 
            % self.disqus_regex_text())
        self.assertRegexpMatches('%s' % response, disqus_regex)
