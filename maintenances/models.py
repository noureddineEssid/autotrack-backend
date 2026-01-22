from django.db import models
from django.conf import settings
from vehicles.models import Vehicle


class Maintenance(models.Model):
    """Maintenance record model"""
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='maintenances'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_maintenances'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='performed_maintenances',
        blank=True,
        null=True
    )
    
    # Maintenance details
    service_date = models.DateTimeField()
    service_type = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    mileage = models.IntegerField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )
    invoice_url = models.URLField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'maintenances'
        ordering = ['-service_date']
        indexes = [
            models.Index(fields=['vehicle', '-service_date']),
            models.Index(fields=['created_by']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.service_type} - {self.vehicle}"

