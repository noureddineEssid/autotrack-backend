from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Vehicle, CarBrand, CarModel
from .serializers import (
    VehicleSerializer, VehicleCreateSerializer, VehicleDetailSerializer,
    CarBrandSerializer, CarModelSerializer
)


class CarBrandViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing car brands
    
    list: Get all car brands
    create: Create a new car brand
    retrieve: Get a specific car brand
    update: Update a car brand
    destroy: Delete a car brand
    """
    queryset = CarBrand.objects.all()
    serializer_class = CarBrandSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def models(self, request, pk=None):
        """Get all models for a specific brand"""
        brand = self.get_object()
        models = brand.models.all()
        serializer = CarModelSerializer(models, many=True)
        return Response(serializer.data)


class CarModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing car models
    
    list: Get all car models
    create: Create a new car model
    retrieve: Get a specific car model
    update: Update a car model
    destroy: Delete a car model
    """
    queryset = CarModel.objects.select_related('brand').all()
    serializer_class = CarModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['brand', 'year_start', 'year_end']
    search_fields = ['name', 'brand__name']
    ordering_fields = ['name', 'year_start', 'created_at']
    ordering = ['brand__name', 'name']


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vehicles
    
    list: Get all vehicles for the authenticated user
    create: Create a new vehicle
    retrieve: Get a specific vehicle
    update: Update a vehicle
    partial_update: Partially update a vehicle
    destroy: Delete a vehicle
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['make', 'model', 'year', 'fuel_type', 'transmission']
    search_fields = ['make', 'model', 'license_plate', 'vin']
    ordering_fields = ['make', 'model', 'year', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter vehicles by owner"""
        return Vehicle.objects.filter(owner=self.request.user).select_related('owner')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return VehicleCreateSerializer
        elif self.action == 'retrieve':
            return VehicleDetailSerializer
        return VehicleSerializer
    
    def perform_create(self, serializer):
        """Set owner to current user"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def maintenances(self, request, pk=None):
        """Get all maintenances for this vehicle"""
        vehicle = self.get_object()
        maintenances = vehicle.maintenances.all().order_by('-service_date')
        
        # Import here to avoid circular dependency
        from maintenances.serializers import MaintenanceSerializer
        serializer = MaintenanceSerializer(maintenances, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents for this vehicle"""
        vehicle = self.get_object()
        documents = vehicle.documents.all().order_by('-created_at')
        
        # Import here to avoid circular dependency
        from documents.serializers import DocumentSerializer
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def diagnostics(self, request, pk=None):
        """Get all diagnostics for this vehicle"""
        vehicle = self.get_object()
        diagnostics = vehicle.diagnostics.all().order_by('-created_at')
        
        # Import here to avoid circular dependency
        from diagnostics.serializers import DiagnosticSerializer
        serializer = DiagnosticSerializer(diagnostics, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get vehicle statistics for the user"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        by_fuel_type = {}
        by_transmission = {}
        
        for vehicle in queryset:
            if vehicle.fuel_type:
                by_fuel_type[vehicle.fuel_type] = by_fuel_type.get(vehicle.fuel_type, 0) + 1
            if vehicle.transmission:
                by_transmission[vehicle.transmission] = by_transmission.get(vehicle.transmission, 0) + 1
        
        return Response({
            'total': total,
            'by_fuel_type': by_fuel_type,
            'by_transmission': by_transmission
        })

