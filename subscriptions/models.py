from django.db import models
from django.conf import settings


class Subscription(models.Model):
    """User subscription model"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('trialing', 'Trialing'),
        ('past_due', 'Past Due'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan_code = models.CharField(max_length=50, default='free')
    plan_name = models.CharField(max_length=100, default='Free')
    
    # Stripe integration
    stripe_subscription_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    
    # Trial
    trial_start = models.DateTimeField(blank=True, null=True)
    trial_end = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['stripe_subscription_id']),
            models.Index(fields=['current_period_end']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan_name}"
    
    def is_active(self):
        """Check if subscription is active"""
        return self.status == 'active'


class SubscriptionHistory(models.Model):
    """Subscription history model to track changes"""
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='history'
    )
    event_type = models.CharField(max_length=50)  # 'created', 'updated', 'cancelled', etc.
    previous_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'subscription_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.subscription} - {self.event_type}"

