"""
Booking models for garage appointments
"""

import uuid
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class GarageService(models.Model):
    """Services offered by garages"""
    
    CATEGORY_CHOICES = [
        ('maintenance', 'Entretien'),
        ('repair', 'Réparation'),
        ('diagnostic', 'Diagnostic'),
        ('tire', 'Pneumatiques'),
        ('bodywork', 'Carrosserie'),
        ('other', 'Autre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    garage = models.ForeignKey('garages.Garage', on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='maintenance')
    duration_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(480)],
        help_text="Durée estimée en minutes"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Prix en euros"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Service Garage'
        verbose_name_plural = 'Services Garages'
        indexes = [
            models.Index(fields=['garage', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.garage.name}"


class GarageAvailability(models.Model):
    """Availability slots for garages"""
    
    WEEKDAY_CHOICES = [
        (0, 'Lundi'),
        (1, 'Mardi'),
        (2, 'Mercredi'),
        (3, 'Jeudi'),
        (4, 'Vendredi'),
        (5, 'Samedi'),
        (6, 'Dimanche'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    garage = models.ForeignKey('garages.Garage', on_delete=models.CASCADE, related_name='availability')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_bookings_per_slot = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Nombre maximum de réservations par créneau"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['weekday', 'start_time']
        verbose_name = 'Disponibilité Garage'
        verbose_name_plural = 'Disponibilités Garages'
        unique_together = [['garage', 'weekday', 'start_time']]
    
    def __str__(self):
        return f"{self.garage.name} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class Booking(models.Model):
    """Garage booking/appointment"""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
        ('no_show', 'Absent'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('refunded', 'Remboursé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    garage = models.ForeignKey('garages.Garage', on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(GarageService, on_delete=models.SET_NULL, null=True, related_name='bookings')
    
    # Booking details
    booking_date = models.DateField()
    booking_time = models.TimeField()
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Customer information
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()
    notes = models.TextField(blank=True, help_text="Notes du client")
    
    # Garage notes
    garage_notes = models.TextField(blank=True, help_text="Notes internes du garage")
    
    # Pricing
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_bookings'
    )
    
    # Reminder sent
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-booking_date', '-booking_time']
        verbose_name = 'Réservation'
        verbose_name_plural = 'Réservations'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['garage', 'booking_date']),
            models.Index(fields=['status', 'booking_date']),
            models.Index(fields=['booking_date', 'booking_time']),
        ]
    
    def __str__(self):
        return f"{self.customer_name} - {self.garage.name} - {self.booking_date} {self.booking_time}"
    
    @property
    def is_past(self):
        """Check if booking is in the past"""
        booking_datetime = datetime.combine(self.booking_date, self.booking_time)
        booking_datetime = timezone.make_aware(booking_datetime) if timezone.is_naive(booking_datetime) else booking_datetime
        return booking_datetime < timezone.now()
    
    @property
    def is_upcoming(self):
        """Check if booking is in next 7 days"""
        booking_datetime = datetime.combine(self.booking_date, self.booking_time)
        booking_datetime = timezone.make_aware(booking_datetime) if timezone.is_naive(booking_datetime) else booking_datetime
        return booking_datetime > timezone.now() and booking_datetime < timezone.now() + timedelta(days=7)
    
    @property
    def is_today(self):
        """Check if booking is today"""
        return self.booking_date == timezone.now().date()
    
    @property
    def can_cancel(self):
        """Check if booking can be cancelled (at least 24h before)"""
        if self.status in ['cancelled', 'completed', 'no_show']:
            return False
        booking_datetime = datetime.combine(self.booking_date, self.booking_time)
        booking_datetime = timezone.make_aware(booking_datetime) if timezone.is_naive(booking_datetime) else booking_datetime
        return booking_datetime > timezone.now() + timedelta(hours=24)
    
    def confirm(self):
        """Confirm the booking"""
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
    
    def start_service(self):
        """Mark booking as in progress"""
        self.status = 'in_progress'
        self.save()
    
    def complete(self, final_price=None):
        """Complete the booking"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if final_price is not None:
            self.final_price = final_price
        self.save()
    
    def cancel(self, reason='', cancelled_by=None):
        """Cancel the booking"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by
        self.save()
    
    def mark_no_show(self):
        """Mark customer as no-show"""
        self.status = 'no_show'
        self.save()


class BookingReview(models.Model):
    """Customer review for a booking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Note de 1 à 5 étoiles"
    )
    comment = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=True)
    
    # Detailed ratings
    service_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    waiting_time = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    value_for_money = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Avis Réservation'
        verbose_name_plural = 'Avis Réservations'
    
    def __str__(self):
        return f"Avis {self.rating}⭐ - {self.booking.garage.name}"
