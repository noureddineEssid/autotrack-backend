from django.db import models


class PlanFeature(models.Model):
    """Plan feature model"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    feature_key = models.CharField(max_length=50, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plan_features'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Plan(models.Model):
    """Subscription plan model"""
    
    INTERVAL_CHOICES = [
        ('month', 'Monthly'),
        ('year', 'Yearly'),
    ]
    
    # Basic information
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default='month')
    
    # Stripe integration
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Features
    features = models.ManyToManyField(PlanFeature, through='PlanFeatureValue', related_name='plans')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plans'
        ordering = ['price']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['stripe_price_id']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}/{self.interval}"


class PlanFeatureValue(models.Model):
    """Plan feature value model (join table with extra data)"""
    
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    feature = models.ForeignKey(PlanFeature, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)  # Can be 'true', 'false', a number, or text
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plan_feature_values'
        unique_together = ['plan', 'feature']
    
    def __str__(self):
        return f"{self.plan.name} - {self.feature.name}: {self.value}"

