from django.db import models


class WebhookEvent(models.Model):
    """Webhook event model for external services"""
    
    # Event details
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    source = models.CharField(max_length=50, default='stripe')  # stripe, etc.
    
    # Processing status
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'webhooks_event'
        verbose_name = 'Webhook Event'
        verbose_name_plural = 'Webhook Events'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.source} - {self.event_type} ({self.created_at})"


# Keep StripeEvent for backward compatibility (can be removed later)
class StripeEvent(models.Model):
    """Stripe webhook event model (legacy - use WebhookEvent instead)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]
    
    # Stripe event details
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    
    # Event data
    data = models.JSONField(default=dict)
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'webhooks_stripe_event'
        verbose_name = 'Stripe Event'
        verbose_name_plural = 'Stripe Events'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.stripe_event_id} - {self.event_type}"

        db_table = 'stripe_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_event_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id}"

