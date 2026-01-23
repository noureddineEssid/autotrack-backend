from rest_framework import serializers
from .models import Reminder, NotificationPreference, PushToken


class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for Reminder model"""
    
    reminder_type_display = serializers.CharField(source='get_reminder_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    vehicle_name = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'reminder_type', 'reminder_type_display', 'title', 'message',
            'priority', 'priority_display', 'vehicle', 'vehicle_name',
            'maintenance', 'document', 'diagnostic',
            'remind_at', 'repeat', 'repeat_interval',
            'status', 'status_display', 'sent_at', 'read_at', 'dismissed_at',
            'created_at', 'updated_at', 'is_overdue'
        ]
        read_only_fields = ['id', 'sent_at', 'read_at', 'dismissed_at', 'created_at', 'updated_at']
    
    def get_vehicle_name(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.license_plate})"
        return None
    
    def get_is_overdue(self, obj):
        from django.utils import timezone
        if obj.status == 'pending' and obj.remind_at < timezone.now():
            return True
        return False


class CreateReminderSerializer(serializers.Serializer):
    """Serializer for creating a reminder"""
    
    reminder_type = serializers.ChoiceField(choices=Reminder.REMINDER_TYPES)
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    priority = serializers.ChoiceField(choices=Reminder.PRIORITY_CHOICES, default='medium')
    vehicle_id = serializers.UUIDField(required=False, allow_null=True)
    maintenance_id = serializers.UUIDField(required=False, allow_null=True)
    document_id = serializers.UUIDField(required=False, allow_null=True)
    diagnostic_id = serializers.UUIDField(required=False, allow_null=True)
    remind_at = serializers.DateTimeField()
    repeat = serializers.BooleanField(default=False)
    repeat_interval = serializers.CharField(required=False, allow_blank=True)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'enable_email', 'enable_push', 'enable_sms', 'enable_in_app',
            'maintenance_reminders', 'document_expiry_reminders',
            'diagnostic_reminders', 'custom_reminders',
            'days_before_maintenance', 'days_before_document_expiry',
            'reminder_time', 'digest_frequency',
            'enable_quiet_hours', 'quiet_hours_start', 'quiet_hours_end',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PushTokenSerializer(serializers.ModelSerializer):
    """Serializer for PushToken model"""
    
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    class Meta:
        model = PushToken
        fields = [
            'id', 'token', 'platform', 'platform_display', 'device_name',
            'is_active', 'last_used_at', 'created_at'
        ]
        read_only_fields = ['id', 'last_used_at', 'created_at']


class ReminderStatsSerializer(serializers.Serializer):
    """Serializer for reminder statistics"""
    
    total_reminders = serializers.IntegerField()
    pending = serializers.IntegerField()
    sent = serializers.IntegerField()
    read = serializers.IntegerField()
    overdue = serializers.IntegerField()
    by_type = serializers.DictField()
    by_priority = serializers.DictField()
    upcoming_7_days = serializers.IntegerField()
