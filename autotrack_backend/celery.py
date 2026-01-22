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
    # Vérifier les abonnements expirés - tous les jours à 00:00
    'check-expired-subscriptions': {
        'task': 'subscriptions.tasks.check_expired_subscriptions',
        'schedule': crontab(hour=0, minute=0),
    },
    # Envoyer rappels renouvellement - tous les jours à 09:00
    'send-renewal-reminders': {
        'task': 'subscriptions.tasks.send_renewal_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    # Mettre à jour statuts abonnements - toutes les heures
    'update-subscription-statuses': {
        'task': 'subscriptions.tasks.update_subscription_statuses',
        'schedule': crontab(minute=0),  # Toutes les heures à la minute 0
    },
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
