"""
Celery tasks for booking notifications
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Booking


@shared_task
def send_booking_confirmation_email(booking_id):
    """Send booking confirmation email to customer"""
    try:
        booking = Booking.objects.select_related('garage', 'vehicle', 'service').get(id=booking_id)
        
        subject = f'Confirmation de réservation - {booking.garage.name}'
        
        message = f"""
        Bonjour {booking.customer_name},

        Votre réservation a été créée avec succès !

        Détails:
        - Garage: {booking.garage.name}
        - Adresse: {booking.garage.address}
        - Service: {booking.service.name if booking.service else 'Non spécifié'}
        - Date: {booking.booking_date.strftime('%d/%m/%Y')}
        - Heure: {booking.booking_time.strftime('%H:%M')}
        - Véhicule: {booking.vehicle.brand} {booking.vehicle.model} ({booking.vehicle.registration_number})
        - Prix estimé: {booking.estimated_price}€

        Statut: En attente de confirmation par le garage

        Notes: {booking.notes or 'Aucune'}

        Pour toute question, contactez le garage au: {booking.garage.phone}

        Cordialement,
        L'équipe AutoTrack
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer_email],
            fail_silently=False,
        )
        
        return f"Email de confirmation envoyé pour la réservation {booking_id}"
    except Booking.DoesNotExist:
        return f"Réservation {booking_id} introuvable"
    except Exception as e:
        return f"Erreur lors de l'envoi de l'email: {str(e)}"


@shared_task
def send_booking_confirmed_email(booking_id):
    """Send email when booking is confirmed by garage"""
    try:
        booking = Booking.objects.select_related('garage', 'vehicle', 'service').get(id=booking_id)
        
        subject = f'Réservation confirmée - {booking.garage.name}'
        
        message = f"""
        Bonjour {booking.customer_name},

        Bonne nouvelle ! Votre réservation a été CONFIRMÉE par le garage.

        Détails:
        - Garage: {booking.garage.name}
        - Adresse: {booking.garage.address}
        - Date: {booking.booking_date.strftime('%d/%m/%Y')}
        - Heure: {booking.booking_time.strftime('%H:%M')}
        - Service: {booking.service.name if booking.service else 'Non spécifié'}
        - Véhicule: {booking.vehicle.brand} {booking.vehicle.model}

        N'oubliez pas de vous présenter à l'heure !

        En cas d'imprévu, vous pouvez annuler jusqu'à 24h avant le rendez-vous.

        Cordialement,
        L'équipe AutoTrack
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer_email],
            fail_silently=False,
        )
        
        return f"Email de confirmation envoyé pour la réservation {booking_id}"
    except Exception as e:
        return f"Erreur: {str(e)}"


@shared_task
def send_booking_reminder_email(booking_id):
    """Send reminder email 24h before appointment"""
    try:
        booking = Booking.objects.select_related('garage', 'vehicle', 'service').get(id=booking_id)
        
        if booking.reminder_sent:
            return f"Rappel déjà envoyé pour {booking_id}"
        
        subject = f'Rappel: Rendez-vous demain - {booking.garage.name}'
        
        message = f"""
        Bonjour {booking.customer_name},

        Rappel de votre rendez-vous DEMAIN:

        - Garage: {booking.garage.name}
        - Adresse: {booking.garage.address}
        - Heure: {booking.booking_time.strftime('%H:%M')}
        - Service: {booking.service.name if booking.service else 'Non spécifié'}
        - Véhicule: {booking.vehicle.brand} {booking.vehicle.model}

        Pensez à arriver 5 minutes en avance.

        Contact garage: {booking.garage.phone}

        À demain !
        L'équipe AutoTrack
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer_email],
            fail_silently=False,
        )
        
        # Mark reminder as sent
        booking.reminder_sent = True
        from django.utils import timezone
        booking.reminder_sent_at = timezone.now()
        booking.save()
        
        return f"Rappel envoyé pour {booking_id}"
    except Exception as e:
        return f"Erreur: {str(e)}"


@shared_task
def send_booking_completed_email(booking_id):
    """Send completion email with review request"""
    try:
        booking = Booking.objects.select_related('garage', 'vehicle', 'service').get(id=booking_id)
        
        subject = f'Merci ! Donnez votre avis - {booking.garage.name}'
        
        message = f"""
        Bonjour {booking.customer_name},

        Votre rendez-vous chez {booking.garage.name} est terminé.

        Prix final: {booking.final_price}€

        Nous espérons que tout s'est bien passé !

        Aidez-nous à améliorer nos services en donnant votre avis sur cette intervention.
        Connectez-vous à votre espace client pour laisser une évaluation.

        Merci de votre confiance,
        L'équipe AutoTrack
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer_email],
            fail_silently=False,
        )
        
        return f"Email de fin envoyé pour {booking_id}"
    except Exception as e:
        return f"Erreur: {str(e)}"


@shared_task
def send_booking_cancelled_email(booking_id):
    """Send cancellation confirmation email"""
    try:
        booking = Booking.objects.select_related('garage', 'vehicle').get(id=booking_id)
        
        subject = f'Annulation confirmée - {booking.garage.name}'
        
        message = f"""
        Bonjour {booking.customer_name},

        Votre réservation a été ANNULÉE.

        Détails de la réservation annulée:
        - Garage: {booking.garage.name}
        - Date: {booking.booking_date.strftime('%d/%m/%Y')}
        - Heure: {booking.booking_time.strftime('%H:%M')}
        - Véhicule: {booking.vehicle.brand} {booking.vehicle.model}

        Raison: {booking.cancellation_reason or 'Non spécifiée'}

        Vous pouvez prendre un nouveau rendez-vous à tout moment.

        Cordialement,
        L'équipe AutoTrack
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer_email],
            fail_silently=False,
        )
        
        return f"Email d'annulation envoyé pour {booking_id}"
    except Exception as e:
        return f"Erreur: {str(e)}"


@shared_task
def send_daily_reminders():
    """Send reminders for bookings in 24 hours (run daily at 10am)"""
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    bookings_to_remind = Booking.objects.filter(
        booking_date=tomorrow,
        status__in=['confirmed'],
        reminder_sent=False
    )
    
    count = 0
    for booking in bookings_to_remind:
        send_booking_reminder_email.delay(str(booking.id))
        count += 1
    
    return f"{count} rappels envoyés pour demain"
