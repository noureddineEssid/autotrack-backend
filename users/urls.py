from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, MeView,
    ChangePasswordView, SessionListView,
    ForgotPasswordView, ValidateResetTokenView, ResetPasswordView,
    VerifyOtpView, ResendOtpView
)

app_name = 'users'

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('me', MeView.as_view(), name='me'),
    path('change-password', ChangePasswordView.as_view(), name='change-password'),
    path('sessions', SessionListView.as_view(), name='sessions'),
    
    # Password reset endpoints
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('validate-reset-token', ValidateResetTokenView.as_view(), name='validate-reset-token'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
    
    # OTP endpoints
    path('verify-otp', VerifyOtpView.as_view(), name='verify-otp'),
    path('resend-otp', ResendOtpView.as_view(), name='resend-otp'),
]
