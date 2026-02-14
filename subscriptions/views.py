from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone
from .models import Subscription, SubscriptionHistory
from .serializers import (
    SubscriptionSerializer, SubscriptionCreateSerializer,
    SubscriptionUpdateSerializer, SubscriptionHistorySerializer
)
from .plan_catalog import list_plans, get_plan, PLAN_HIERARCHY
from .limits import get_usage_counts, get_plan_limits


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
    filterset_fields = ['status', 'plan_code', 'cancel_at_period_end']
    ordering_fields = ['created_at', 'current_period_end']
    ordering = ['-created_at']

    def _get_or_create_subscription(self, user):
        subscription = Subscription.objects.filter(user=user).order_by('-created_at').first()
        if subscription:
            return subscription

        now = timezone.now()
        subscription = Subscription.objects.create(
            user=user,
            plan_code='free',
            plan_name='Gratuit',
            status='active',
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        SubscriptionHistory.objects.create(
            subscription=subscription,
            event_type='created',
            new_status='active',
            metadata={'plan_code': 'free'}
        )
        return subscription

    def _record_history(self, subscription, event_type, previous_status=None, new_status=None, metadata=None):
        SubscriptionHistory.objects.create(
            subscription=subscription,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            metadata=metadata or {},
        )

    def _get_active_subscription(self, user):
        subscription = Subscription.objects.filter(user=user, status='active').order_by('-created_at').first()
        return subscription or self._get_or_create_subscription(user)

    def _serialize_subscription(self, subscription):
        plan = get_plan(subscription.plan_code) or get_plan('free')
        interval = 'monthly'
        amount = plan.get('monthlyPrice', 0)

        return {
            '_id': str(subscription.id),
            'user': str(subscription.user.id),
            'plan': plan,
            'status': subscription.status,
            'interval': interval,
            'amount': amount,
            'startDate': subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            'endDate': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            'cancelAtPeriodEnd': subscription.cancel_at_period_end,
            'canceledAt': subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            'stripeCustomerId': subscription.stripe_customer_id,
            'stripeSubscriptionId': subscription.stripe_subscription_id,
        }
    
    def get_queryset(self):
        """Filter subscriptions by user"""
        if self.request.user.is_staff:
            return Subscription.objects.select_related('user').all()
        return Subscription.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return SubscriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        """Get current subscription for user"""
        subscription = self._get_active_subscription(request.user)
        return Response(self._serialize_subscription(subscription))

    @action(detail=False, methods=['get'], url_path='plans', permission_classes=[AllowAny])
    def plans(self, request):
        """Return available subscription plans"""
        return Response(list_plans())

    @action(detail=False, methods=['get'], url_path='usage')
    def usage(self, request):
        """Return usage stats and limits for current plan"""
        subscription = self._get_active_subscription(request.user)
        plan_limits = get_plan_limits(subscription.plan_code)
        usage = get_usage_counts(request.user)

        def _build_resource(current, limit, unit_label=''):
            if limit == -1:
                return {
                    'current': current,
                    'limit': -1,
                    'percentage': 0,
                    'limitLabel': 'Illimité',
                }
            percentage = 0 if limit == 0 else min((current / limit) * 100, 100)
            return {
                'current': current,
                'limit': limit,
                'percentage': percentage,
                'limitLabel': f"{limit}{unit_label}",
            }

        storage_limit_mb = plan_limits.get('storage_mb', -1)
        storage_current_mb = round(usage['storage_bytes'] / 1024 / 1024, 2) if usage['storage_bytes'] else 0
        storage_resource = _build_resource(storage_current_mb, storage_limit_mb, ' Mo')
        storage_resource.update({
            'currentMB': storage_current_mb,
            'limitMB': storage_limit_mb,
        })

        usage_payload = {
            'plan': {
                'name': subscription.plan_name,
                'type': subscription.plan_code,
            },
            'usage': {
                'vehicles': _build_resource(usage['vehicles'], plan_limits.get('vehicles', -1)),
                'storage': storage_resource,
                'diagnostics': _build_resource(usage['diagnostics'], plan_limits.get('diagnostics', -1)),
                'maintenances': _build_resource(usage['maintenances'], plan_limits.get('maintenances', -1)),
                'documents': _build_resource(usage['documents'], plan_limits.get('documents', -1)),
            },
        }

        warnings = []
        for key, resource in usage_payload['usage'].items():
            if resource['limit'] != -1 and resource['percentage'] >= 80:
                warnings.append(f"Vous approchez de la limite pour {key}.")

        usage_payload['warnings'] = warnings

        return Response(usage_payload)

    @action(detail=False, methods=['get'], url_path='check-limits')
    def check_limits(self, request):
        """Check limits for a resource"""
        resource = request.query_params.get('resource')
        amount = int(request.query_params.get('amount', '1'))
        extra_bytes = int(request.query_params.get('bytes', '0'))

        subscription = self._get_active_subscription(request.user)
        plan_limits = get_plan_limits(subscription.plan_code)
        usage = get_usage_counts(request.user)

        if resource == 'storage':
            limit_mb = plan_limits.get('storage_mb', -1)
            current_bytes = usage['storage_bytes']
            if limit_mb == -1:
                return Response({'allowed': True, 'limit': -1, 'current': current_bytes})
            limit_bytes = limit_mb * 1024 * 1024
            allowed = current_bytes + extra_bytes <= limit_bytes
            return Response({
                'allowed': allowed,
                'limit': limit_bytes,
                'limit_mb': limit_mb,
                'current': current_bytes,
                'requested_bytes': extra_bytes,
            })

        limit = plan_limits.get(resource, -1)
        current = usage.get(resource, 0)
        allowed = True if limit == -1 else (current + amount <= limit)
        return Response({
            'allowed': allowed,
            'limit': limit,
            'current': current,
            'requested': amount,
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active subscription for current user"""
        subscription = self._get_active_subscription(request.user)
        
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

    @action(detail=False, methods=['post'], url_path='cancel')
    def cancel_current(self, request):
        """Cancel current subscription"""
        subscription = self._get_active_subscription(request.user)
        immediate = request.data.get('immediate', False)

        if immediate:
            previous_status = subscription.status
            subscription.status = 'cancelled'
            subscription.cancel_at_period_end = False
            subscription.cancelled_at = timezone.now()
            self._record_history(
                subscription,
                event_type='cancelled',
                previous_status=previous_status,
                new_status='cancelled',
            )
        else:
            subscription.cancel_at_period_end = True
            self._record_history(
                subscription,
                event_type='cancel_scheduled',
                previous_status=subscription.status,
                new_status=subscription.status,
            )

        subscription.save()

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

    @action(detail=False, methods=['post'], url_path='resume')
    def resume(self, request):
        """Resume current subscription"""
        subscription = self._get_active_subscription(request.user)

        subscription.cancel_at_period_end = False
        if subscription.status == 'cancelled':
            previous_status = subscription.status
            subscription.status = 'active'
            subscription.cancelled_at = None
            self._record_history(
                subscription,
                event_type='resumed',
                previous_status=previous_status,
                new_status='active',
            )
        subscription.save()

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_plan(self, request, pk=None):
        """Change subscription plan"""
        subscription = self.get_object()
        new_plan_code = request.data.get('plan_code')
        new_plan_name = request.data.get('plan_name')

        if not new_plan_code or not new_plan_name:
            return Response(
                {'error': 'plan_code and plan_name are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.plan_code = new_plan_code
        subscription.plan_name = new_plan_name
        subscription.save()
        
        # TODO: Update Stripe subscription via Celery
        # from subscriptions.tasks import update_stripe_subscription
        # update_stripe_subscription.delay(subscription.id, new_plan.id)
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='change-plan')
    def change_plan_current(self, request):
        """Change current subscription plan"""
        subscription = self._get_active_subscription(request.user)

        plan_code = request.data.get('plan_code') or request.data.get('newPlanId') or request.data.get('plan')
        plan = get_plan(plan_code)
        if not plan:
            return Response({'message': 'Plan invalide'}, status=status.HTTP_400_BAD_REQUEST)

        current_plan_code = subscription.plan_code
        current_level = PLAN_HIERARCHY.get(current_plan_code, 0)
        new_level = PLAN_HIERARCHY.get(plan['type'], 0)

        usage = get_usage_counts(request.user)
        limits = plan['limits']

        violations = []
        warnings = []

        def _check(resource_key, current_value, new_limit, label):
            if new_limit == -1:
                return
            if current_value > new_limit:
                violations.append({
                    'resource': resource_key,
                    'current': current_value,
                    'newLimit': new_limit,
                    'message': f"{label} dépasse la limite du nouveau plan.",
                    'action': 'reduce',
                })
            elif new_limit > 0 and current_value >= new_limit * 0.8:
                warnings.append(f"{label} proche de la limite ({current_value}/{new_limit}).")

        _check('vehicles', usage['vehicles'], limits.get('vehicles', -1), 'Véhicules')
        _check('documents', usage['documents'], limits.get('documents', -1), 'Documents')
        _check('maintenances', usage['maintenances'], limits.get('maintenances', -1), 'Maintenances')
        _check('diagnostics', usage['diagnostics'], limits.get('diagnostics', -1), 'Diagnostics')

        storage_limit = limits.get('storage_mb', -1)
        storage_current_mb = round(usage['storage_bytes'] / 1024 / 1024, 2) if usage['storage_bytes'] else 0
        if storage_limit != -1 and storage_current_mb > storage_limit:
            violations.append({
                'resource': 'storage',
                'current': storage_current_mb,
                'newLimit': storage_limit,
                'message': 'Stockage dépasse la limite du nouveau plan.',
                'action': 'reduce',
            })
        elif storage_limit != -1 and storage_current_mb >= storage_limit * 0.8:
            warnings.append(f"Stockage proche de la limite ({storage_current_mb}/{storage_limit} Mo).")

        if violations:
            return Response({
                'canChange': False,
                'violations': violations,
                'warnings': warnings,
            }, status=status.HTTP_400_BAD_REQUEST)

        immediate = request.data.get('immediate', True)

        previous_plan = subscription.plan_code
        subscription.plan_code = plan['type']
        subscription.plan_name = plan['name']
        subscription.status = 'active'
        subscription.cancel_at_period_end = False
        subscription.save()

        self._record_history(
            subscription,
            event_type='plan_changed',
            previous_status=subscription.status,
            new_status=subscription.status,
            metadata={'from': previous_plan, 'to': plan['type']},
        )

        response_data = self._serialize_subscription(subscription)
        if not immediate and new_level < current_level:
            response_data['pendingPlan'] = plan
            response_data['pendingPlanEffectiveDate'] = subscription.current_period_end.isoformat() if subscription.current_period_end else None

        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        """Return subscription history for current user"""
        subscription = self._get_active_subscription(request.user)
        history = subscription.history.all().order_by('-created_at')
        serializer = SubscriptionHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='invoices')
    def invoices(self, request):
        """Return invoices (placeholder)"""
        return Response([])
    
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
        by_plan = all_subs.values('plan_name').annotate(count=Count('id'))
        
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
