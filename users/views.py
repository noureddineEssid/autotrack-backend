from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
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
    generate_password_reset_token, verify_password_reset_token
)
from emails.email_service import EmailService
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

User = get_user_model()
email_service = EmailService()


class RegisterView(generics.CreateAPIView):
    """User registration view"""
    
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate OTP for email verification
        otp_code = create_otp_for_user(user)
        
        # Send welcome email with OTP
        email_service.send_welcome_email(
            to_email=user.email,
            user_name=user.first_name or user.email
        )
        
        # Send OTP email
        email_service.send_otp_email(
            to_email=user.email,
            user_name=user.first_name or user.email,
            otp_code=otp_code
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login view"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate OTP for login verification
        otp_code = create_otp_for_user(user)
        
        # Send OTP email
        email_service.send_otp_email(user, otp_code)
        
        # Return OTP required response without tokens
        return Response({
            'requireOtp': True,
            'email': user.email,
            'message': 'OTP code sent to your email'
        })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """User logout view"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Deactivate user sessions
            Session.objects.filter(user=request.user, is_active=True).update(is_active=False)
            
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveUpdateAPIView):
    """Current user view"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Change password view"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Invalid old password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Invalidate all sessions
        Session.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # Send confirmation email
        email_service.send_password_change_confirmation(
            to_email=user.email,
            user_name=user.first_name or user.email
        )
        
        return Response({'message': 'Password changed successfully'})


class SessionListView(generics.ListAPIView):
    """User sessions list view"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SessionSerializer
    
    def get_queryset(self):
        return Session.objects.filter(user=self.request.user, is_active=True)


class ForgotPasswordView(APIView):
    """Forgot password view - Send reset token to email"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            uid, token = generate_password_reset_token(user)
            
            # Send email
            reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?uid={uid}&token={token}"
            email_service.send_password_reset_email(
                to_email=user.email,
                user_name=user.first_name or user.email,
                reset_url=reset_url
            )
            
            return Response({
                'message': 'Password reset email sent successfully'
            })
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            return Response({
                'message': 'If your email is registered, you will receive a password reset link'
            })


class ValidateResetTokenView(APIView):
    """Validate reset token view"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ValidateResetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        
        user = verify_password_reset_token(uid, token)
        
        if user:
            return Response({
                'valid': True,
                'message': 'Token is valid'
            })
        else:
            return Response({
                'valid': False,
                'message': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """Reset password view"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        user = verify_password_reset_token(uid, token)
        
        if not user:
            return Response({
                'error': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        user.save()
        
        # Invalidate all sessions
        Session.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # Send confirmation email
        email_service.send_password_change_confirmation(
            to_email=user.email,
            user_name=user.first_name or user.email
        )
        
        return Response({
            'message': 'Password reset successfully'
        })


class VerifyOtpView(APIView):
    """Verify OTP view"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            user = User.objects.get(email=email)
            
            if verify_otp_for_user(user, otp_code):
                # Mark user email as verified
                user.email_verified = True
                user.save(update_fields=['email_verified'])
                
                # Generate JWT tokens after successful OTP verification
                refresh = RefreshToken.for_user(user)
                
                # Create session
                Session.objects.create(
                    user=user,
                    token=str(refresh.access_token),
                    refresh_token=str(refresh),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    expires_at=timezone.now() + timedelta(days=30)
                )
                
                return Response({
                    'message': 'OTP verified successfully',
                    'verified': True,
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
            else:
                return Response({
                    'error': 'Invalid or expired OTP code'
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ResendOtpView(APIView):
    """Resend OTP view"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Generate new OTP
            otp_code = create_otp_for_user(user)
            
            # Send OTP email
            email_service.send_otp_email(user, otp_code)
            
            return Response({
                'message': 'OTP sent successfully'
            })
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

