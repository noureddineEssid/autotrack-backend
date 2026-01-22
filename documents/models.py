from django.db import models
from django.conf import settings
from vehicles.models import Vehicle


class Document(models.Model):
    """Document model for vehicle documents"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('invoice', 'Invoice'),
        ('insurance', 'Insurance'),
        ('registration', 'Registration'),
        ('inspection', 'Inspection'),
        ('maintenance', 'Maintenance Record'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='documents',
        blank=True,
        null=True
    )
    
    # Document details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='other'
    )
    
    # File
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_size = models.IntegerField(blank=True, null=True)  # in bytes
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    
    # OCR/Analysis
    extracted_text = models.TextField(blank=True, null=True)
    analysis_data = models.JSONField(default=dict, blank=True)
    is_analyzed = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['document_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"

