from rest_framework import serializers
from .models import Maintenance
from vehicles.serializers import VehicleSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class MaintenanceSerializer(serializers.ModelSerializer):
    """Maintenance serializer"""
    
    vehicle_info = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Maintenance
        fields = [
            'id', 'vehicle', 'vehicle_info', 'created_by', 'created_by_name',
            'performed_by', 'performed_by_name', 'service_date', 'service_type',
            'description', 'mileage', 'cost', 'status', 'invoice_url',
            'reminder_sent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_vehicle_info(self, obj):
        return {
            'id': obj.vehicle.id,
            'make': obj.vehicle.make,
            'model': obj.vehicle.model,
            'year': obj.vehicle.year,
            'license_plate': obj.vehicle.license_plate
        }


class MaintenanceCreateSerializer(serializers.ModelSerializer):
    """Maintenance creation serializer"""
    
    class Meta:
        model = Maintenance
        fields = [
            'vehicle', 'service_date', 'service_type', 'description',
            'mileage', 'cost', 'status', 'invoice_url', 'performed_by'
        ]
    
    def validate_vehicle(self, value):
        """Ensure vehicle belongs to current user"""
        user = self.context['request'].user
        if value.owner != user:
            raise serializers.ValidationError("You can only create maintenances for your own vehicles")
        return value
    
    def validate_mileage(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Mileage cannot be negative")
        return value
    
    def validate_cost(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Cost cannot be negative")
        return value


class MaintenanceDetailSerializer(MaintenanceSerializer):
    """Maintenance detail serializer with full vehicle info"""
    
    vehicle_detail = VehicleSerializer(source='vehicle', read_only=True)
    
    class Meta(MaintenanceSerializer.Meta):
        fields = MaintenanceSerializer.Meta.fields + ['vehicle_detail']


class MaintenanceUpdateSerializer(serializers.ModelSerializer):
    """Maintenance update serializer"""
    
    class Meta:
        model = Maintenance
        fields = [
            'service_date', 'service_type', 'description', 'mileage',
            'cost', 'status', 'invoice_url', 'performed_by', 'reminder_sent'
        ]
