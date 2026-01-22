from rest_framework import serializers
from .models import Subscription
from plans.serializers import PlanSerializer
from users.serializers import UserSerializer


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscription serializer"""
    
    plan_info = PlanSerializer(source='plan', read_only=True)
    user_info = serializers.SerializerMethodField()
    days_until_renewal = serializers.SerializerMethodField()
    is_trial_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_info', 'plan', 'plan_info', 'status',
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
        fields = ['plan']
    
    def validate_plan(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This plan is not available.")
        return value
    
    def create(self, validated_data):
        # Ajouter l'utilisateur de la requête
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
            validated_data['stripe_customer_id'] = request.user.stripe_customer_id or ''
        
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
