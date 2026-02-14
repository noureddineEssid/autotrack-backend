from rest_framework import serializers
from .models import Subscription, SubscriptionHistory
from users.serializers import UserSerializer


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscription serializer"""
    
    user_info = serializers.SerializerMethodField()
    days_until_renewal = serializers.SerializerMethodField()
    is_trial_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_info', 'plan_code', 'plan_name', 'status',
            'stripe_subscription_id', 'stripe_customer_id', 'current_period_start',
            'current_period_end', 'cancel_at_period_end', 'trial_start', 'trial_end',
            'days_until_renewal', 'is_trial_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'stripe_subscription_id', 'stripe_customer_id',
            'current_period_start', 'current_period_end', 'trial_start',
            'trial_end', 'created_at', 'updated_at'
        ]
    
    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name
        }
    
    def get_days_until_renewal(self, obj):
        if obj.current_period_end:
            from datetime import date
            today = date.today()
            delta = (obj.current_period_end - today).days
            return max(0, delta)
        return None
    
    def get_is_trial_active(self, obj):
        if obj.trial_start and obj.trial_end:
            from datetime import date
            today = date.today()
            return obj.trial_start <= today <= obj.trial_end
        return False


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Subscription creation serializer"""
    
    class Meta:
        model = Subscription
        fields = ['plan_code', 'plan_name']
    
    def create(self, validated_data):
        # Ajouter l'utilisateur de la requête
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
            validated_data['stripe_customer_id'] = request.user.stripe_customer_id or ''

        from django.utils import timezone
        from datetime import timedelta

        validated_data.setdefault('status', 'active')
        validated_data.setdefault('current_period_start', timezone.now())
        validated_data.setdefault('current_period_end', timezone.now() + timedelta(days=30))
        
        # TODO: Create Stripe subscription via Celery
        # from subscriptions.tasks import create_stripe_subscription
        # subscription = super().create(validated_data)
        # create_stripe_subscription.delay(subscription.id)
        # return subscription
        
        return super().create(validated_data)


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """Subscription update serializer"""
    
    class Meta:
        model = Subscription
        fields = ['status', 'cancel_at_period_end']


class SubscriptionHistorySerializer(serializers.ModelSerializer):
    """Subscription history serializer"""

    class Meta:
        model = SubscriptionHistory
        fields = ['id', 'event_type', 'previous_status', 'new_status', 'metadata', 'created_at']
