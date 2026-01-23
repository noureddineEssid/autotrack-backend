"""
Tâches Celery pour AutoTrack
"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from emails.email_service import EmailService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)
email_service = EmailService()


@shared_task(name='subscriptions.check_expired_subscriptions')
def check_expired_subscriptions():
    """
    Vérifie et désactive les abonnements expirés
    Cette tâche doit être exécutée quotidiennement
    """
    from subscriptions.models import Subscription
    
    logger.info("Checking for expired subscriptions...")
    
    # Trouver les abonnements actifs qui ont expiré
    expired_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__lte=timezone.now()
    )
    
    count = 0
    for subscription in expired_subscriptions:
        # Mettre à jour le statut
        subscription.status = 'expired'
        subscription.save(update_fields=['status'])
        
        # Envoyer un email de notification
        email_service.send_subscription_expired_email(
            user=subscription.user,
            plan_name=subscription.plan.name
        )
        
        count += 1
    
    logger.info(f"Marked {count} subscriptions as expired")
    return {'expired_count': count}


@shared_task(name='subscriptions.send_renewal_reminders')
def send_renewal_reminders():
    """
    Envoie des rappels de renouvellement 7 jours avant l'expiration
    Cette tâche doit être exécutée quotidiennement
    """
    from subscriptions.models import Subscription
    
    logger.info("Sending renewal reminders...")
    
    # Date dans 7 jours
    reminder_date = timezone.now() + timedelta(days=7)
    
    # Trouver les abonnements qui expirent dans 7 jours
    upcoming_renewals = Subscription.objects.filter(
        status='active',
        end_date__date=reminder_date.date(),
        auto_renew=True
    )
    
    count = 0
    for subscription in upcoming_renewals:
        # Envoyer l'email de rappel
        email_service.send_subscription_renewal_reminder(
            user=subscription.user,
            plan_name=subscription.plan.name,
            renewal_date=subscription.end_date
        )
        
        count += 1
    
    logger.info(f"Sent {count} renewal reminders")
    return {'reminder_count': count}


@shared_task(name='maintenances.send_maintenance_reminders')
def send_maintenance_reminders():
    """
    Envoie des rappels de maintenance 3 jours avant la date prévue
    Cette tâche doit être exécutée quotidiennement
    """
    from maintenances.models import Maintenance
    
    logger.info("Sending maintenance reminders...")
    
    # Date dans 3 jours
    reminder_date = timezone.now() + timedelta(days=3)
    
    # Trouver les maintenances programmées dans 3 jours
    upcoming_maintenances = Maintenance.objects.filter(
        status='scheduled',
        scheduled_date__date=reminder_date.date()
    ).select_related('vehicle', 'vehicle__user')
    
    count = 0
    for maintenance in upcoming_maintenances:
        # Calculer les jours restants
        days_left = (maintenance.scheduled_date.date() - timezone.now().date()).days
        
        # Envoyer l'email de rappel
        email_service.send_maintenance_reminder_email(
            user=maintenance.vehicle.user,
            vehicle=maintenance.vehicle,
            maintenance=maintenance,
            days_left=days_left
        )
        
        count += 1
    
    logger.info(f"Sent {count} maintenance reminders")
    return {'reminder_count': count}


@shared_task(name='documents.cleanup_old_documents')
def cleanup_old_documents():
    """
    Nettoie les documents marqués pour suppression il y a plus de 30 jours
    Cette tâche doit être exécutée hebdomadairement
    """
    from documents.models import Document
    
    logger.info("Cleaning up old deleted documents...")
    
    # Date il y a 30 jours
    deletion_threshold = timezone.now() - timedelta(days=30)
    
    # Trouver les documents à supprimer définitivement
    # Note: Nécessite un champ 'deleted_at' dans le modèle Document
    old_documents = Document.objects.filter(
        deleted_at__lte=deletion_threshold,
        deleted_at__isnull=False
    )
    
    count = old_documents.count()
    
    # Supprimer les fichiers et les enregistrements
    for document in old_documents:
        if document.file:
            document.file.delete(save=False)
        document.delete()
    
    logger.info(f"Cleaned up {count} old documents")
    return {'cleaned_count': count}


@shared_task(name='notifications.cleanup_old_notifications')
def cleanup_old_notifications():
    """
    Archive les notifications lues de plus de 90 jours
    Cette tâche doit être exécutée hebdomadairement
    """
    from notifications.models import Notification
    
    logger.info("Cleaning up old read notifications...")
    
    # Date il y a 90 jours
    cleanup_threshold = timezone.now() - timedelta(days=90)
    
    # Trouver les notifications lues anciennes
    old_notifications = Notification.objects.filter(
        is_read=True,
        read_at__lte=cleanup_threshold
    )
    
    count = old_notifications.count()
    old_notifications.delete()
    
    logger.info(f"Cleaned up {count} old notifications")
    return {'cleaned_count': count}


@shared_task(name='health.check_system_health')
def check_system_health():
    """
    Vérifie la santé du système et envoie des alertes si nécessaire
    Cette tâche doit être exécutée toutes les heures
    """
    from django.db import connection
    import stripe
    from django.conf import settings
    
    logger.info("Checking system health...")
    
    health_status = {
        'database': False,
        'stripe': False,
        'timestamp': timezone.now().isoformat()
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['database'] = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check Stripe
    try:
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Price.list(limit=1)
            health_status['stripe'] = True
    except Exception as e:
        logger.error(f"Stripe health check failed: {str(e)}")
    
    # Si tout est OK
    if all(health_status.values()):
        logger.info("System health check: All systems operational")
    else:
        logger.warning(f"System health check: Issues detected - {health_status}")
    
    return health_status


@shared_task(name='users.cleanup_inactive_sessions')
def cleanup_inactive_sessions():
    """
    Nettoie les sessions expirées
    Cette tâche doit être exécutée quotidiennement
    """
    from users.models import Session
    
    logger.info("Cleaning up inactive sessions...")
    
    # Supprimer les sessions expirées
    expired_sessions = Session.objects.filter(
        expires_at__lte=timezone.now()
    )
    
    count = expired_sessions.count()
    expired_sessions.delete()
    
    logger.info(f"Cleaned up {count} expired sessions")
    return {'cleaned_count': count}
