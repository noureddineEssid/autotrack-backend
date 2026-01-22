from rest_framework import serializers
from .models import Diagnostic, DiagnosticReply
from vehicles.serializers import VehicleSerializer


class DiagnosticReplySerializer(serializers.ModelSerializer):
    """Diagnostic reply serializer"""
    
    class Meta:
        model = DiagnosticReply
        fields = ['id', 'diagnostic', 'sender', 'sender_type', 'message', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


class DiagnosticSerializer(serializers.ModelSerializer):
    """Diagnostic serializer"""
    
    vehicle_info = VehicleSerializer(source='vehicle', read_only=True)
    replies_count = serializers.SerializerMethodField()
    latest_reply = serializers.SerializerMethodField()
    
    class Meta:
        model = Diagnostic
        fields = [
            'id', 'user', 'vehicle', 'vehicle_info', 'title', 'description',
            'status', 'ai_analysis', 'confidence_score', 'replies_count',
            'latest_reply', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'ai_analysis', 'confidence_score', 'created_at', 'updated_at']
    
    def get_replies_count(self, obj):
        return obj.replies.count()
    
    def get_latest_reply(self, obj):
        latest = obj.replies.order_by('-created_at').first()
        if latest:
            return DiagnosticReplySerializer(latest).data
        return None


class DiagnosticCreateSerializer(serializers.ModelSerializer):
    """Diagnostic creation serializer"""
    
    class Meta:
        model = Diagnostic
        fields = ['vehicle', 'title', 'description']
    
    def validate_vehicle(self, value):
        # Vérifie que le véhicule appartient à l'utilisateur
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.owner != request.user:
                raise serializers.ValidationError(
                    'You can only create diagnostics for your own vehicles.'
                )
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        diagnostic = super().create(validated_data)
        
        # TODO: Trigger AI analysis asynchronously via Celery
        # from diagnostics.tasks import analyze_diagnostic_with_ai
        # analyze_diagnostic_with_ai.delay(diagnostic.id)
        
        return diagnostic


class DiagnosticDetailSerializer(DiagnosticSerializer):
    """Diagnostic detail serializer with all replies"""
    
    all_replies = DiagnosticReplySerializer(source='replies', many=True, read_only=True)
    
    class Meta(DiagnosticSerializer.Meta):
        fields = DiagnosticSerializer.Meta.fields + ['all_replies']


class DiagnosticUpdateSerializer(serializers.ModelSerializer):
    """Diagnostic update serializer"""
    
    class Meta:
        model = Diagnostic
        fields = ['title', 'description', 'status']


class DiagnosticReplyCreateSerializer(serializers.ModelSerializer):
    """Diagnostic reply creation serializer"""
    
    class Meta:
        model = DiagnosticReply
        fields = ['diagnostic', 'message', 'metadata']
    
    def validate_diagnostic(self, value):
        # Vérifie que le diagnostic appartient à l'utilisateur
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.user != request.user:
                raise serializers.ValidationError(
                    'You can only reply to your own diagnostics.'
                )
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['sender_type'] = 'user'
        if request and hasattr(request, 'user'):
            validated_data['sender'] = request.user
        return super().create(validated_data)
