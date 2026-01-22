from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Q
from .models import Garage, GarageReview
from .serializers import (
    GarageSerializer, GarageCreateSerializer, GarageDetailSerializer,
    GarageUpdateSerializer, GarageReviewSerializer
)
import math


class GarageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing garages
    
    list: Get all garages
    create: Create a new garage
    retrieve: Get a specific garage
    update: Update a garage
    partial_update: Partially update a garage
    destroy: Delete a garage
    """
    queryset = Garage.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'postal_code', 'country']
    search_fields = ['name', 'address', 'city', 'specialties']
    ordering_fields = ['name', 'average_rating', 'total_reviews', 'created_at']
    ordering = ['-average_rating', 'name']
    
    def get_permissions(self):
        """Allow anyone to view garages, but require auth for create/update/delete"""
        if self.action in ['list', 'retrieve', 'search_nearby', 'top_rated']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return GarageCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return GarageUpdateSerializer
        elif self.action == 'retrieve':
            return GarageDetailSerializer
        return GarageSerializer
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """Add a review to a garage"""
        garage = self.get_object()
        
        serializer = GarageReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(garage=garage)
            
            # Update garage rating
            avg_rating = garage.reviews.aggregate(Avg('rating'))['rating__avg']
            garage.average_rating = avg_rating or 0
            garage.total_reviews = garage.reviews.count()
            garage.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top rated garages"""
        limit = int(request.query_params.get('limit', 10))
        queryset = self.get_queryset().filter(
            total_reviews__gte=3
        ).order_by('-average_rating')[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search_nearby(self, request):
        """
        Search garages nearby based on coordinates
        Query params: lat, lng, radius (in km, default 10)
        """
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            radius = float(request.query_params.get('radius', 10))
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid coordinates. Please provide lat and lng parameters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simple distance calculation (not precise for large distances)
        # For production, consider using PostGIS or more accurate geospatial queries
        garages = []
        for garage in self.get_queryset():
            if garage.location and 'coordinates' in garage.location:
                g_lng, g_lat = garage.location['coordinates']
                
                # Calculate approximate distance using Haversine formula
                distance = self._calculate_distance(lat, lng, g_lat, g_lng)
                
                if distance <= radius:
                    garage_data = GarageSerializer(garage).data
                    garage_data['distance_km'] = round(distance, 2)
                    garages.append(garage_data)
        
        # Sort by distance
        garages.sort(key=lambda x: x['distance_km'])
        
        return Response(garages)
    
    @action(detail=False, methods=['get'])
    def by_specialty(self, request):
        """Get garages grouped by specialty"""
        specialty = request.query_params.get('specialty')
        
        if specialty:
            queryset = self.get_queryset().filter(
                specialties__contains=[specialty]
            )
        else:
            queryset = self.get_queryset()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula (in km)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c


class GarageReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing garage reviews
    
    list: Get all reviews
    create: Create a new review
    retrieve: Get a specific review
    update: Update a review
    destroy: Delete a review
    """
    queryset = GarageReview.objects.select_related('garage').all()
    serializer_class = GarageReviewSerializer
    permission_classes = [AllowAny]  # Allow anyone to view/create reviews
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['garage', 'rating']
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Update garage rating after creating review"""
        review = serializer.save()
        garage = review.garage
        
        # Update garage rating
        avg_rating = garage.reviews.aggregate(Avg('rating'))['rating__avg']
        garage.average_rating = avg_rating or 0
        garage.total_reviews = garage.reviews.count()
        garage.save()
    
    def perform_destroy(self, instance):
        """Update garage rating after deleting review"""
        garage = instance.garage
        instance.delete()
        
        # Update garage rating
        avg_rating = garage.reviews.aggregate(Avg('rating'))['rating__avg']
        garage.average_rating = avg_rating or 0
        garage.total_reviews = garage.reviews.count()
        garage.save()

