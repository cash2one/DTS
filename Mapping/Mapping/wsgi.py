"""
WSGI config for Mapping project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""
import sys
import os
reload(sys)
sys.setdefaultencoding('utf8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Mapping.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from analyse.mapping_thread import mails
mails()
