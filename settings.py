# Django settings for brightmap project.
DEBUG = True
TEMPLATE_DEBUG = DEBUG
AUTHNET_DEBUG  = DEBUG
SERVER = None

# Brightmap specific whether to actually send emails.
if DEBUG:
    SEND_EMAIL    = False
else:
    SEND_EMAIL    = True
    
MAX_SPONSORS  = 2       # The maximum number of sponsor per organizer
MAX_TRIALS    = 1       # The maximum number of tials a user may have
MAX_MAIL_SEND = 3       # The maximum number of emails sent to a person per event

SPREADSHEET   = 'BrightMap Addresses - Prod'

# Sys Admin
ADMINS = (
     ('PeteD', 'pete@brightmap.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME'    : 'bm_prod',               # Or path to database file if using sqlite3.
        'USER'    : 'bm_prod',               # Not used with sqlite3.
        'PASSWORD': '8jcgjg93j',             # Not used with sqlite3.
        'HOST'    : '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT'    : '',                      # Set to empty string for default. Not used with sqlite3.
        
        'STORAGE_ENGINE': 'MyISAM'           # Default storage engine for South
    }
}

MEETUP = {
    'APP_SECRET'  :'eajnk9f4lvuoaac5hl4lpdc0rr',
    'API_KEY'     :'u1h5ch0cgjsv5p8ogj6f4hsoj7',
}

# The callback for OAuth2 on Eventbright is specific to the server
if SERVER == "RACKSPACE":
    EVENTBRITE = {
                  'APP_KEY'       :'MDlmYmM4OTNiNDAx',    # Eventbrite APP_KEY
                  'APP_SECRET'    :'EIYMDWGITNM6H2QHRLH4N6IA67RKMDIJYERXK64LJXG5CU2BNV',
                  'API_KEY'       :'T3PVH7U55PMT5L7WHA'
    }
elif SERVER == 'AMAZON':
    EVENTBRITE = {
                  'APP_KEY'       :'MDlmYmM4OTNiNDAx',    # Eventbrite APP_KEY
                  'APP_SECRET'    :'XGRUNGDWFUZJXEVZMUJFTU3WEH3T7ZIL7QL6GJN23RL5IGLHQQ',
                  'API_KEY'       :'V7AHHVDPGJFRFYXIWP'
    }
else:
    EVENTBRITE = {
                  'APP_KEY'       :'MDlmYmM4OTNiNDAx',    # Eventbrite APP_KEY
                  'APP_SECRET'    :'JRCND6ZOQ7FBVHBRCNRLC62J6EFTNIL67MJMXVSVR3RYLUXTSL',
                  'API_KEY'       :'ZNCYQDFW5U5PWRMSG6'
    }


# Amazon Mail API, we don't use it but we have it
AMAZON = {
    'AccessKeyId' :'AKIAJCK3GLV6WBISCSXA',
    'SecretKey'   :'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'
}



AUTHORIZE = {
    'API_LOG_IN_ID'     :'3g4RxZd8eK',
    'TRANSACTION_ID'    :'3F48dExWA7959ey3'
}


PAYPAL = {
    'USERID'      : 'paypal_api1.brightmap.com',
    'PASSWORD'    : 'KTAJJA7GCFV5JGJ9',
    'SIGNATURE'   : 'AcUrj-xyiC9eQ3nznjzM0mGSJtPfAPKlNIrrdycEGN79iFsobze-a-Dh'
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
LOGIN_URL = SITE_BASE

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
import os.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT   = os.path.join(os.path.abspath(os.path.dirname(__file__)),'media')

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

#INTERNAL_IPS = ('127.0.0.1',)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'brightmap.urls'
AUTH_PROFILE_MODULE = 'base.Profile'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
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
    'leadb',
    'organ',
    'social',
    #'api',
    'authorize',
    'south',
)

EMAIL_HOST          = 'smtp.sendgrid.net'
EMAIL_PORT          = 587
EMAIL_HOST_USER     = 'brightmap'
EMAIL_HOST_PASSWORD = '8jcgjg93j'
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
        },
        'main': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler', # set the logging class to log to a file
            'filename': 'main.log'        # log file
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'main.py': {
            'handlers': ['main'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}
