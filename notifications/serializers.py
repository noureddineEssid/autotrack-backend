from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'title', 'message',
            'link', 'metadata', 'is_read', 'read_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'read_at', 'created_at', 'updated_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Notification creation serializer"""
    
    class Meta:
        model = Notification
        fields = ['notification_type', 'title', 'message', 'link', 'metadata']
    
    def create(self, validated_data):
        # Ajouter l'utilisateur de la requête
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        return super().create(validated_data)


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Notification update serializer"""
    
    class Meta:
        model = Notification
        fields = ['is_read']
