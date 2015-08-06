from django.test import TestCase
from django.test.client import Client
from django.conf import settings

class LTILinkTextTest(TestCase):

    def setUp(self):
        self.hasattr_adelaidex_lti = hasattr(settings, 'ADELAIDEX_LTI')
        self.adelaidex_lti = getattr(settings, 'ADELAIDEX_LTI')

    def tearDown(self):
        if self.hasattr_adelaidex_lti:
            setattr(settings, 'ADELAIDEX_LTI', self.adelaidex_lti)

    def test_lti_link_text_not_set(self):
        if self.hasattr_adelaidex_lti:
            del settings.ADELAIDEX_LTI['LINK_TEXT']

        client = Client()
        response = client.get('/')
        self.assertEquals(response.context['ADELAIDEX_LTI_LINK_TEXT'], '')

    def test_lti_link_text_set(self):
        setattr(settings, 'ADELAIDEX_LTI', {'LINK_TEXT': 'Hi there'})

        client = Client()
        response = client.get('/')
        self.assertEquals(response.context['ADELAIDEX_LTI_LINK_TEXT'], 'Hi there')


class LTIQueryStringTest(TestCase):

    def test_lti_query_string_not_set(self):
        client = Client()
        response = client.get('/')
        self.assertEquals(response.context['ADELAIDEX_LTI_QUERY_STRING'], '')

    def test_lti_link_text_set(self):
        client = Client()
        response = client.get('/?query=hi+there')
        self.assertEquals(response.context['ADELAIDEX_LTI_QUERY_STRING'], '?query=hi+there')
