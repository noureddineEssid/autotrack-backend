"""
Celery tasks for automatic reminders
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from .models import Reminder, NotificationPreference
from maintenances.models import Maintenance
from documents.models import Document
from diagnostics.models import Diagnostic


@shared_task
def check_and_create_maintenance_reminders():
    """
    Check for upcoming maintenances and create reminders
    """
    from users.models import User
    
    users = User.objects.all()
    reminders_created = 0
    
    for user in users:
        # Get user preferences
        try:
            prefs = user.notification_preferences
        except NotificationPreference.DoesNotExist:
            prefs = NotificationPreference.objects.create(user=user)
        
        if not prefs.maintenance_reminders:
            continue
        
        # Get upcoming maintenances
        remind_date = timezone.now() + timedelta(days=prefs.days_before_maintenance)
        maintenances = Maintenance.objects.filter(
            user=user,
            status='scheduled',
            date__lte=remind_date.date(),
            date__gte=timezone.now().date()
        )
        
        for maintenance in maintenances:
            # Check if reminder already exists
            existing = Reminder.objects.filter(
                user=user,
                maintenance=maintenance,
                status__in=['pending', 'sent']
            ).exists()
            
            if not existing:
                Reminder.objects.create(
                    user=user,
                    reminder_type='maintenance',
                    title=f"Entretien prévu: {maintenance.maintenance_type}",
                    message=f"Vous avez un entretien prévu le {maintenance.date.strftime('%d/%m/%Y')} pour {maintenance.vehicle.make} {maintenance.vehicle.model}",
                    priority='high' if (maintenance.date - timezone.now().date()).days <= 3 else 'medium',
                    vehicle=maintenance.vehicle,
                    maintenance=maintenance,
                    remind_at=timezone.now()
                )
                reminders_created += 1
    
    return f"Created {reminders_created} maintenance reminders"


@shared_task
def check_and_create_document_expiry_reminders():
    """
    Check for expiring documents and create reminders
    """
    from users.models import User
    
    users = User.objects.all()
    reminders_created = 0
    
    for user in users:
        # Get user preferences
        try:
            prefs = user.notification_preferences
        except NotificationPreference.DoesNotExist:
            prefs = NotificationPreference.objects.create(user=user)
        
        if not prefs.document_expiry_reminders:
            continue
        
        # Get expiring documents
        remind_date = timezone.now() + timedelta(days=prefs.days_before_document_expiry)
        documents = Document.objects.filter(
            user=user,
            expiry_date__lte=remind_date.date(),
            expiry_date__gte=timezone.now().date()
        )
        
        for document in documents:
            # Check if reminder already exists
            existing = Reminder.objects.filter(
                user=user,
                document=document,
                status__in=['pending', 'sent']
            ).exists()
            
            if not existing:
                days_until_expiry = (document.expiry_date - timezone.now().date()).days
                priority = 'urgent' if days_until_expiry <= 7 else 'high' if days_until_expiry <= 30 else 'medium'
                
                Reminder.objects.create(
                    user=user,
                    reminder_type='document_expiry',
                    title=f"Document expirant: {document.document_type}",
                    message=f"Votre {document.document_type} pour {document.vehicle.make} {document.vehicle.model} expire le {document.expiry_date.strftime('%d/%m/%Y')}",
                    priority=priority,
                    vehicle=document.vehicle,
                    document=document,
                    remind_at=timezone.now()
                )
                reminders_created += 1
    
    return f"Created {reminders_created} document expiry reminders"


@shared_task
def check_and_create_diagnostic_reminders():
    """
    Check for unresolved diagnostics and create reminders
    """
    from users.models import User
    
    users = User.objects.all()
    reminders_created = 0
    
    for user in users:
        # Get user preferences
        try:
            prefs = user.notification_preferences
        except NotificationPreference.DoesNotExist:
            prefs = NotificationPreference.objects.create(user=user)
        
        if not prefs.diagnostic_reminders:
            continue
        
        # Get critical unresolved diagnostics older than 7 days
        critical_date = timezone.now() - timedelta(days=7)
        diagnostics = Diagnostic.objects.filter(
            user=user,
            resolved=False,
            severity__in=['critical', 'high'],
            date__lte=critical_date.date()
        )
        
        for diagnostic in diagnostics:
            # Check if reminder already exists recently
            existing = Reminder.objects.filter(
                user=user,
                diagnostic=diagnostic,
                status__in=['pending', 'sent'],
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if not existing:
                Reminder.objects.create(
                    user=user,
                    reminder_type='diagnostic_followup',
                    title=f"Diagnostic non résolu: {diagnostic.diagnostic_code}",
                    message=f"Le problème {diagnostic.diagnostic_code} sur {diagnostic.vehicle.make} {diagnostic.vehicle.model} n'est toujours pas résolu depuis {diagnostic.date.strftime('%d/%m/%Y')}",
                    priority='urgent' if diagnostic.severity == 'critical' else 'high',
                    vehicle=diagnostic.vehicle,
                    diagnostic=diagnostic,
                    remind_at=timezone.now()
                )
                reminders_created += 1
    
    return f"Created {reminders_created} diagnostic reminders"


@shared_task
def send_pending_reminders():
    """
    Send all pending reminders via appropriate channels
    """
    now = timezone.now()
    pending_reminders = Reminder.objects.filter(
        status='pending',
        remind_at__lte=now
    )
    
    sent_count = 0
    
    for reminder in pending_reminders:
        try:
            prefs = reminder.user.notification_preferences
        except NotificationPreference.DoesNotExist:
            prefs = NotificationPreference.objects.create(user=reminder.user)
        
        # Check quiet hours
        if prefs.enable_quiet_hours:
            current_time = now.time()
            if prefs.quiet_hours_start <= prefs.quiet_hours_end:
                if prefs.quiet_hours_start <= current_time <= prefs.quiet_hours_end:
                    continue
            else:
                if current_time >= prefs.quiet_hours_start or current_time <= prefs.quiet_hours_end:
                    continue
        
        # Send via enabled channels
        if prefs.enable_email:
            send_email_reminder(reminder)
        
        if prefs.enable_push:
            send_push_reminder(reminder)
        
        # Mark as sent
        reminder.mark_as_sent()
        sent_count += 1
    
    return f"Sent {sent_count} reminders"


def send_email_reminder(reminder):
    """Send reminder via email"""
    try:
        send_mail(
            subject=f"[AutoTrack+] {reminder.title}",
            message=reminder.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reminder.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_push_reminder(reminder):
    """Send reminder via push notification"""
    # TODO: Implement with Firebase Cloud Messaging or OneSignal
    pass


@shared_task
def cleanup_old_reminders():
    """
    Delete old dismissed/completed reminders
    """
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted = Reminder.objects.filter(
        status__in=['dismissed', 'completed'],
        updated_at__lt=cutoff_date
    ).delete()
    
    return f"Deleted {deleted[0]} old reminders"
