"""
Utilitaires pour l'authentification (OTP, tokens, etc.)
"""
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


def generate_otp():
    """Génère un code OTP à 6 chiffres"""
    return ''.join(random.choices(string.digits, k=6))


def create_otp_for_user(user):
    """
    Crée et stocke un code OTP pour un utilisateur
    Retourne le code OTP généré
    """
    otp_code = generate_otp()
    expire_time = timezone.now() + timedelta(minutes=10)
    
    user.code_otp = otp_code
    user.expire_otp = expire_time
    user.save(update_fields=['code_otp', 'expire_otp'])
    
    return otp_code


def verify_otp_for_user(user, code):
    """
    Vérifie le code OTP d'un utilisateur
    Retourne True si valide, False sinon
    """
    if not user.code_otp or not user.expire_otp:
        return False
    
    # Vérifier expiration
    if timezone.now() > user.expire_otp:
        user.code_otp = None
        user.expire_otp = None
        user.save(update_fields=['code_otp', 'expire_otp'])
        return False
    
    # Vérifier code
    if user.code_otp != code:
        return False
    
    # Code valide, nettoyer
    user.code_otp = None
    user.expire_otp = None
    user.save(update_fields=['code_otp', 'expire_otp'])
    
    return True


def clear_otp_for_user(user):
    """Nettoie le code OTP d'un utilisateur"""
    user.code_otp = None
    user.expire_otp = None
    user.save(update_fields=['code_otp', 'expire_otp'])


def generate_password_reset_token(user):
    """
    Génère un token de réinitialisation de mot de passe
    Retourne (uid, token)
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token


def verify_password_reset_token(uid, token):
    """
    Vérifie un token de réinitialisation de mot de passe
    Retourne l'utilisateur si valide, None sinon
    """
    try:
        from .models import User
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        if default_token_generator.check_token(user, token):
            return user
        return None
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
