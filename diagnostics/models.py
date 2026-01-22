from django.db import models
from django.conf import settings
from vehicles.models import Vehicle


class Diagnostic(models.Model):
    """Vehicle diagnostic model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diagnostics'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='diagnostics'
    )
    
    # Diagnostic details
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # AI Analysis
    ai_analysis = models.TextField(blank=True, null=True)
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diagnostics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.vehicle}"


class DiagnosticReply(models.Model):
    """Diagnostic reply/conversation model"""
    
    SENDER_TYPE_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI Assistant'),
        ('mechanic', 'Mechanic'),
    ]
    
    diagnostic = models.ForeignKey(
        Diagnostic,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diagnostic_replies'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['diagnostic', 'created_at']),
        ]
    
    def __str__(self):
        return f"Reply to {self.diagnostic.title} by {self.sender_type}"

