from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Q
from .models import Diagnostic, DiagnosticReply
from .serializers import (
    DiagnosticSerializer, DiagnosticCreateSerializer, DiagnosticDetailSerializer,
    DiagnosticUpdateSerializer, DiagnosticReplySerializer, DiagnosticReplyCreateSerializer
)


class DiagnosticViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing diagnostics
    
    list: Get all diagnostics for current user
    create: Create a new diagnostic
    retrieve: Get a specific diagnostic
    update: Update a diagnostic
    partial_update: Partially update a diagnostic
    destroy: Delete a diagnostic
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehicle', 'status']
    search_fields = ['title', 'description', 'vehicle__make', 'vehicle__model']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter diagnostics by user"""
        return Diagnostic.objects.filter(
            user=self.request.user
        ).select_related('vehicle').prefetch_related('replies')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return DiagnosticCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DiagnosticUpdateSerializer
        elif self.action == 'retrieve':
            return DiagnosticDetailSerializer
        return DiagnosticSerializer
    
    @action(detail=True, methods=['post'])
    def add_reply(self, request, pk=None):
        """Add a reply to a diagnostic"""
        diagnostic = self.get_object()
        
        data = request.data.copy()
        data['diagnostic'] = diagnostic.id
        data['is_ai_response'] = False
        
        serializer = DiagnosticReplyCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def request_ai_analysis(self, request, pk=None):
        """Request AI analysis for a diagnostic"""
        diagnostic = self.get_object()
        
        # TODO: Trigger AI analysis via Celery
        # from diagnostics.tasks import analyze_diagnostic_with_ai
        # task = analyze_diagnostic_with_ai.delay(diagnostic.id)
        
        return Response({
            'message': 'AI analysis requested. You will receive a response shortly.',
            'diagnostic_id': diagnostic.id
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending diagnostics"""
        queryset = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed diagnostics"""
        queryset = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get diagnostic statistics"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        by_status = queryset.values('status').annotate(count=Count('id'))
        
        avg_confidence = queryset.filter(
            confidence_score__isnull=False
        ).aggregate(avg=Avg('confidence_score'))
        
        return Response({
            'total_diagnostics': total,
            'by_status': list(by_status),
            'average_confidence_score': round(avg_confidence['avg'] or 0, 2)
        })
    
    @action(detail=False, methods=['get'])
    def by_vehicle(self, request):
        """Get diagnostics grouped by vehicle"""
        vehicle_id = request.query_params.get('vehicle_id')
        
        if vehicle_id:
            queryset = self.get_queryset().filter(vehicle_id=vehicle_id)
        else:
            queryset = self.get_queryset()
        
        # Group by vehicle
        vehicles = {}
        for diagnostic in queryset:
            vehicle_key = str(diagnostic.vehicle.id)
            if vehicle_key not in vehicles:
                vehicles[vehicle_key] = {
                    'vehicle': {
                        'id': diagnostic.vehicle.id,
                        'make': diagnostic.vehicle.make,
                        'model': diagnostic.vehicle.model,
                        'year': diagnostic.vehicle.year
                    },
                    'diagnostics': []
                }
            vehicles[vehicle_key]['diagnostics'].append(
                DiagnosticSerializer(diagnostic).data
            )
        
        return Response(list(vehicles.values()))


class DiagnosticReplyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing diagnostic replies
    
    list: Get all replies for current user's diagnostics
    create: Create a new reply
    retrieve: Get a specific reply
    update: Update a reply
    destroy: Delete a reply
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DiagnosticReplySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['diagnostic', 'is_ai_response']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter replies by diagnostic owner (current user)"""
        return DiagnosticReply.objects.filter(
            diagnostic__user=self.request.user
        ).select_related('diagnostic', 'diagnostic__vehicle', 'sender')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return DiagnosticReplyCreateSerializer
        return DiagnosticReplySerializer
