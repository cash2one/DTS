#coding:utf-8
"""
Django settings for Mapping project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
#from __future__ import absolute_import
import os
import sys
import djcelery
djcelery.setup_loader()
from kombu import Exchange,Queue
# from .. import analyse
BROKER_URL = 'redis://127.0.0.1:6379/11'
CELERYD_FORCE_EXECV = True  
CELERY_IGNORE_RESULT = True   
CELERY_DISABLE_RATE_LIMITS = True
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'Asia/Shanghai' 

CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('taskfor_wait', Exchange('taskfor_wait'), routing_key='taskfor_wait'),
    Queue('taskfor_ice', Exchange('taskfor_ice'), routing_key='taskfor_ice'),
    Queue('taskfor_hx', Exchange('taskfor_hx'), routing_key='taskfor_hx'),
)

CELERY_ROUTES = {
    'analyse.tasks.wait': {'queue': 'taskfor_wait', 'routing_key': 'taskfor_wait'},
    'analyse.tasks.for_ice': {'queue': 'taskfor_ice', 'routing_key': 'taskfor_ice'},
    'analyse.tasks.for_hx': {'queue': 'taskfor_hx', 'routing_key': 'taskfor_hx'},
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'jc583z&l=$nqful=f0)uggnzzha02s&530!k^++6xi5e!_b82k'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['192.168.162.108', 'dts1.100credit.com', '127.0.0.1', 'localhost']

LOGIN_URL = '/accounts/login/'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'account',
    'analyse',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.BlockedIpMiddleware',
)

ROOT_URLCONF = 'Mapping.urls'

SESSION_COOKIE_AGE = 60 * 60 * 24

WSGI_APPLICATION = 'Mapping.wsgi.application'

MAIL = 'dts@100credit.com'

MAIL_PASSWD = '018660'

MAIL_URL="http://192.168.23.108:8003/als/custom/mail/"

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Map',
        'USER': 'map',
        'PASSWORD': 'map',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'zh-cn'

SITE_ID = 1

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = False

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

DATETIME_FORMAT = 'Y-n-j H:i:s'
DATE_FORMAT = 'Y-n-j'

#STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = '/opt/django_project/all_file/DTS/media/'
MEDIA_URL = '/media/'


SESSION_COOKIE_AGE= 60 * 60 * 2


STATICFILES_DIRS = (
    (os.path.join(BASE_DIR,'static')),
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

FILE_UPLOAD_HANDLERS = (
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)

LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(asctime)s: %(message)s'
                }
            },
        'filters': {
            },
        'handlers': {
            'daserr': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/opt/django_project/all_file/DTS/log/err.log',
                #'filename': os.path.join(os.path.dirname(BASE_DIR), 'log/err.log'),
                'maxBytes': 1024*1024*5,
                'backupCount': 5,
                'formatter': 'verbose',
                },
            'behavior': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/opt/django_project/all_file/DTS/log/behavor.log',
                #'filename': os.path.join(os.path.dirname(BASE_DIR), 'log/err.log'),
                'maxBytes': 1024*1024*5,
                'backupCount': 5,
                'formatter': 'verbose',
                }
            },
        'loggers': {
            'daserr': {
                'handlers': ['daserr'],
                'level': 'ERROR',
                },
            'behavior': {
                'handlers': ['behavior'],
                'level': 'ERROR',
                },

            }
        }


MY_TMP_PATH = '/opt/django_project/all_file/DTS/tmp/'
