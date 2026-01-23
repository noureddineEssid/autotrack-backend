from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service centralisé pour l'envoi d'emails avec templates HTML
    """
    
    @staticmethod
    def send_email(subject, template_name, context, recipient_email):
        """
        Envoie un email en utilisant un template HTML
        
        Args:
            subject: Sujet de l'email
            template_name: Nom du template (sans .html)
            context: Dictionnaire de données pour le template
            recipient_email: Email du destinataire
        
        Returns:
            bool: True si envoyé avec succès, False sinon
        """
        try:
            # Ajouter les variables globales au contexte
            context.update({
                'site_name': 'AutoTrack',
                'site_url': settings.FRONTEND_URL or 'http://localhost:3000',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'current_year': 2026
            })
            
            # Générer le contenu HTML depuis le template
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
            
            # Créer l'email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Envoyer
            email.send(fail_silently=False)
            logger.info(f"Email envoyé avec succès à {recipient_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {recipient_email}: {str(e)}")
            return False
    
    @classmethod
    def send_welcome_email(cls, user):
        """Envoie l'email de bienvenue à un nouvel utilisateur"""
        return cls.send_email(
            subject='Bienvenue sur AutoTrack!',
            template_name='welcome',
            context={
                'user_name': user.first_name or user.email.split('@')[0],
                'user_email': user.email
            },
            recipient_email=user.email
        )
    
    @classmethod
    def send_otp_email(cls, user, otp_code):
        """Envoie le code OTP pour vérification"""
        return cls.send_email(
            subject='Votre code de vérification AutoTrack',
            template_name='otp',
            context={
                'user_name': user.first_name or user.email.split('@')[0],
                'otp_code': otp_code,
                'expires_in': '10 minutes'
            },
            recipient_email=user.email
        )
    
    @classmethod
    def send_password_reset_email(cls, user, reset_token):
        """Envoie l'email de réinitialisation de mot de passe"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        return cls.send_email(
            subject='Réinitialisation de votre mot de passe AutoTrack',
            template_name='password-reset',
            context={
                'user_name': user.first_name or user.email.split('@')[0],
                'reset_url': reset_url,
                'expires_in': '1 heure'
            },
            recipient_email=user.email
        )
    
    @classmethod
    def send_subscription_confirmation_email(cls, user, plan_name, amount):
        """Envoie la confirmation d'abonnement"""
        return cls.send_email(
            subject='Confirmation de votre abonnement AutoTrack',
            template_name='subscription-confirmation',
            context={
                'user_name': user.first_name or user.email.split('@')[0],
                'plan_name': plan_name,
                'amount': f"{amount}€",
                'dashboard_url': f"{settings.FRONTEND_URL}/dashboard"
            },
            recipient_email=user.email
        )
    
    @classmethod
    def send_subscription_renewal_reminder(cls, user, plan_name, renewal_date):
        """Envoie un rappel de renouvellement d'abonnement"""
        return cls.send_email(
            subject='Rappel: Renouvellement de votre abonnement AutoTrack',
            template_name='subscription-renewal',
            context={
                'user_name': user.first_name or user.email.split('@')[0],
                'plan_name': plan_name,
                'renewal_date': renewal_date.strftime('%d/%m/%Y'),
                'manage_url': f"{settings.FRONTEND_URL}/dashboard/subscription"
            },
            recipient_email=user.email
        )
    
    @classmethod
    def send_subscription_expired_email(cls, user, plan_name):
        """Envoie la notification d'expiration d'abonnement"""
        return cls.send_email(
            subject='Votre abonnement AutoTrack a expiré',
            template_name='subscription-expired',
            context={
                'user_name': user.first_name or user.email.split('@')[0],
                'plan_name': plan_name,
                'renew_url': f"{settings.FRONTEND_URL}/dashboard/subscription"
            },
            recipient_email=user.email
        )
    
    @classmethod
    def send_maintenance_reminder_email(cls, user, vehicle, maintenance, days_left):
        """Envoie un rappel de maintenance programmée"""
        return cls.send_email(
            subject=f'Rappel: Maintenance de votre {vehicle.brand} {vehicle.model}',
            template_name='maintenance-reminder',
            context={
                'user_name': user.first_name or user.email.split('@')[0],
                'vehicle_name': f"{vehicle.brand} {vehicle.model}",
                'maintenance_type': maintenance.type,
                'days_left': days_left,
                'scheduled_date': maintenance.scheduled_date.strftime('%d/%m/%Y'),
                'dashboard_url': f"{settings.FRONTEND_URL}/dashboard/maintenances"
            },
            recipient_email=user.email
        )
