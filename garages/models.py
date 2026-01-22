from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Garage(models.Model):
    """Garage model with geolocation support"""
    
    # Basic information
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Address
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Geolocation (using JSONField for coordinates: [longitude, latitude])
    location = models.JSONField(
        blank=True,
        null=True,
        help_text='GeoJSON Point: {"type": "Point", "coordinates": [longitude, latitude]}'
    )
    
    # Details
    description = models.TextField(blank=True, null=True)
    specialties = models.JSONField(default=list, blank=True)  # ['Vidange', 'Révision', etc.]
    certifications = models.JSONField(default=list, blank=True)  # ['ISO 9001', etc.]
    
    # Rating system
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'garages'
        ordering = ['-average_rating', 'name']
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['postal_code']),
            models.Index(fields=['-average_rating']),
        ]
    
    def __str__(self):
        return self.name


class GarageReview(models.Model):
    """Garage review model"""
    
    garage = models.ForeignKey(Garage, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=100)
    reviewer_email = models.EmailField(blank=True, null=True)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'garage_reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['garage', '-created_at']),
        ]
    
    def __str__(self):
        return f"Review for {self.garage.name} by {self.reviewer_name}"

