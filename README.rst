django\_adelaidex.lti
====================

LTI integration used by the AdelaideX Django applications.

Usage
-----

1. Add django\_adelaidex.lti to your settings.INSTALLED\_APPS::
    INSTALLED_APPS = (
        ...
        'django_adelaidex.lti',
    )

2. Configure settings.ADELAIDEX\_LTI, e.g.::

    ADELAIDEX_LTI = {
        'LOGIN_URL': None,
        'COURSE_URL': 'https://courses.edx.org/courses...',
        'ENROL_URL': 'https://edx.org/course/...',
        'OAUTH_CREDENTIALS': {
            'mykey': 'mysecret'
        },
        'LINK_TEXT': 'Course Name Goes Here',
        'PERSIST_NAME': 'lti-myapp',
        'PERSIST_PARAMS': ['next'],
        'STAFF_MEMBER_GROUP': 1,
    }

3. Optionally add django\_adelaidex.lti.middleware to MIDDLEWARE\_CLASSES::

    MIDDLEWARE_CLASSES = (
        ...
        'django_adelaidex.lti.middleware.TimezoneMiddleware',
    )

4. Optionally add django\_adelaidex.lti.context\_processors to TEMPLATE\_CONTEXT\_PROCESSORS::

    TEMPLATE_CONTEXT_PROCESSORS = (
        ...
        'django_adelaidex.lti.context_processors.lti_settings',
    )

5. Append this to your TEMPLATE_DIRS::

    TEMPLATE_DIRS = (
        ...
        # TODO Hopefully fixed in Django 1.8
        os.path.join( SITE_PACKAGES_INSTALL_DIR, 'django_adelaidex', 'lti', 'templates' ),
    )

6. Include the URLconf in your project urls.py::

    url(r'^lti/', include('django_adelaidex.lti.urls')),

7. Optionally configure overriding your default 'login' url with our 403 page,
   to disallow normal Django user authentication when running under LTI mode, e.g.::
    
    url(r'^login/$',
        django_adelaidex.lti.views.LTIPermissionDeniedView.as_view(),
        name='login') if settings.ADELAIDEX_LTI.get('LOGIN_URL') 
    else
    url(r'^login/$', django.contrib.auth.views.auth_views.login, name='login'),
