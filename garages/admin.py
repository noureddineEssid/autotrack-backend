from django.contrib import admin
from .models import Garage, GarageReview


@admin.register(Garage)
class GarageAdmin(admin.ModelAdmin):
    """Garage admin"""
    list_display = ['name', 'city', 'postal_code', 'average_rating', 'total_reviews']
    list_filter = ['city', 'country', 'average_rating']
    search_fields = ['name', 'address', 'city', 'email']
    ordering = ['-average_rating', 'name']
    readonly_fields = ['average_rating', 'total_reviews', 'created_at', 'updated_at']


@admin.register(GarageReview)
class GarageReviewAdmin(admin.ModelAdmin):
    """Garage review admin"""
    list_display = ['garage', 'reviewer_name', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['garage__name', 'reviewer_name', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
