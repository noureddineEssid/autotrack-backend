from django.db import models
from django.conf import settings


class UserSettings(models.Model):
    """User settings model"""
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('es', 'Spanish'),
    ]
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Preferences
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='auto')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    maintenance_reminders = models.BooleanField(default=True)
    subscription_alerts = models.BooleanField(default=True)
    
    # Privacy
    profile_public = models.BooleanField(default=False)
    
    # Additional settings
    custom_settings = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_settings'
        verbose_name_plural = 'User settings'
    
    def __str__(self):
        return f"Settings for {self.user.email}"

