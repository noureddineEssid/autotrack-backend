from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Subscription admin"""
    list_display = ['user', 'plan', 'status', 'current_period_end', 'cancel_at_period_end', 'created_at']
    list_filter = ['status', 'cancel_at_period_end', 'plan', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'stripe_subscription_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Stripe Information', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id')
        }),
        ('Billing Period', {
            'fields': ('current_period_start', 'current_period_end', 'cancel_at_period_end')
        }),
        ('Trial Period', {
            'fields': ('trial_start', 'trial_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
