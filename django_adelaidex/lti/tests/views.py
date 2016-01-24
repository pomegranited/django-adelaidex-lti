import os
import time
from random import randint
from oauth2 import Request, Consumer, SignatureMethod_HMAC_SHA1 as SignatureMethod

from django.views.generic import TemplateView
from django.conf import settings
from django.core.urlresolvers import reverse
from django_adelaidex.lti.models import Cohort


class TestDisqusSSOView(TemplateView):
    template_name='disqus_sso.html'


class TestDisqusSSOView(TemplateView):
    template_name='disqus_sso.html'


class TestOauthPostView(TemplateView):

    template_name = 'oauth.html'

    # Generate the parameters required for an OAUTH 1.0 request
    # http://tools.ietf.org/html/rfc5849
    def oauth_params(self, action, method='POST', uid=None, key=None):
        secret = None
        cohort = None
        oauth_credentials = getattr(settings, 'LTI_OAUTH_CREDENTIALS', {})
        if not key:
            keys = oauth_credentials.keys()
            if len(keys):
                key = keys[0]
            else:
                cohort = Cohort.objects.first()
                if cohort:
                    key = cohort.oauth_key
        if key:
            if key in oauth_credentials:
                secret = oauth_credentials.get(key)
            else:
                if not cohort:
                    cohorts = Cohort.objects.filter(oauth_key=key).all()
                    cohort = None
                    if cohorts:
                        cohort = cohorts[0]
                if cohort:
                    secret = cohort.oauth_secret

        if not secret:
            return None

        consumer = Consumer(key, secret)

        nonce = ''
        for i in range(32):
            nonce = nonce + str(randint(0,9))
        nonce = int(nonce)

        if not uid:
            uid = str(nonce)

        signer = SignatureMethod()
        oauth_params = {
            'oauth_consumer_key': key,
            'oauth_signature_method': signer.name,
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': str(nonce),
            'user_id': uid,
            'oauth_version': '1.0',
            'lti_message_type': 'basic-lti-launch-request',
        }
        request = Request(method, action, oauth_params)
        oauth_params['oauth_signature'] = signer.sign(request, consumer, None)
        return oauth_params

    def get_context_data(self, **kwargs):
        context = super(TestOauthPostView, self).get_context_data(**kwargs)
        context['action'] = self.request.build_absolute_uri(reverse('lti-entry'))
        context['oauth_params'] = self.oauth_params(action=context['action'], **self.kwargs)
        return context
