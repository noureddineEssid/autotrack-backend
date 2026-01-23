from django.db import models
from django.conf import settings
from vehicles.models import Vehicle
import uuid


class Report(models.Model):
    """Model for generated reports"""
    
    REPORT_TYPES = [
        ('vehicle_summary', 'Vehicle Summary'),
        ('maintenance_history', 'Maintenance History'),
        ('diagnostic_history', 'Diagnostic History'),
        ('cost_analysis', 'Cost Analysis'),
        ('fuel_consumption', 'Fuel Consumption'),
        ('comprehensive', 'Comprehensive Report'),
    ]
    
    FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMATS)
    
    # Optional filters
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    
    # Report configuration
    include_charts = models.BooleanField(default=True)
    include_images = models.BooleanField(default=True)
    include_summary = models.BooleanField(default=True)
    include_details = models.BooleanField(default=True)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(null=True, blank=True)  # in bytes
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Auto-delete after 7 days
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'report_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.format.upper()} - {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def download_url(self):
        """Generate download URL for the report"""
        if self.status == 'completed' and self.file_path:
            return f"/api/reports/{self.id}/download/"
        return None
    
    @property
    def is_expired(self):
        """Check if report has expired"""
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class ReportTemplate(models.Model):
    """Custom report templates for users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='report_templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template configuration (stored as JSON)
    report_type = models.CharField(max_length=50, choices=Report.REPORT_TYPES)
    default_format = models.CharField(max_length=10, choices=Report.FORMATS, default='pdf')
    
    # Default settings
    include_charts = models.BooleanField(default=True)
    include_images = models.BooleanField(default=True)
    include_summary = models.BooleanField(default=True)
    include_details = models.BooleanField(default=True)
    
    # Metadata
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
