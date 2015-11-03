from django.conf import settings
from django.utils.safestring import mark_safe
import base64
import hashlib
import hmac
import json
import time

from django_adelaidex.lti.models import Cohort


def lti_settings(request):
    '''
    Adds LTI-related settings to the context.
    '''
    cohort = Cohort.objects.get_current()
    if cohort:
        lti = {'ADELAIDEX_LTI_LINK_TEXT': cohort.title}
    else:
        lti = {'ADELAIDEX_LTI_LINK_TEXT': ''}

    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        query_string = '?%s' % query_string
    lti['ADELAIDEX_LTI_QUERY_STRING'] = query_string
    return lti


def disqus_settings(request):
    '''
    Adds DISQUS-related settings to the context.
    '''
    disqus_settings = getattr(settings, 'ADELAIDEX_LTI_DISQUS', {})
    return {'DISQUS_SHORTNAME': disqus_settings.get('SHORTNAME', '')}


def disqus_sso(request):
    # ref https://github.com/disqus/DISQUS-API-Recipes/blob/master/sso/python/sso.py
    # create a JSON packet of our user data attributes
    
    disqus_settings = getattr(settings, 'ADELAIDEX_LTI_DISQUS', {})

    # Get the authenticated user's email, or use the default 
    email = None
    if request.user.is_authenticated():
        email = request.user.email
        if not email:
            default_email = disqus_settings.get('DEFAULT_EMAIL', '')
            if default_email:
                email = default_email.format(user=request.user)

    # Email is required for sso
    if not email:
        return {'DISQUS_SSO': ''}

    data = json.dumps({
        'id': request.user.username,
        'username': request.user.first_name,
        'email': email,
    })
    # encode the data to base64
    message = base64.b64encode(data)
    # generate a timestamp for signing the message
    timestamp = int(time.time())
    # generate our hmac signature
    sig = hmac.HMAC(disqus_settings.get('SECRET_KEY', ''), '%s %s' %
                    (message, timestamp), hashlib.sha1).hexdigest()
 
    # return a script tag to insert the sso message
    script = '''<script type="text/javascript">'''\
    '''var disqus_config=function(){'''\
    '''this.page.remote_auth_s3="%(message)s %(sig)s %(timestamp)s";'''\
    '''this.page.api_key="%(pub_key)s";'''\
    '''}</script>''' % dict(
        message=message,
        timestamp=timestamp,
        sig=sig,
        pub_key=disqus_settings.get('PUBLIC_KEY', ''),
    )

    return {'DISQUS_SSO': mark_safe(script)}
