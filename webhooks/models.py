from django.db import models


class WebhookEvent(models.Model):
    """Webhook event model for external services"""
    
    # Event details
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    source = models.CharField(max_length=50, default='external')
    
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

