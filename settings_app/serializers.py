from rest_framework import serializers
from .models import UserSettings


class UserSettingsSerializer(serializers.ModelSerializer):
    """User settings serializer"""
    
    class Meta:
        model = UserSettings
        fields = [
            'id', 'user', 'language', 'theme', 'timezone',
            'email_notifications', 'push_notifications',
            'maintenance_reminders', 'subscription_alerts',
            'profile_public', 'custom_settings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserSettingsUpdateSerializer(serializers.ModelSerializer):
    """User settings update serializer"""
    
    class Meta:
        model = UserSettings
        fields = [
            'language', 'theme', 'timezone',
            'email_notifications', 'push_notifications',
            'maintenance_reminders', 'subscription_alerts',
            'profile_public', 'custom_settings'
        ]
