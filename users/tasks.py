"""
Tâches Celery pour les utilisateurs
"""
from celery import shared_task
from django.utils import timezone
from .models import Session
import logging

logger = logging.getLogger(__name__)


@shared_task
def clean_expired_sessions():
    """
    Nettoyer les sessions expirées
    Exécuté quotidiennement à 02:00
    """
    now = timezone.now()
    
    # Supprimer sessions expirées
    deleted_count, _ = Session.objects.filter(expires_at__lt=now).delete()
    
    # Désactiver sessions inactives anciennes (> 30 jours)
    old_inactive = Session.objects.filter(
        is_active=False,
        created_at__lt=now - timezone.timedelta(days=30)
    )
    inactive_count = old_inactive.count()
    old_inactive.delete()
    
    total_cleaned = deleted_count + inactive_count
    
    logger.info(
        f"Cleaned {total_cleaned} sessions "
        f"({deleted_count} expired, {inactive_count} old inactive)"
    )
    
    return f"{total_cleaned} sessions cleaned"
