"""
Tâches Celery pour les abonnements
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Subscription
from emails.email_service import EmailService
import logging

logger = logging.getLogger(__name__)
email_service = EmailService()


@shared_task
def check_expired_subscriptions():
    """
    Vérifier et désactiver les abonnements expirés
    Exécuté quotidiennement à 00:00
    """
    now = timezone.now()
    
    # Trouver abonnements actifs expirés
    expired_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__lt=now
    )
    
    count = 0
    for subscription in expired_subscriptions:
        # Mettre à jour statut
        subscription.status = 'expired'
        subscription.save(update_fields=['status'])
        
        # Logger l'expiration
        logger.info(f"Subscription {subscription.id} expired for user {subscription.user.email}")
        
        count += 1
    
    logger.info(f"Checked and updated {count} expired subscriptions")
    return f"{count} subscriptions expired"


@shared_task
def send_renewal_reminders():
    """
    Envoyer rappels de renouvellement 7 jours avant expiration
    Exécuté quotidiennement à 09:00
    """
    now = timezone.now()
    reminder_date = now + timedelta(days=7)
    
    # Trouver abonnements expirant dans 7 jours
    upcoming_expiry = Subscription.objects.filter(
        status='active',
        end_date__date=reminder_date.date(),
        auto_renew=False  # Seulement pour non auto-renew
    ).select_related('user', 'plan')
    
    count = 0
    for subscription in upcoming_expiry:
        try:
            # TODO: Créer template email de rappel renouvellement
            # Pour l'instant, log seulement
            logger.info(
                f"Renewal reminder for subscription {subscription.id} "
                f"(user: {subscription.user.email}, plan: {subscription.plan.name})"
            )
            
            # Envoyer notification in-app
            from notifications.models import Notification
            Notification.objects.create(
                user=subscription.user,
                type='subscription',
                title='Renouvellement d\'abonnement',
                message=f'Votre abonnement {subscription.plan.name} expire dans 7 jours. Pensez à le renouveler!',
                data={
                    'subscription_id': subscription.id,
                    'plan_name': subscription.plan.name,
                    'end_date': subscription.end_date.isoformat()
                }
            )
            
            count += 1
        except Exception as e:
            logger.error(f"Error sending renewal reminder for subscription {subscription.id}: {str(e)}")
    
    logger.info(f"Sent {count} renewal reminders")
    return f"{count} renewal reminders sent"


@shared_task
def update_subscription_statuses():
    """
    Mettre à jour les statuts d'abonnements
    Exécuté toutes les heures
    """
    now = timezone.now()
    updated_count = 0
    
    # 1. Activer les abonnements qui commencent maintenant
    pending_to_activate = Subscription.objects.filter(
        status='pending',
        start_date__lte=now
    )
    
    for subscription in pending_to_activate:
        subscription.status = 'active'
        subscription.save(update_fields=['status'])
        logger.info(f"Activated subscription {subscription.id}")
        updated_count += 1
    
    # 2. Marquer comme expirés les abonnements dépassés
    active_to_expire = Subscription.objects.filter(
        status='active',
        end_date__lt=now
    )
    
    for subscription in active_to_expire:
        subscription.status = 'expired'
        subscription.save(update_fields=['status'])
        logger.info(f"Expired subscription {subscription.id}")
        updated_count += 1
    
    # 3. Gérer auto-renewal (à 1 jour de l'expiration)
    tomorrow = now + timedelta(days=1)
    to_auto_renew = Subscription.objects.filter(
        status='active',
        end_date__date=tomorrow.date(),
        auto_renew=True
    ).select_related('user', 'plan')
    
    for subscription in to_auto_renew:
        try:
            # TODO: Intégrer paiement Stripe pour auto-renewal
            logger.info(
                f"Auto-renewal scheduled for subscription {subscription.id} "
                f"(user: {subscription.user.email})"
            )
            # Logique de renouvellement automatique à implémenter
        except Exception as e:
            logger.error(f"Error auto-renewing subscription {subscription.id}: {str(e)}")
    
    logger.info(f"Updated {updated_count} subscription statuses")
    return f"{updated_count} subscriptions updated"
