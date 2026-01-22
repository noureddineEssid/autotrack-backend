from rest_framework import serializers
from .models import Garage, GarageReview
from django.db.models import Avg


class GarageReviewSerializer(serializers.ModelSerializer):
    """Garage review serializer"""
    
    class Meta:
        model = GarageReview
        fields = [
            'id', 'garage', 'reviewer_name', 'reviewer_email',
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class GarageSerializer(serializers.ModelSerializer):
    """Garage serializer"""
    
    reviews_count = serializers.IntegerField(source='total_reviews', read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Garage
        fields = [
            'id', 'name', 'email', 'phone', 'address', 'city',
            'postal_code', 'country', 'location', 'description',
            'specialties', 'certifications', 'average_rating',
            'total_reviews', 'reviews_count', 'recent_reviews',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'average_rating', 'total_reviews', 'created_at', 'updated_at']
    
    def get_recent_reviews(self, obj):
        recent = obj.reviews.all().order_by('-created_at')[:3]
        return GarageReviewSerializer(recent, many=True).data


class GarageCreateSerializer(serializers.ModelSerializer):
    """Garage creation serializer"""
    
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    
    class Meta:
        model = Garage
        fields = [
            'name', 'email', 'phone', 'address', 'city', 'postal_code',
            'country', 'latitude', 'longitude', 'description',
            'specialties', 'certifications'
        ]
    
    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        
        if latitude is not None and longitude is not None:
            validated_data['location'] = {
                'type': 'Point',
                'coordinates': [longitude, latitude]
            }
        
        return super().create(validated_data)


class GarageDetailSerializer(GarageSerializer):
    """Garage detail serializer with all reviews"""
    
    all_reviews = GarageReviewSerializer(source='reviews', many=True, read_only=True)
    
    class Meta(GarageSerializer.Meta):
        fields = GarageSerializer.Meta.fields + ['all_reviews']


class GarageUpdateSerializer(serializers.ModelSerializer):
    """Garage update serializer"""
    
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    
    class Meta:
        model = Garage
        fields = [
            'name', 'email', 'phone', 'address', 'city', 'postal_code',
            'country', 'latitude', 'longitude', 'description',
            'specialties', 'certifications'
        ]
    
    def update(self, instance, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        
        if latitude is not None and longitude is not None:
            validated_data['location'] = {
                'type': 'Point',
                'coordinates': [longitude, latitude]
            }
        
        return super().update(instance, validated_data)
