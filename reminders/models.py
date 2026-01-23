from django.db import models
from django.conf import settings
from vehicles.models import Vehicle
from diagnostics.models import Diagnostic
import uuid


class Reminder(models.Model):
    """Model for user reminders"""
    
    REMINDER_TYPES = [
        ('maintenance', 'Maintenance Due'),
        ('document_expiry', 'Document Expiring'),
        ('diagnostic_followup', 'Diagnostic Follow-up'),
        ('custom', 'Custom Reminder'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('read', 'Read'),
        ('dismissed', 'Dismissed'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders')
    
    # Reminder details
    reminder_type = models.CharField(max_length=50, choices=REMINDER_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Related objects (optional)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    maintenance = models.ForeignKey('maintenances.Maintenance', on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    document = models.ForeignKey('documents.Document', on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    diagnostic = models.ForeignKey(Diagnostic, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    
    # Scheduling
    remind_at = models.DateTimeField()
    repeat = models.BooleanField(default=False)
    repeat_interval = models.CharField(max_length=20, blank=True)  # daily, weekly, monthly, yearly
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-remind_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'remind_at']),
            models.Index(fields=['status', 'remind_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_sent(self):
        """Mark reminder as sent"""
        from django.utils import timezone
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_read(self):
        """Mark reminder as read"""
        from django.utils import timezone
        if self.status == 'sent':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()
    
    def dismiss(self):
        """Dismiss reminder"""
        from django.utils import timezone
        self.status = 'dismissed'
        self.dismissed_at = timezone.now()
        self.save()


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    enable_email = models.BooleanField(default=True)
    enable_push = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_in_app = models.BooleanField(default=True)
    
    # Reminder type preferences
    maintenance_reminders = models.BooleanField(default=True)
    document_expiry_reminders = models.BooleanField(default=True)
    diagnostic_reminders = models.BooleanField(default=True)
    custom_reminders = models.BooleanField(default=True)
    
    # Timing preferences
    days_before_maintenance = models.IntegerField(default=7)
    days_before_document_expiry = models.IntegerField(default=30)
    reminder_time = models.TimeField(default='09:00:00')
    
    # Frequency
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='weekly'
    )
    
    # Quiet hours
    enable_quiet_hours = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default='22:00:00')
    quiet_hours_end = models.TimeField(default='08:00:00')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class PushToken(models.Model):
    """Store push notification tokens for mobile devices"""
    
    PLATFORMS = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_tokens')
    token = models.CharField(max_length=500, unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORMS)
    device_name = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.device_name}"
