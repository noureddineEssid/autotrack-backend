from rest_framework import serializers
from .models import Vehicle, CarBrand, CarModel


class CarBrandSerializer(serializers.ModelSerializer):
    """Car brand serializer"""
    
    models_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CarBrand
        fields = ['id', 'name', 'logo_url', 'models_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_models_count(self, obj):
        return obj.models.count()


class CarModelSerializer(serializers.ModelSerializer):
    """Car model serializer"""
    
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta:
        model = CarModel
        fields = ['id', 'brand', 'brand_name', 'name', 'year_start', 'year_end', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleSerializer(serializers.ModelSerializer):
    """Vehicle serializer"""
    
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    owner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner', 'owner_email', 'owner_name',
            'make', 'model', 'year', 'license_plate', 'vin',
            'color', 'fuel_type', 'transmission',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def get_owner_name(self, obj):
        return obj.owner.get_full_name()
    
    def create(self, validated_data):
        # Set owner to current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class VehicleCreateSerializer(serializers.ModelSerializer):
    """Vehicle creation serializer"""
    
    class Meta:
        model = Vehicle
        fields = [
            'make', 'model', 'year', 'license_plate', 'vin',
            'color', 'fuel_type', 'transmission'
        ]
    
    def validate_year(self, value):
        from datetime import datetime
        current_year = datetime.now().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(
                f"Year must be between 1900 and {current_year + 1}"
            )
        return value
    
    def validate_vin(self, value):
        if value and len(value) != 17:
            raise serializers.ValidationError("VIN must be exactly 17 characters")
        return value


class VehicleDetailSerializer(VehicleSerializer):
    """Vehicle detail serializer with additional info"""
    
    maintenances_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    
    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + ['maintenances_count', 'documents_count']
    
    def get_maintenances_count(self, obj):
        return obj.maintenances.count()
    
    def get_documents_count(self, obj):
        return obj.documents.count()
