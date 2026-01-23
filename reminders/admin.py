from django.contrib import admin
from .models import Reminder, NotificationPreference, PushToken


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'reminder_type', 'priority', 'status', 'remind_at', 'is_overdue']
    list_filter = ['reminder_type', 'priority', 'status', 'remind_at']
    search_fields = ['title', 'message', 'user__username', 'user__email']
    readonly_fields = ['id', 'sent_at', 'read_at', 'dismissed_at', 'created_at', 'updated_at']
    date_hierarchy = 'remind_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'reminder_type', 'title', 'message', 'priority')
        }),
        ('Related Objects', {
            'fields': ('vehicle', 'maintenance', 'document', 'diagnostic')
        }),
        ('Scheduling', {
            'fields': ('remind_at', 'repeat', 'repeat_interval')
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'read_at', 'dismissed_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def is_overdue(self, obj):
        from django.utils import timezone
        if obj.status == 'pending' and obj.remind_at < timezone.now():
            return True
        return False
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'enable_email', 'enable_push', 'enable_sms', 'digest_frequency']
    list_filter = ['enable_email', 'enable_push', 'enable_sms', 'digest_frequency']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Channels', {
            'fields': ('enable_email', 'enable_push', 'enable_sms', 'enable_in_app')
        }),
        ('Reminder Types', {
            'fields': ('maintenance_reminders', 'document_expiry_reminders', 'diagnostic_reminders', 'custom_reminders')
        }),
        ('Timing', {
            'fields': ('days_before_maintenance', 'days_before_document_expiry', 'reminder_time', 'digest_frequency')
        }),
        ('Quiet Hours', {
            'fields': ('enable_quiet_hours', 'quiet_hours_start', 'quiet_hours_end')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'device_name', 'is_active', 'last_used_at', 'created_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['user__username', 'device_name', 'token']
    readonly_fields = ['id', 'last_used_at', 'created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'token', 'platform', 'device_name')
        }),
        ('Status', {
            'fields': ('is_active', 'last_used_at')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
