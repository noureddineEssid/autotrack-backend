from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager for User model"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User"""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        # Set username to email if not provided
        if 'username' not in extra_fields or not extra_fields.get('username'):
            extra_fields['username'] = email
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('garage_owner', 'Garage Owner'),
    ]
    
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Stripe
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Password reset
    password_reset_token = models.CharField(max_length=255, blank=True, null=True)
    password_reset_token_expiration = models.DateTimeField(blank=True, null=True)
    
    # OTP for 2FA
    code_otp = models.CharField(max_length=6, blank=True, null=True)
    expire_otp = models.DateTimeField(blank=True, null=True)
    
    # Roles
    roles = models.JSONField(default=list, blank=True)
    
    # Email verification
    email_verified = models.BooleanField(default=False)
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['stripe_customer_id']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return role in self.roles if self.roles else False


class Session(models.Model):
    """User session model"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email}"
    
    def is_expired(self):
        """Check if session is expired"""
        return timezone.now() > self.expires_at

