from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from .models import WebhookEvent
from .serializers import WebhookEventSerializer
import json
import stripe


class WebhookEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing webhook events (admin only)
    
    list: Get all webhook events
    retrieve: Get a specific webhook event
    """
    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'source', 'processed']
    ordering = ['-created_at']
    http_method_names = ['get', 'head', 'options']  # Read-only
    
    @action(detail=False, methods=['get'])
    def unprocessed(self, request):
        """Get unprocessed webhook events"""
        queryset = self.get_queryset().filter(processed=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def errors(self, request):
        """Get webhook events with errors"""
        queryset = self.get_queryset().exclude(error_message__isnull=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    
    Stripe sends webhooks for various events like:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Log the webhook event
    webhook_event = WebhookEvent.objects.create(
        event_type=event['type'],
        payload=event,
        source='stripe',
        processed=False
    )
    
    # TODO: Process webhook asynchronously via Celery
    # from webhooks.tasks import process_stripe_webhook
    # process_stripe_webhook.delay(webhook_event.id)
    
    # For now, process synchronously
    try:
        _process_stripe_event(event, webhook_event)
    except Exception as e:
        webhook_event.error_message = str(e)
        webhook_event.save()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({'status': 'success'})


def _process_stripe_event(event, webhook_event):
    """Process Stripe webhook event"""
    from subscriptions.models import Subscription
    from django.utils import timezone
    
    event_type = event['type']
    data = event['data']['object']
    
    if event_type == 'customer.subscription.created':
        # Handle subscription creation
        subscription_id = data['id']
        customer_id = data['customer']
        
        # Find and update subscription
        try:
            subscription = Subscription.objects.get(stripe_customer_id=customer_id)
            subscription.stripe_subscription_id = subscription_id
            subscription.status = data['status']
            subscription.current_period_start = timezone.datetime.fromtimestamp(data['current_period_start'])
            subscription.current_period_end = timezone.datetime.fromtimestamp(data['current_period_end'])
            subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    elif event_type == 'customer.subscription.updated':
        # Handle subscription update
        subscription_id = data['id']
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = data['status']
            subscription.current_period_start = timezone.datetime.fromtimestamp(data['current_period_start'])
            subscription.current_period_end = timezone.datetime.fromtimestamp(data['current_period_end'])
            subscription.cancel_at_period_end = data.get('cancel_at_period_end', False)
            subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    elif event_type == 'customer.subscription.deleted':
        # Handle subscription cancellation
        subscription_id = data['id']
        
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.status = 'canceled'
            subscription.save()
        except Subscription.DoesNotExist:
            pass
    
    elif event_type == 'invoice.payment_succeeded':
        # Handle successful payment
        # TODO: Send notification to user
        pass
    
    elif event_type == 'invoice.payment_failed':
        # Handle failed payment
        # TODO: Send notification to user
        pass
    
    # Mark webhook as processed
    webhook_event.processed = True
    webhook_event.processed_at = timezone.now()
    webhook_event.save()

