from django.views.generic import UpdateView, TemplateView, RedirectView
from django_auth_lti.mixins import LTIUtilityMixin, LTIRoleRestrictionMixin
from django.core.urlresolvers import reverse, resolve, get_script_prefix
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.http import is_safe_url
from django.shortcuts import get_object_or_404
from django_adelaidex.mixins import TemplatePathMixin, CSRFExemptMixin, LoggedInMixin
from django_adelaidex.lti.models import UserForm
import re
import pickle


class UserViewMixin(object):
    form_class = UserForm
    model = UserForm._meta.model

    def get_object(self):
        '''This view's object is the current user'''
        return get_object_or_404(self.model, pk=self.request.user.id)

    def get_success_url(self, next_param=None, default='home'):

        url_name = default
        kwargs = {}

        # If no next param, try to get it from the GET request
        if not next_param:
            next_param = self.request.GET.get(REDIRECT_FIELD_NAME)

        if next_param:

            # Strip leading script prefix
            script_prefix = get_script_prefix()
            if script_prefix:
                next_param = re.sub(r'^%s' % get_script_prefix(), '/', next_param)

            if next_param and is_safe_url(url=next_param, host=self.request.get_host()):
                resolved = resolve(next_param)
                url_name = resolved.url_name
                kwargs = resolved.kwargs

        return reverse(url_name, kwargs=kwargs)


class UserProfileView(LoggedInMixin, UserViewMixin, TemplatePathMixin, UpdateView):
    TemplatePathMixin.template_dir = 'django_adelaidex_lti'
    template_name = TemplatePathMixin.prepend_template_path('profile.html')


class LTIPermissionDeniedView(TemplatePathMixin, TemplateView):

    TemplatePathMixin.template_dir = 'django_adelaidex_lti'
    template_name = TemplatePathMixin.prepend_template_path('lti-403.html')


class LTIInactiveView(CSRFExemptMixin, TemplatePathMixin, TemplateView):
    TemplatePathMixin.template_dir = 'django_adelaidex_lti'
    template_name = TemplatePathMixin.prepend_template_path('lti-inactive.html')


class LTIPersistMixin(object):

    def lti_settings(self, key=None, default=None):
        adelaidex_lti = getattr(settings, 'ADELAIDEX_LTI', {})
        if key:
            return adelaidex_lti.get(key, default)
        return adelaidex_lti


class LTIRedirectView(LTIPersistMixin, RedirectView):

    # Send 302, in case we need to change anything
    permanent=False

    # Store current GET parms to a cookie, to be used by LTIEntryView.get_success_url()
    def dispatch(self, *args, **kwargs):

        if 'redirect_url' in kwargs:
            self.redirect_url = kwargs['redirect_url']
            del kwargs['redirect_url']

        response = super(LTIRedirectView, self).dispatch(*args, **kwargs)

        # Store the given persistent parameters, serialized, in a cookie,
        # if configured to do so.
        cookie_name = self.lti_settings('PERSIST_NAME')
        if cookie_name:
            store_params = {}
            persist_params = self.lti_settings('PERSIST_PARAMS', [])
            for key in persist_params:
                store_params[key] = self.request.GET.get(key)

            try:
                store_params = pickle.dumps(store_params)
                response.set_cookie(cookie_name, store_params)
            except:
                pass # ignore corrupted params or other pickling errors

        return response

    def get_redirect_url(self):
        return self.redirect_url


class LTIEntryView(LTIPersistMixin, UserViewMixin, CSRFExemptMixin, LTIUtilityMixin, TemplatePathMixin, UpdateView):

    TemplatePathMixin.template_dir = 'django_adelaidex_lti'
    template_name = TemplatePathMixin.prepend_template_path('lti-entry.html')

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated():
            if self.request.user.is_active:
                return super(LTIEntryView, self).get(request, *args, **kwargs)
            else:
                return HttpResponseRedirect(reverse('lti-inactive'))

        return HttpResponseRedirect('%s?%s=%s' % (reverse('login'), REDIRECT_FIELD_NAME, self.request.get_full_path()))

    def post(self, request, *args, **kwargs):
        '''Bypass this form if we already have a user.first_name 
           (and we're not trying to POST an update).'''

        self.object = self.get_object()
        if self.request.user.is_authenticated() and self.request.user.is_active:
            if not 'first_name' in self.request.POST and self.object.first_name:
                return HttpResponseRedirect(self.get_success_url())
            else:
                return super(LTIEntryView, self).post(request, *args, **kwargs)

        return HttpResponseRedirect(reverse('lti-inactive'))

    def form_valid(self, form):
        '''Set is_staff setting based on LTI User roles'''

        roles = self.current_user_roles()
        if 'Instructor' in roles:
            form.instance.is_staff = True
        else:
            form.instance.is_staff = False

        response = super(LTIEntryView, self).form_valid(form)

        # clear out the persistent LTI parameters; 
        # they've been used by get_success_url()
        cookie_name = self.lti_settings('PERSIST_NAME')
        if cookie_name:
            response.delete_cookie(cookie_name)

        return response

    def get_success_url(self):
        '''If LTIRedirectView or edX sent a 'custom_next' path, redirect there.'''

        # See if this request started from an LTIRedirectView, and so has a cookie.
        next_param = None
        cookie_name = self.lti_settings('PERSIST_NAME', '')
        cookie = self.request.COOKIES.get(cookie_name)
        if cookie:
            try:
                stored_params = pickle.loads(cookie)
                next_param = stored_params.get(REDIRECT_FIELD_NAME)
            except:
                pass # ignore corrupted cookies or errors during unpickling

        # If no next param found in cookie, get it from the POST request
        if not next_param:
            next_param = self.request.POST.get('custom_next')

        return super(LTIEntryView, self).get_success_url(next_param)
