from rest_framework import serializers
from .models import Plan, PlanFeature, PlanFeatureValue


class PlanFeatureValueSerializer(serializers.ModelSerializer):
    """Plan feature value serializer"""
    feature_name = serializers.CharField(source='feature.name', read_only=True)
    feature_key = serializers.CharField(source='feature.feature_key', read_only=True)
    
    class Meta:
        model = PlanFeatureValue
        fields = ['id', 'feature', 'feature_name', 'feature_key', 'value']


class PlanSerializer(serializers.ModelSerializer):
    """Plan serializer"""
    
    price_display = serializers.SerializerMethodField()
    feature_values = PlanFeatureValueSerializer(source='planfeaturevalue_set', many=True, read_only=True)
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'price', 'price_display',
            'currency', 'interval', 'stripe_price_id', 'stripe_product_id',
            'is_active', 'is_popular', 'feature_values',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_price_display(self, obj):
        return f"{obj.price} {obj.currency}/{obj.interval}"


class PlanCreateSerializer(serializers.ModelSerializer):
    """Plan creation serializer"""
    
    class Meta:
        model = Plan
        fields = [
            'name', 'description', 'price', 'currency', 'interval',
            'stripe_price_id', 'stripe_product_id', 'is_active', 'is_popular'
        ]
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be non-negative.")
        return value


class PlanUpdateSerializer(serializers.ModelSerializer):
    """Plan update serializer"""
    
    class Meta:
        model = Plan
        fields = [
            'name', 'description', 'price', 'currency', 'interval',
            'is_active', 'is_popular'
        ]
