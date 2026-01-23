"""
Admin configuration for bookings
"""

from django.contrib import admin
from .models import GarageService, GarageAvailability, Booking, BookingReview


@admin.register(GarageService)
class GarageServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'garage', 'category', 'duration_minutes', 'price', 'is_active']
    list_filter = ['category', 'is_active', 'garage']
    search_fields = ['name', 'description', 'garage__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = [
        ('Informations de base', {
            'fields': ['id', 'garage', 'name', 'description', 'category']
        }),
        ('Tarification', {
            'fields': ['duration_minutes', 'price']
        }),
        ('Statut', {
            'fields': ['is_active', 'created_at', 'updated_at']
        }),
    ]


@admin.register(GarageAvailability)
class GarageAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['garage', 'weekday_display', 'start_time', 'end_time', 'max_bookings_per_slot', 'is_active']
    list_filter = ['weekday', 'is_active', 'garage']
    search_fields = ['garage__name']
    readonly_fields = ['id']
    
    def weekday_display(self, obj):
        return obj.get_weekday_display()
    weekday_display.short_description = 'Jour'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'customer_name', 'garage', 'vehicle_display', 'booking_date',
        'booking_time', 'status', 'payment_status', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'booking_date', 'created_at', 'garage']
    search_fields = ['customer_name', 'customer_email', 'customer_phone', 'garage__name', 'vehicle__registration_number']
    readonly_fields = [
        'id', 'user', 'created_at', 'updated_at', 'confirmed_at',
        'completed_at', 'cancelled_at', 'reminder_sent_at', 'is_past_display',
        'is_upcoming_display', 'can_cancel_display'
    ]
    date_hierarchy = 'booking_date'
    
    fieldsets = [
        ('Client', {
            'fields': ['user', 'customer_name', 'customer_phone', 'customer_email', 'vehicle']
        }),
        ('Réservation', {
            'fields': ['garage', 'service', 'booking_date', 'booking_time', 'duration_minutes', 'status']
        }),
        ('Notes', {
            'fields': ['notes', 'garage_notes']
        }),
        ('Tarification', {
            'fields': ['estimated_price', 'final_price', 'payment_status']
        }),
        ('Historique', {
            'fields': [
                'created_at', 'updated_at', 'confirmed_at',
                'completed_at', 'cancelled_at', 'cancellation_reason', 'cancelled_by'
            ]
        }),
        ('Rappels', {
            'fields': ['reminder_sent', 'reminder_sent_at']
        }),
        ('Statut calculé', {
            'fields': ['is_past_display', 'is_upcoming_display', 'can_cancel_display']
        }),
    ]
    
    def vehicle_display(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.brand} {obj.vehicle.model} ({obj.vehicle.registration_number})"
        return '-'
    vehicle_display.short_description = 'Véhicule'
    
    def is_past_display(self, obj):
        return obj.is_past
    is_past_display.boolean = True
    is_past_display.short_description = 'Passé'
    
    def is_upcoming_display(self, obj):
        return obj.is_upcoming
    is_upcoming_display.boolean = True
    is_upcoming_display.short_description = 'À venir (7j)'
    
    def can_cancel_display(self, obj):
        return obj.can_cancel
    can_cancel_display.boolean = True
    can_cancel_display.short_description = 'Annulable'


@admin.register(BookingReview)
class BookingReviewAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rating', 'would_recommend', 'created_at']
    list_filter = ['rating', 'would_recommend', 'created_at']
    search_fields = ['booking__customer_name', 'booking__garage__name', 'comment']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Réservation', {
            'fields': ['id', 'booking']
        }),
        ('Évaluation globale', {
            'fields': ['rating', 'comment', 'would_recommend']
        }),
        ('Évaluations détaillées', {
            'fields': ['service_quality', 'waiting_time', 'value_for_money']
        }),
        ('Dates', {
            'fields': ['created_at', 'updated_at']
        }),
    ]
