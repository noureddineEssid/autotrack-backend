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



