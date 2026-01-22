"""
Service d'envoi d'emails pour AutoTrack
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


class EmailService:
    """Service centralisé pour l'envoi d'emails"""
    
    @staticmethod
    def send_welcome_email(user):
        """
        Envoie un email de bienvenue à un nouvel utilisateur
        """
        subject = 'Bienvenue sur AutoTrack+ !'
        context = {
            'name': user.first_name or user.email,
            'email': user.email,
            'login_url': f"{settings.FRONTEND_URL}/auth/login" if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000/auth/login"
        }
        
        html_content = render_to_string('emails/welcome.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
    
    @staticmethod
    def send_otp_email(user, otp_code):
        """
        Envoie un email avec le code OTP pour la connexion
        """
        subject = 'Votre code de vérification AutoTrack+'
        context = {
            'name': user.first_name or user.email,
            'otp_code': otp_code,
            'validity_minutes': 10
        }
        
        html_content = render_to_string('emails/otp.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
    
    @staticmethod
    def send_password_reset_email(user, reset_url):
        """
        Envoie un email de réinitialisation de mot de passe
        """
        subject = 'Réinitialisation de votre mot de passe AutoTrack+'
        context = {
            'name': user.first_name or user.email,
            'reset_url': reset_url
        }
        
        html_content = render_to_string('emails/password_reset.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
    
    @staticmethod
    def send_password_change_confirmation(user):
        """
        Envoie un email de confirmation de changement de mot de passe
        """
        subject = 'Votre mot de passe a été changé'
        context = {
            'name': user.first_name or user.email,
        }
        
        html_content = render_to_string('emails/password_change_confirmation.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
    
    @staticmethod
    def send_subscription_email(to_email, subject, template_name, context):
        """
        Envoie un email lié à l'abonnement
        """
        html_content = render_to_string(f'emails/{template_name}.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
