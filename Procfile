web: sh -c 'cd socialsink && gunicorn socialsink.wsgi:application --log-file - --log-level debug'
python manage.py collectstatic --noinput
manage.py migrate
