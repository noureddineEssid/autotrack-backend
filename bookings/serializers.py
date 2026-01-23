"""
Serializers for booking system
"""

from rest_framework import serializers
from .models import GarageService, GarageAvailability, Booking, BookingReview


class GarageServiceSerializer(serializers.ModelSerializer):
    """Serializer for garage services"""
    
    garage_name = serializers.CharField(source='garage.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = GarageService
        fields = [
            'id', 'garage', 'garage_name', 'name', 'description',
            'category', 'category_display', 'duration_minutes', 'price',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GarageAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for garage availability"""
    
    garage_name = serializers.CharField(source='garage.name', read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = GarageAvailability
        fields = [
            'id', 'garage', 'garage_name', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'max_bookings_per_slot', 'is_active'
        ]
        read_only_fields = ['id']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for bookings"""
    
    garage_name = serializers.CharField(source='garage.name', read_only=True)
    garage_address = serializers.CharField(source='garage.address', read_only=True)
    garage_phone = serializers.CharField(source='garage.phone', read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_today = serializers.BooleanField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'garage', 'garage_name', 'garage_address', 'garage_phone',
            'vehicle', 'vehicle_display', 'service', 'service_name',
            'booking_date', 'booking_time', 'duration_minutes', 'status', 'status_display',
            'customer_name', 'customer_phone', 'customer_email', 'notes', 'garage_notes',
            'estimated_price', 'final_price', 'payment_status', 'payment_status_display',
            'created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at',
            'cancellation_reason', 'cancelled_by', 'reminder_sent', 'reminder_sent_at',
            'is_past', 'is_upcoming', 'is_today', 'can_cancel'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'confirmed_at',
            'completed_at', 'cancelled_at', 'cancelled_by', 'reminder_sent', 'reminder_sent_at'
        ]
    
    def get_vehicle_display(self, obj):
        """Get vehicle display name"""
        if obj.vehicle:
            return f"{obj.vehicle.brand} {obj.vehicle.model} - {obj.vehicle.registration_number}"
        return None
    
    def validate(self, data):
        """Validate booking data"""
        # Check if garage is open on selected date/time
        booking_date = data.get('booking_date')
        booking_time = data.get('booking_time')
        garage = data.get('garage')
        
        if booking_date and booking_time and garage:
            weekday = booking_date.weekday()
            availability = GarageAvailability.objects.filter(
                garage=garage,
                weekday=weekday,
                start_time__lte=booking_time,
                end_time__gte=booking_time,
                is_active=True
            ).first()
            
            if not availability:
                raise serializers.ValidationError({
                    'booking_time': 'Le garage n\'est pas disponible à cette date/heure'
                })
            
            # Check if slot is not fully booked
            existing_bookings = Booking.objects.filter(
                garage=garage,
                booking_date=booking_date,
                booking_time=booking_time,
                status__in=['pending', 'confirmed', 'in_progress']
            ).count()
            
            if existing_bookings >= availability.max_bookings_per_slot:
                raise serializers.ValidationError({
                    'booking_time': 'Ce créneau est complet'
                })
        
        return data


class CreateBookingSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings"""
    
    class Meta:
        model = Booking
        fields = [
            'garage', 'vehicle', 'service', 'booking_date', 'booking_time',
            'customer_name', 'customer_phone', 'customer_email', 'notes'
        ]
    
    def create(self, validated_data):
        """Create booking with user and estimated price"""
        # Get service to calculate duration and price
        service = validated_data.get('service')
        if service:
            validated_data['duration_minutes'] = service.duration_minutes
            validated_data['estimated_price'] = service.price
        
        # Set user from request
        validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)


class BookingReviewSerializer(serializers.ModelSerializer):
    """Serializer for booking reviews"""
    
    booking_details = serializers.SerializerMethodField()
    
    class Meta:
        model = BookingReview
        fields = [
            'id', 'booking', 'booking_details', 'rating', 'comment',
            'would_recommend', 'service_quality', 'waiting_time',
            'value_for_money', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_booking_details(self, obj):
        """Get booking details"""
        return {
            'garage_name': obj.booking.garage.name,
            'service_name': obj.booking.service.name if obj.booking.service else None,
            'booking_date': obj.booking.booking_date,
        }
    
    def validate(self, data):
        """Validate review"""
        booking = data.get('booking')
        
        # Check if booking is completed
        if booking.status != 'completed':
            raise serializers.ValidationError({
                'booking': 'Vous ne pouvez évaluer qu\'une réservation terminée'
            })
        
        # Check if review already exists
        if hasattr(booking, 'review') and self.instance is None:
            raise serializers.ValidationError({
                'booking': 'Vous avez déjà évalué cette réservation'
            })
        
        return data


class BookingStatsSerializer(serializers.Serializer):
    """Serializer for booking statistics"""
    
    total_bookings = serializers.IntegerField()
    pending = serializers.IntegerField()
    confirmed = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    completed = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    no_show = serializers.IntegerField()
    upcoming_7_days = serializers.IntegerField()
    today = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.FloatField()
    by_service = serializers.DictField()
    by_garage = serializers.DictField()


class AvailableSlotSerializer(serializers.Serializer):
    """Serializer for available time slots"""
    
    date = serializers.DateField()
    time = serializers.TimeField()
    available_spots = serializers.IntegerField()
    service_id = serializers.UUIDField(required=False)
    garage_id = serializers.UUIDField()
