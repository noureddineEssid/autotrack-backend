from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .serializers import (
    UserSerializer, UserRegisterSerializer, UserLoginSerializer,
    ChangePasswordSerializer, SessionSerializer,
    ForgotPasswordSerializer, ValidateResetTokenSerializer,
    ResetPasswordSerializer, VerifyOtpSerializer, ResendOtpSerializer
)
from .models import Session
from .auth_utils import (
    create_otp_for_user, verify_otp_for_user,
    generate_password_reset_token, verify_password_reset_token,
    OTP_LOCKOUT_MINUTES,
)
from emails.email_service import EmailService
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

User = get_user_model()
email_service = EmailService()

# ---------------------------------------------------------------------------
# Custom throttle scopes for auth endpoints
# ---------------------------------------------------------------------------

class LoginThrottle(AnonRateThrottle):
    scope = 'login'


class OtpVerifyThrottle(AnonRateThrottle):
    scope = 'otp_verify'


class OtpResendThrottle(AnonRateThrottle):
    scope = 'otp_resend'


class PasswordResetThrottle(AnonRateThrottle):
    scope = 'password_reset'


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_client_ip(request) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class RegisterView(generics.CreateAPIView):
    """User registration — rate-limited to prevent spam."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer
    throttle_classes = [LoginThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp_code = create_otp_for_user(user)

        email_service.send_welcome_email(
            to_email=user.email,
            user_name=user.first_name or user.email,
        )
        email_service.send_otp_email(
            to_email=user.email,
            user_name=user.first_name or user.email,
            otp_code=otp_code,
        )

        # Do NOT issue JWT tokens yet — user must verify OTP first.
        return Response({
            'requireOtp': True,
            'email': user.email,
            'message': 'Registration successful. Please verify your email with the OTP code sent.',
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Login — issues OTP, never issues tokens before verification."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        otp_code = create_otp_for_user(user)
        email_service.send_otp_email(user, otp_code)

        return Response({
            'requireOtp': True,
            'email': user.email,
            'message': 'OTP code sent to your email',
        })


class LogoutView(APIView):
    """Logout — blacklists the refresh token and deactivates the session."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Blacklist the refresh token so it cannot be reused
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # Already invalid / blacklisted — that's fine

        Session.objects.filter(user=request.user, is_active=True).update(is_active=False)
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)


class MeView(generics.RetrieveUpdateAPIView):
    """Current user view."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Change password — invalidates all sessions and blacklists current refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Blacklist the current refresh token if provided
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        Session.objects.filter(user=user, is_active=True).update(is_active=False)

        email_service.send_password_change_confirmation(
            to_email=user.email,
            user_name=user.first_name or user.email,
        )

        return Response({'message': 'Password changed successfully'})


class SessionListView(generics.ListAPIView):
    """User sessions list view."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SessionSerializer

    def get_queryset(self):
        return Session.objects.filter(user=self.request.user, is_active=True)


class ForgotPasswordView(APIView):
    """Forgot password — always returns the same message to prevent user enumeration."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetThrottle]

    _GENERIC_MSG = 'If your email is registered, you will receive a password reset link.'

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            uid, token = generate_password_reset_token(user)
            reset_url = (
                f"{settings.FRONTEND_URL}/auth/reset-password?uid={uid}&token={token}"
            )
            email_service.send_password_reset_email(
                to_email=user.email,
                user_name=user.first_name or user.email,
                reset_url=reset_url,
            )
        except User.DoesNotExist:
            pass  # Silently ignore — same response below

        return Response({'message': self._GENERIC_MSG})


class ValidateResetTokenView(APIView):
    """Validate reset token view."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = ValidateResetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']

        user = verify_password_reset_token(uid, token)

        if user:
            return Response({'valid': True, 'message': 'Token is valid'})
        return Response(
            {'valid': False, 'message': 'Invalid or expired token'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResetPasswordView(APIView):
    """Reset password — token is one-time use (Django default token generator)."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']

        user = verify_password_reset_token(uid, token)

        if not user:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save()

        Session.objects.filter(user=user, is_active=True).update(is_active=False)

        email_service.send_password_change_confirmation(
            to_email=user.email,
            user_name=user.first_name or user.email,
        )

        return Response({'message': 'Password reset successfully'})


class VerifyOtpView(APIView):
    """Verify OTP — rate-limited, lockout after 5 failed attempts."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [OtpVerifyThrottle]

    _GENERIC_ERROR = 'Invalid or expired OTP code'

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Same error as wrong OTP — no enumeration
            return Response(
                {'error': self._GENERIC_ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check lockout before verifying
        if user.otp_locked_until and timezone.now() < user.otp_locked_until:
            wait = int((user.otp_locked_until - timezone.now()).total_seconds() / 60) + 1
            return Response(
                {'error': f'Too many failed attempts. Try again in {wait} minute(s).'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if not verify_otp_for_user(user, otp_code):
            return Response(
                {'error': self._GENERIC_ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # OTP valid — mark email as verified and issue tokens
        user.email_verified = True
        user.save(update_fields=['email_verified'])

        refresh = RefreshToken.for_user(user)

        Session.objects.create(
            user=user,
            token=str(refresh.access_token),
            refresh_token=str(refresh),
            ip_address=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=timezone.now() + timedelta(days=7),
        )

        return Response({
            'message': 'OTP verified successfully',
            'verified': True,
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
        })


class ResendOtpView(APIView):
    """Resend OTP — rate-limited, always returns success to prevent user enumeration."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [OtpResendThrottle]

    _GENERIC_MSG = 'If the email is registered, a new OTP has been sent.'

    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            otp_code = create_otp_for_user(user)
            email_service.send_otp_email(user, otp_code)
        except User.DoesNotExist:
            pass  # Silently ignore — same response below

        return Response({'message': self._GENERIC_MSG})

