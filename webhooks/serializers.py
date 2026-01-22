from rest_framework import serializers
from .models import WebhookEvent


class WebhookEventSerializer(serializers.ModelSerializer):
    """Webhook event serializer"""
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'event_type', 'payload', 'source', 'processed',
            'processed_at', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'processed_at', 'created_at']
