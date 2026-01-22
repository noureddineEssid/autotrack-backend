from rest_framework import serializers
from .models import AIConversation, AIMessage


class AIMessageSerializer(serializers.ModelSerializer):
    """AI message serializer"""
    
    class Meta:
        model = AIMessage
        fields = ['id', 'conversation', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class AIConversationSerializer(serializers.ModelSerializer):
    """AI conversation serializer"""
    
    messages = AIMessageSerializer(many=True, read_only=True)
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AIConversation
        fields = [
            'id', 'user', 'title', 'context', 'messages',
            'messages_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class AIConversationCreateSerializer(serializers.ModelSerializer):
    """AI conversation creation serializer"""
    
    class Meta:
        model = AIConversation
        fields = ['title', 'context']


class AIMessageCreateSerializer(serializers.ModelSerializer):
    """AI message creation serializer"""
    
    class Meta:
        model = AIMessage
        fields = ['conversation', 'content']
    
    def validate_conversation(self, value):
        # Vérifie que la conversation appartient à l'utilisateur
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.user != request.user:
                raise serializers.ValidationError(
                    'You can only add messages to your own conversations.'
                )
        return value
    
    def create(self, validated_data):
        # Toujours role='user' pour les messages créés par l'utilisateur
        validated_data['role'] = 'user'
        message = super().create(validated_data)
        
        # TODO: Trigger AI response via Celery
        # from ai_assistant.tasks import generate_ai_response
        # generate_ai_response.delay(message.conversation.id, message.id)
        
        return message
