django\_adelaidex.lti
====================

LTI integration used by the AdelaideX Django applications.

Usage
-----

1. Update your user model::

        AUTH_USER_MODEL = 'lti.User'

*Note:* This is a pretty drastic to an existing application, but can be done relatively easily in a new application.  See [Django Topics :: Authentication : Substituting a Custom User Model](https://docs.djangoproject.com/en/1.9/topics/auth/customizing/#substituting-a-custom-user-model) for details.

2. You can use django_adelaidex.lti.models.Cohort instances to define your LTI integration, or
   `settings.ADELAIDEX_LTI`, e.g.:

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

3. Add `django_adelaidex.lti` to your `settings.INSTALLED_APPS`.

        INSTALLED_APPS = (
            ...
            'django_adelaidex.util', # for django_adelaidex.util.templatetags.dict_filters
            'django_adelaidex.lti',
        )

4. Add `django_adelaidex.lti.middleware` to `settings.MIDDLEWARE_CLASSES`.

        MIDDLEWARE_CLASSES = (
            ...
            'django_auth_lti.middleware.LTIAuthMiddleware',
            'django_adelaidex.lti.middleware.TimezoneMiddleware',
        )

5. Add `django_adelaidex.lti.context_processors` to `settings.TEMPLATES`:

        TEMPLATES = [
        {
         ...
            'OPTIONS': {
                'context_processors': [
                    'django.core.context_processors.request', # required by _profile.html
                    'django_adelaidex.lti.context_processors.lti_settings',
                    ...
                ],
            },
        )

6. Include the `django_adelaidex.lti.urls` in your project's `urls.urlpatterns`, e.g.,

        urlpatterns = [
            ...
            url(r'^lti/', include('django_adelaidex.lti.urls')),
        ]

7. Optionally configure overriding your default 'login' url with our 403 page,
   to disallow normal Django user authentication when running under LTI mode, e.g.::

        # in settings.py
        LOGIN_URL='login'

        # in urls.py
        if getattr(settings, 'ADELAIDEX_LTI', {}).get('LOGIN_URL'):
            urlpatterns.append(url(r'^login/$',
                               LTIPermissionDeniedView.as_view(),
                               name='login'))
        else:
            urlpatterns.append(url(r'^login/$',
                               auth_views.login,
                               kwargs={'template_name': 'login.html'},
                               name='login'))
Test
----

To set up the virtualenv::

    virtualenv .virtualenv
    source .virtualenv/bin/activate
    pip install --extra-index-url=https://lti-adx.adelaide.edu.au/pypi/ -U -r django_adelaidex/lti/tests/pip.txt 
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

    ./manage.py test

To check coverage::

    coverage run --include=django_adelaidex/*  ./manage.py test     
    Name                                                         Stmts   Miss  Cover
    --------------------------------------------------------------------------------
    django_adelaidex/__init__.py                                     2      0   100%
    django_adelaidex/lti/__init__.py                                 0      0   100%
    django_adelaidex/lti/admin.py                                   10      0   100%
    django_adelaidex/lti/backends.py                                84      9    89%
    django_adelaidex/lti/context_processors.py                      44      0   100%
    django_adelaidex/lti/middleware.py                              18      0   100%
    django_adelaidex/lti/migrations/0001_initial.py                  8      0   100%
    django_adelaidex/lti/migrations/0002_auto_20151230_1212.py       6      0   100%
    django_adelaidex/lti/migrations/0003_cohort.py                   6      0   100%
    django_adelaidex/lti/migrations/0004_user_cohort.py              5      0   100%
    django_adelaidex/lti/migrations/0005_auto_20151023_1224.py       7      0   100%
    django_adelaidex/lti/migrations/0006_cohort_is_default.py        6      0   100%
    django_adelaidex/lti/migrations/0007_auto_20160121_1051.py       6      0   100%
    django_adelaidex/lti/migrations/__init__.py                      0      0   100%
    django_adelaidex/lti/models.py                                 121      2    98%
    django_adelaidex/lti/tests/__init__.py                           0      0   100%
    django_adelaidex/lti/tests/settings.py                          22      0   100%
    django_adelaidex/lti/tests/test_contextprocessors.py            85      0   100%
    django_adelaidex/lti/tests/test_integration.py                 682      0   100%
    django_adelaidex/lti/tests/test_middleware.py                   94      0   100%
    django_adelaidex/lti/tests/test_models.py                      190      0   100%
    django_adelaidex/lti/tests/test_views.py                       329      0   100%
    django_adelaidex/lti/tests/urls.py                              12      0   100%
    django_adelaidex/lti/tests/views.py                             54      1    98%
    django_adelaidex/lti/urls.py                                     4      0   100%
    django_adelaidex/lti/views.py                                  118      7    94%
    --------------------------------------------------------------------------------
    TOTAL                                                         1913     19    99%


Build
-----

To build the pip package::

    python setup.py sdist
