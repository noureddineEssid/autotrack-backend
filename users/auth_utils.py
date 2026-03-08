"""
Utilitaires pour l'authentification (OTP, tokens, etc.)
"""
import secrets
import hmac
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

# Number of failed OTP attempts before lockout
OTP_MAX_ATTEMPTS = 5
OTP_LOCKOUT_MINUTES = 15


def _hash_otp(raw_code: str) -> str:
    """HMAC-SHA256 hash of OTP code using SECRET_KEY as the key."""
    key = force_bytes(settings.SECRET_KEY)
    return hmac.new(key, force_bytes(raw_code), hashlib.sha256).hexdigest()


def generate_otp() -> str:
    """Cryptographically secure 6-digit OTP."""
    return str(secrets.randbelow(1_000_000)).zfill(6)


def create_otp_for_user(user) -> str:
    """
    Creates and stores a hashed OTP for a user.
    Returns the plaintext OTP code (to be sent via email).
    """
    otp_code = generate_otp()
    expire_time = timezone.now() + timedelta(minutes=10)

    user.code_otp = _hash_otp(otp_code)
    user.expire_otp = expire_time
    user.otp_attempts = 0
    user.otp_locked_until = None
    user.save(update_fields=['code_otp', 'expire_otp', 'otp_attempts', 'otp_locked_until'])

    return otp_code


def verify_otp_for_user(user, code: str) -> bool:
    """
    Verifies the OTP code for a user.
    Returns True if valid, False otherwise.
    Enforces lockout after OTP_MAX_ATTEMPTS failed attempts.
    """
    now = timezone.now()

    # Check lockout
    if user.otp_locked_until and now < user.otp_locked_until:
        return False

    if not user.code_otp or not user.expire_otp:
        return False

    # Check expiration
    if now > user.expire_otp:
        user.code_otp = None
        user.expire_otp = None
        user.otp_attempts = 0
        user.save(update_fields=['code_otp', 'expire_otp', 'otp_attempts'])
        return False

    # Constant-time comparison against stored hash
    if not hmac.compare_digest(_hash_otp(code), user.code_otp):
        user.otp_attempts += 1
        update_fields = ['otp_attempts']
        if user.otp_attempts >= OTP_MAX_ATTEMPTS:
            user.otp_locked_until = now + timedelta(minutes=OTP_LOCKOUT_MINUTES)
            user.code_otp = None
            user.expire_otp = None
            update_fields += ['otp_locked_until', 'code_otp', 'expire_otp']
        user.save(update_fields=update_fields)
        return False

    # Valid — clear OTP
    user.code_otp = None
    user.expire_otp = None
    user.otp_attempts = 0
    user.otp_locked_until = None
    user.save(update_fields=['code_otp', 'expire_otp', 'otp_attempts', 'otp_locked_until'])
    return True


def clear_otp_for_user(user) -> None:
    """Clears OTP data for a user."""
    user.code_otp = None
    user.expire_otp = None
    user.otp_attempts = 0
    user.save(update_fields=['code_otp', 'expire_otp', 'otp_attempts'])


def generate_password_reset_token(user):
    """
    Generates a password reset token.
    Returns (uid, token)
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token


def verify_password_reset_token(uid, token):
    """
    Verifies a password reset token.
    Returns the User if valid, None otherwise.
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
