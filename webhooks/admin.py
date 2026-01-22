from django.contrib import admin
from .models import WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Webhook event admin"""
    list_display = ['event_type', 'source', 'processed', 'processed_at', 'created_at']
    list_filter = ['event_type', 'source', 'processed', 'created_at']
    search_fields = ['event_type', 'error_message']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'processed_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'source', 'payload')
        }),
        ('Processing Status', {
            'fields': ('processed', 'processed_at', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
