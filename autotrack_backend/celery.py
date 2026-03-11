import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotrack_backend.settings')

app = Celery('autotrack_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Celery Beat Schedule - Tâches périodiques
app.conf.beat_schedule = {
    # Nettoyer anciennes sessions - tous les jours à 02:00
    'clean-expired-sessions': {
        'task': 'users.tasks.clean_expired_sessions',
        'schedule': crontab(hour=2, minute=0),
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
