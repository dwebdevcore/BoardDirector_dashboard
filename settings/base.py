# -*- coding: utf-8 -*-
from collections import OrderedDict

import os
import urlparse

try:
    from .env import apply_environment

    apply_environment()
except ImportError:
    pass

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def rel(*x):
    return os.path.join(PROJECT_DIR, *x)


os.sys.path.insert(0, rel('apps'))
os.sys.path.insert(0, rel('libs'))

DOMAIN = os.environ.get('DOMAIN')

DEBUG = False

EMAIL_HOST = 'smtp.mandrillapp.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'Board Director'
EMAIL_USE_TLS = True

ADMINS = (
    ('Barrick Michael', 'michaelbarrick@boarddirector.co'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'boarddocuments_db',
        'USER': 'ubuntu',
    }
}

if 'DATABASE_URL' in os.environ:
    # Parse database configuration from $DATABASE_URL
    import dj_database_url

    DATABASES['default'] = dj_database_url.config()

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'common.context_processors.membership',
                'common.context_processors.trial_period',
                'common.context_processors.chameleon',
                'common.context_processors.tidio',
                'customer_io.context_processors.access_keys',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.eggs.Loader',
            ]
        },
    },
]

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SSL_ON = os.environ.get('SSL_ON')

SESSION_COOKIE_HTTPONLY = True

if SSL_ON:
    SECURE_PROXY_SSL_HEADER = ('', '')
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    EMAIL_CHANGE_USE_HTTPS = True

ALLOWED_HOSTS = [DOMAIN]

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = rel('public', 'media')

MEDIA_URL = '/media/'

STATIC_ROOT = rel('public', 'static')

STATIC_URL = '/static/'

LIBRE_OFFICE_BINARY = 'soffice'

STATICFILES_DIRS = [
    rel('apps', 'common', 'static'),
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

SECRET_KEY = '7&W$5t4rtg53RTEW%$^#4535764yzems*1^scad0-k-q$-(g5d'

MIDDLEWARE = (
    'common.middleware.ForceSSLMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'common.middleware.TimezoneMiddleware',
    'common.middleware.CurrentAccountMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'common.middleware.CatchSocialException',
)

ROOT_URLCONF = 'common.urls'

WSGI_APPLICATION = 'wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'common.static_files.NoNodeStaticFilesConfig',
    'django.contrib.admin',
    'django.contrib.flatpages',

    # libs
    'sorl.thumbnail',
    'change_email',
    'mptt',
    'compressor',
    'social_django',
    'rest_framework',
    'rest_framework_swagger',

    # apps
    'accounts',
    'billing',
    'boardcalendar',
    'committees',
    'common',
    'documents',
    'meetings',
    'profiles',
    'registration',
    'dashboard',
    'news',
    'rsvp',
    'permissions',
    'customer_io',  # "customerio" is official lib for the customer.io API
    'voting',
)

AVATAR_UPLOAD_ROOT_TEMPLATE = '{instance_id_hash}/{filename_hash}{ext}'
AVATAR_CROPS_UPLOAD_ROOT_TEMPLATE = 'crops/{filename}-{crop_name}{ext}'
STATICFILES_STORAGE = 'common.static_files.MercifulManifestStaticFilesStorage'

USE_S3 = False
if not DEBUG and 'AWS_STORAGE_BUCKET_NAME' in os.environ:
    INSTALLED_APPS += ('storages',)
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    DEFAULT_FILE_STORAGE = 'common.storage_backends.StableS3BotoStorage'
    AVATAR_UPLOAD_ROOT_TEMPLATE = 'uploads/avatars/{instance_id_hash}/{filename_hash}{ext}'
    AVATAR_CROPS_UPLOAD_ROOT_TEMPLATE = 'uploads/avatars/crops/{filename}-{crop_name}{ext}'
    S3_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
    STATIC_URL = S3_URL
    USE_S3 = True
    AWS_S3_SECURE_URLS = True

# Configure avatare path settings
AVATAR_ROOT = os.path.join(MEDIA_ROOT, 'avatars')
AVATAR_URL = os.path.join(MEDIA_URL, 'avatars/')

DEFAULT_AVATAR = rel('apps', 'common', 'static', 'images', 'default_avatar.png')
DEFAULT_AVATAR_URL = urlparse.urljoin(STATIC_URL, 'images/default_avatar.png')
DEFAULT_LIST_AVATAR = rel('apps', 'common', 'static', 'images', 'default_list_avatar.png')
DEFAULT_LIST_AVATAR_URL = urlparse.urljoin(STATIC_URL, 'images/default_list_avatar.png')

# Configure django registration
DEFAULT_FROM_EMAIL = 'Board Director <info@boarddirector.co>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
DONOTREPLY_FROM_EMAIL = 'Board Director <donotreply@boarddirector.co>'


# Chameleon
CHAMELEON_ENABLED = True

# Tidio chat
TIDIO_ENABLED = True

# User settings
AUTH_USER_MODEL = 'profiles.User'

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.twitter.TwitterOAuth',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.linkedin.LinkedinOAuth2',

    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/accounts/'

ACCOUNT_ACTIVATION_DAYS = 7
AUTH_USER_EMAIL_UNIQUE = True
TRIAL_PERIOD = 21
DASHBOARD_MEETINGS_COUNT = 65

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# Some proxying to localhost like Vagrant Share or ngrok - when you need to expose files to web.
DEV_EXTERNAL_DOMAIN = None

# Social config
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',  # Enabled

    # Create a user account if we haven't found one yet.
    'registration.social.redirect_new_user_to_registration',

    # 'social_core.pipeline.user.create_user',

    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',

    'social_core.pipeline.user.user_details',
]

SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = ['is_frame', 'login_back']
SOCIAL_AUTH_INACTIVE_USER_URL = 'registration_complete'
SOCIAL_AUTH_LOGIN_ERROR_URL = 'login_error'
# SOCIAL_RAISE_EXCEPTIONS = True

# Social keys.
# Use https://local.boarddirector.co:8000/ for local keys (alias it in hosts file)
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    'access_type': 'offline',
    'approval_prompt': 'auto'
}
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email'
]


SOCIAL_MAPPING = OrderedDict()
SOCIAL_MAPPING['google-oauth2'] = {
    'name': 'Google Plus',
    'icon': 'social-google',
    'fa_icon': 'google'
}

SOCIAL_MAPPING['linkedin-oauth2'] = {
    'name': 'Linkedin',
    'icon': 'social-linkedin',
    'fa_icon': 'linkedin',
}

SOCIAL_MAPPING['facebook'] = {
    'name': 'Facebook',
    'icon': 'social-facebook',
    'fa_icon': 'facebook',
}

SOCIAL_MAPPING['twitter'] = {
    'name': 'Twitter',
    'icon': 'social-twitter',
    'fa_icon': 'twitter',
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'common.restauth.authentication.RestTokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'common.api.exception_handler.custom_exception_handler',
}

REST_TOKEN_MAX_AGE_DAYS = 30

try:
    from .local import *
except ImportError:
    pass
