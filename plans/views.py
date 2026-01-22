from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Plan
from .serializers import (
    PlanSerializer, PlanCreateSerializer, PlanUpdateSerializer
)


class PlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscription plans
    
    list: Get all active plans
    create: Create a new plan (admin only)
    retrieve: Get a specific plan
    update: Update a plan (admin only)
    partial_update: Partially update a plan (admin only)
    destroy: Delete a plan (admin only)
    """
    queryset = Plan.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['interval', 'is_active', 'is_popular']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    ordering = ['price']
    
    def get_permissions(self):
        """Allow anyone to view plans, but require admin for create/update/delete"""
        if self.action in ['list', 'retrieve', 'active_plans', 'popular']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        """Show only active plans to non-admin users"""
        if self.request.user.is_staff:
            return Plan.objects.all()
        return Plan.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return PlanCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PlanUpdateSerializer
        return PlanSerializer
    
    @action(detail=False, methods=['get'])
    def active_plans(self, request):
        """Get all active plans"""
        queryset = Plan.objects.filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_interval(self, request):
        """Get plans grouped by billing interval"""
        interval = request.query_params.get('interval')
        
        if interval:
            queryset = self.get_queryset().filter(interval=interval)
        else:
            queryset = self.get_queryset()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular plans"""
        queryset = self.get_queryset().filter(
            is_active=True,
            is_popular=True
        ).order_by('price')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
