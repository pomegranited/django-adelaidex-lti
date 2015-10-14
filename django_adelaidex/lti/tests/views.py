import os
import time
from random import randint
from oauth2 import Request, Consumer, SignatureMethod_HMAC_SHA1 as SignatureMethod

from django.views.generic import TemplateView
from django.conf import settings
from django.core.urlresolvers import reverse


class TestDisqusSSOView(TemplateView):
    template_name='disqus_sso.html'


class TestOauthPostView(TemplateView):

    template_name = 'oauth.html'

    # Generate the parameters required for an OAUTH 1.0 request
    # http://tools.ietf.org/html/rfc5849
    def oauth_params(self, action, method='POST', user_id=None):
        keys = getattr(settings, 'LTI_OAUTH_CREDENTIALS', {}).keys()
        if not keys:
            return None

        key = keys[0]
        secret = getattr(settings, 'LTI_OAUTH_CREDENTIALS', {}).get(key)
        if not secret:
            return None
        consumer = Consumer(key, secret)

        nonce = ''
        for i in range(32):
            nonce = nonce + str(randint(0,9))
        nonce = int(nonce)

        # Warning:  This test view creates a new user for each auth.
        # Not sure how to test with existing user_ids, or if we need to.
        if not user_id:
            user_id = str(nonce)

        signer = SignatureMethod()
        oauth_params = {
            'oauth_consumer_key': key,
            'oauth_signature_method': signer.name,
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': str(nonce),
            'user_id': user_id,
            'oauth_version': '1.0',
            'lti_message_type': 'basic-lti-launch-request',
        }
        request = Request(method, action, oauth_params)
        oauth_params['oauth_signature'] = signer.sign(request, consumer, None)
        return oauth_params

    def get_context_data(self, **kwargs):
        context = super(TestOauthPostView, self).get_context_data(**kwargs)
        context['action'] = self.request.build_absolute_uri(reverse('lti-entry'))
        context['oauth_params'] = self.oauth_params(action=context['action'])
        return context
