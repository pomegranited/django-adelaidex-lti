django\_adelaidex.lti
====================

LTI integration used by the AdelaideX Django applications.

Usage
-----

1. Configure settings.ADELAIDEX\_LTI, e.g.::

    ADELAIDEX_LTI = {
        'LOGIN_URL': None,
        'COURSE_URL': 'https://courses.edx.org/courses...',
        'ENROL_URL': 'https://edx.org/course/...',
        'LINK_TEXT': 'Course Name Goes Here',
        'PERSIST_NAME': 'lti-myapp',
        'PERSIST_PARAMS': ['next'],
        'STAFF_MEMBER_GROUP': 1,
    }
    LTI_OAUTH_CREDENTIALS': {
        'mykey': 'mysecret'
    },

2. Add django\_adelaidex.lti to your settings.INSTALLED\_APPS::

    INSTALLED_APPS = (
        ...
        'django_adelaidex.util', # for django_adelaidex.util.templatetags.dict_filters
        'django_adelaidex.lti',
    )

3. Add django\_adelaidex.lti.middleware to MIDDLEWARE\_CLASSES::

    MIDDLEWARE_CLASSES = (
        ...
        'django_auth_lti.middleware.LTIAuthMiddleware',
        'django_adelaidex.lti.middleware.TimezoneMiddleware',
    )

4. Add django\_adelaidex.lti.context\_processors to TEMPLATE\_CONTEXT\_PROCESSORS::

    TEMPLATE_CONTEXT_PROCESSORS = (
        ...
        'django.core.context_processors.request', # required by _profile.html
        'django_adelaidex.lti.context_processors.lti_settings',
    )

5. Append this to your TEMPLATE_DIRS::

    TEMPLATE_DIRS = (
        ...
        # TODO Hopefully fixed in Django 1.8
        os.path.join( SITE_PACKAGES_INSTALL_DIR, 'django_adelaidex', 'lti', 'templates' ),
    )

6. Update your user model::

    AUTH_USER_MODEL = 'lti.User'


6. Include the URLconf in your project urls.py::

    url(r'^lti/', include('django_adelaidex.lti.urls')),

7. Optionally configure overriding your default 'login' url with our 403 page,
   to disallow normal Django user authentication when running under LTI mode, e.g.::
    
    url(r'^login/$',
        django_adelaidex.lti.views.LTIPermissionDeniedView.as_view(),
        name='login') if settings.ADELAIDEX_LTI.get('LOGIN_URL') 
    else
    url(r'^login/$', django.contrib.auth.views.auth_views.login, name='login'),

Test
----

To set up the virtualenv::

    virtualenv .virtualenv
    source .virtualenv/bin/activate
    pip install --extra-index-url=http://lti-adx.adelaide.edu.au/pypi/ -U -r django_adelaidex/lti/tests/pip.txt 
    sudo find .virtualenv/lib/python2.7/site-packages -name \*.so -exec chcon -t shlib_t {} \;

Use the data fixtures to load the initial staff users list:

    ./manage.py loaddata django_adelaidex/lti/tests/fixtures/000_staff_group.json
        Installed 1 object(s) from 1 fixture(s)

To run the standalone server::

    ./manage.py runserver 0.0.0.0:8000

To create users on the standalone server::
            
    (.virtualenv)$ ./manage.py shell
        >>> from django_adelaidex.lti.models import User
        >>> student = User.objects.create_user('student', 'student@adelaide.edu.au', 'password')
        >>> superuser = User.objects.create_user('superuser', 'super@adelaide.edu.au', 'password')
        >>> superuser.is_super = True
        >>> superuser.is_staff = True
        >>> superuser.save()
        >>> staff = User.objects.create_user('staff', 'staff@adelaide.edu.au', 'password')
        >>> staff.is_staff = True
        >>> staff.save()

To run integration tests::

Integration tests are run using the selenium library, which requires a browser
to be installed.  We access this browser via an Xvfb session, configured to run
on display port :0, on address 0.0.0.0:8080.

    [root@loco ~]# sudo -u xvfb nohup /usr/bin/Xvfb :0 -screen 0 1024x768x24 &

To run the tests::

    python manage.py test

To check coverage::

    coverage run --include=django_adelaidex/*  python manage.py test     

    Name                                                Stmts   Miss  Cover
    -----------------------------------------------------------------------
    django_adelaidex/__init__                               2      0   100%
    django_adelaidex/lti/__init__                           0      0   100%
    django_adelaidex/lti/context_processors                 9      0   100%
    django_adelaidex/lti/middleware                        10      0   100%
    django_adelaidex/lti/migrations/0001_initial            8      0   100%
    django_adelaidex/lti/migrations/__init__                0      0   100%
    django_adelaidex/lti/models                            67      0   100%
    django_adelaidex/lti/tests/__init__                     0      0   100%
    django_adelaidex/lti/tests/settings                    22      0   100%
    django_adelaidex/lti/tests/test_contextprocessors      22      0   100%
    django_adelaidex/lti/tests/test_integration           317      3    99%
    django_adelaidex/lti/tests/test_middleware             42      0   100%
    django_adelaidex/lti/tests/test_models                122      0   100%
    django_adelaidex/lti/tests/test_views                 294      0   100%
    django_adelaidex/lti/tests/urls                         6      0   100%
    django_adelaidex/lti/urls                               4      0   100%
    django_adelaidex/lti/views                            106      5    95%
    -----------------------------------------------------------------------
    TOTAL                                                1031      8    99%

Build
-----

To build the pip package::

    python setup.py sdist
