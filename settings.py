# Django settings for brightmap project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('PeteD', 'pete@brightmap.com'),
)

MANAGERS = ADMINS
"""
DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME'    : 'brightmap',                # Or path to database file if using sqlite3.
        'USER'    : 'PeteD',                    # Not used with sqlite3.
        'PASSWORD': 'g00dd0g',                  # Not used with sqlite3.
        'HOST'    : 'firstinstance.cfbsndnshc5a.us-east-1.rds.amazonaws.com',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT'    : '3306',                     # Set to empty string for default. Not used with sqlite3.
    }
}
"""
DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME'    : 'brightmap',             # Or path to database file if using sqlite3.
        'USER'    : 'brightmap',             # Not used with sqlite3.
        'PASSWORD': '$m0ney',                # Not used with sqlite3.
        'HOST'    : '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT'    : '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

MEETUP = {
    'APP_SECRET'  :'eajnk9f4lvuoaac5hl4lpdc0rr',
    'API_KEY'     :'u1h5ch0cgjsv5p8ogj6f4hsoj7',
}

EVENTBRITE = {
    'APP_KEY'       :'MDlmYmM4OTNiNDAx',    # Eventbrite APP_KEY
}

AMAZON = {
    'AccessKeyId' :'AKIAJCK3GLV6WBISCSXA',
    'SecretKey'   :'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'
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1
SITE_NAME = 'localhost:8000'
SITE_BASE = 'http://'+SITE_NAME

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
import os.path
MEDIA_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)),'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)),'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'x3gs0huqv%tu@+m5fz_%^s%i-agk0+*%mmok7a=sgrc*=(48_d'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'brightmap.urls'
AUTH_PROFILE_MODULE = 'base.Profile'

TEMPLATE_DIRS = (
    MEDIA_ROOT
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'base',
    'south'
)

EMAIL_HOST          = 'in.mailjet.com'
EMAIL_PORT          = 25
EMAIL_HOST_USER     = 'd21668dd0d4bb01c19f3845e45cfa5a3'
EMAIL_HOST_PASSWORD = 'fa2934689303dcab990c72d0838c6ef1'
EMAIL_USE_TL        = True


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
