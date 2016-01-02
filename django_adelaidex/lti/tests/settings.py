# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Placeholder settings, for use when running tests.
SECRET_KEY = 'notagoodsecret'

# Runs via ./manage.py test
DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ['*']
STATIC_URL = '/static/'
LOGIN_URL = 'login'

from django.core.urlresolvers import reverse_lazy
LOGIN_REDIRECT_URL = reverse_lazy('home')

# Avoid logging warning from django_auth_lti.middleware
LOGGING_CONFIG_FILE = os.path.join(BASE_DIR, 'tests', 'logging.conf')
from logging import config as logging_config
logging_config.fileConfig(LOGGING_CONFIG_FILE)

DATABASES = {
    'default': {
         'ENGINE': 'django.db.backends.sqlite3',
         'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    'django_adelaidex.util', # for django_adelaidex.util.templatetags.dict_filters
    'django_adelaidex.lti',
)   

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_auth_lti.middleware.LTIAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_adelaidex.lti.middleware.TimezoneMiddleware',
)

TIME_ZONE = 'UTC'

AUTH_USER_MODEL = 'lti.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'tests', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django_adelaidex.lti.context_processors.lti_settings',
                'django_adelaidex.lti.context_processors.disqus_settings',
                'django_adelaidex.lti.context_processors.disqus_sso',
            ],
        },
    },
]

FIXTURE_DIRS = (
    os.path.join(BASE_DIR, 'tests', 'fixtures'),
)

ROOT_URLCONF = 'django_adelaidex.lti.tests.urls'
