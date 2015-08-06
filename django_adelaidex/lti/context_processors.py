from django.conf import settings

def lti_settings(request):
    '''
    Adds LTI-related settings to the context.
    '''
    adelaidex_lti = getattr(settings, 'ADELAIDEX_LTI', {})
    lti = {'ADELAIDEX_LTI_LINK_TEXT': adelaidex_lti.get('LINK_TEXT', '')}

    query_string = request.META.get('QUERY_STRING', '')
    if query_string:
        query_string = '?%s' % query_string
    lti['ADELAIDEX_LTI_QUERY_STRING'] = query_string
    return lti
