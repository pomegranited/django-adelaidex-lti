from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.core.urlresolvers import reverse


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
