#!/bin/sh

uwsgi --ini mysite_uwsgi.ini > /dev/null 2>&1 &
python /home/zy/Mapping_celery/Mapping/manage.py celery worker --loglevel=info


