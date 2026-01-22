from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import date
from .models import Subscription
from .serializers import (
    SubscriptionSerializer, SubscriptionCreateSerializer,
    SubscriptionUpdateSerializer
)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscriptions
    
    list: Get all subscriptions for current user
    create: Create a new subscription
    retrieve: Get a specific subscription
    update: Update a subscription
    partial_update: Partially update a subscription
    destroy: Delete a subscription
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'plan', 'cancel_at_period_end']
    ordering_fields = ['created_at', 'current_period_end']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter subscriptions by user"""
        if self.request.user.is_staff:
            return Subscription.objects.select_related('user', 'plan').all()
        return Subscription.objects.filter(user=self.request.user).select_related('plan')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return SubscriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active subscription for current user"""
        subscription = self.get_queryset().filter(
            status='active'
        ).order_by('-created_at').first()
        
        if subscription:
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        
        return Response({
            'message': 'No active subscription found.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel subscription at period end"""
        subscription = self.get_object()
        
        if subscription.status != 'active':
            return Response(
                {'error': 'Only active subscriptions can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.cancel_at_period_end = True
        subscription.save()
        
        # TODO: Cancel Stripe subscription via Celery
        # from subscriptions.tasks import cancel_stripe_subscription
        # cancel_stripe_subscription.delay(subscription.id)
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a cancelled subscription"""
        subscription = self.get_object()
        
        if not subscription.cancel_at_period_end:
            return Response(
                {'error': 'Subscription is not scheduled for cancellation.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.cancel_at_period_end = False
        subscription.save()
        
        # TODO: Reactivate Stripe subscription via Celery
        # from subscriptions.tasks import reactivate_stripe_subscription
        # reactivate_stripe_subscription.delay(subscription.id)
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_plan(self, request, pk=None):
        """Change subscription plan"""
        subscription = self.get_object()
        new_plan_id = request.data.get('plan_id')
        
        if not new_plan_id:
            return Response(
                {'error': 'plan_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from plans.models import Plan
        try:
            new_plan = Plan.objects.get(id=new_plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {'error': 'Plan not found or inactive.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        subscription.plan = new_plan
        subscription.save()
        
        # TODO: Update Stripe subscription via Celery
        # from subscriptions.tasks import update_stripe_subscription
        # update_stripe_subscription.delay(subscription.id, new_plan.id)
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get subscription statistics (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        all_subs = Subscription.objects.all()
        
        total = all_subs.count()
        by_status = all_subs.values('status').annotate(count=Count('id'))
        by_plan = all_subs.values('plan__name').annotate(count=Count('id'))
        
        active = all_subs.filter(status='active').count()
        trialing = all_subs.filter(status='trialing').count()
        cancelled = all_subs.filter(cancel_at_period_end=True).count()
        
        return Response({
            'total_subscriptions': total,
            'active': active,
            'trialing': trialing,
            'scheduled_for_cancellation': cancelled,
            'by_status': list(by_status),
            'by_plan': list(by_plan)
        })
