from django.contrib import admin
from .models import UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """User settings admin"""
    list_display = ['user', 'language', 'timezone', 'theme', 'email_notifications']
    list_filter = ['language', 'theme', 'email_notifications']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['user']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Localization', {
            'fields': ('language', 'timezone', 'theme')
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'push_notifications',
                      'maintenance_reminders', 'subscription_alerts')
        }),
        ('Privacy', {
            'fields': ('profile_public',)
        }),
        ('Custom Settings', {
            'fields': ('custom_settings',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
