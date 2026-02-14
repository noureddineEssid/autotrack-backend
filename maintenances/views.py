from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from .models import Maintenance
from .serializers import (
    MaintenanceSerializer, MaintenanceCreateSerializer,
    MaintenanceDetailSerializer, MaintenanceUpdateSerializer
)
from subscriptions.limits import enforce_limit


class MaintenanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vehicle maintenances
    
    list: Get all maintenances for user's vehicles
    create: Create a new maintenance record
    retrieve: Get a specific maintenance
    update: Update a maintenance
    partial_update: Partially update a maintenance
    destroy: Delete a maintenance
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehicle', 'status', 'service_type']
    search_fields = ['service_type', 'description', 'vehicle__make', 'vehicle__model']
    ordering_fields = ['service_date', 'cost', 'mileage', 'created_at']
    ordering = ['-service_date']
    
    def get_queryset(self):
        """Filter maintenances by user's vehicles"""
        return Maintenance.objects.filter(
            vehicle__owner=self.request.user
        ).select_related('vehicle', 'created_by', 'performed_by')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MaintenanceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MaintenanceUpdateSerializer
        elif self.action == 'retrieve':
            return MaintenanceDetailSerializer
        return MaintenanceSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        enforce_limit(self.request.user, 'maintenances', amount=1)
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming scheduled maintenances"""
        queryset = self.get_queryset().filter(
            status='SCHEDULED',
            service_date__gte=datetime.now()
        ).order_by('service_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent completed maintenances (last 30 days)"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        queryset = self.get_queryset().filter(
            status='COMPLETED',
            service_date__gte=thirty_days_ago
        ).order_by('-service_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get maintenance statistics"""
        queryset = self.get_queryset()
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(service_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(service_date__lte=end_date)
        
        stats = queryset.aggregate(
            total_count=Count('id'),
            total_cost=Sum('cost'),
            average_cost=Avg('cost'),
            scheduled_count=Count('id', filter=Q(status='SCHEDULED')),
            completed_count=Count('id', filter=Q(status='COMPLETED')),
            in_progress_count=Count('id', filter=Q(status='IN_PROGRESS'))
        )
        
        # Top service types
        top_services = queryset.values('service_type').annotate(
            count=Count('id'),
            total_cost=Sum('cost')
        ).order_by('-count')[:5]
        
        return Response({
            'overview': stats,
            'top_services': list(top_services)
        })
    
    @action(detail=False, methods=['get'])
    def by_vehicle(self, request):
        """Get maintenances grouped by vehicle"""
        vehicle_id = request.query_params.get('vehicle_id')
        
        if vehicle_id:
            queryset = self.get_queryset().filter(vehicle_id=vehicle_id)
        else:
            queryset = self.get_queryset()
        
        # Group by vehicle
        vehicles_data = {}
        for maintenance in queryset:
            vehicle_key = str(maintenance.vehicle.id)
            if vehicle_key not in vehicles_data:
                vehicles_data[vehicle_key] = {
                    'vehicle': {
                        'id': maintenance.vehicle.id,
                        'make': maintenance.vehicle.make,
                        'model': maintenance.vehicle.model,
                        'year': maintenance.vehicle.year
                    },
                    'maintenances': [],
                    'total_cost': 0,
                    'count': 0
                }
            
            vehicles_data[vehicle_key]['maintenances'].append(
                MaintenanceSerializer(maintenance).data
            )
            vehicles_data[vehicle_key]['count'] += 1
            if maintenance.cost:
                vehicles_data[vehicle_key]['total_cost'] += float(maintenance.cost)
        
        return Response(list(vehicles_data.values()))

