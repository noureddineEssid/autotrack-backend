"""
Statistics Views - Comprehensive analytics and reporting
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import io
from django.http import FileResponse

from .serializers import (
    OverviewStatsSerializer,
    CostBreakdownSerializer,
    MonthlyTrendSerializer,
    VehicleStatsSerializer,
    MaintenanceStatsSerializer,
    DiagnosticStatsSerializer,
    CostComparisonSerializer,
    ExportRequestSerializer,
)
from vehicles.models import Vehicle
from maintenances.models import Maintenance
from diagnostics.models import Diagnostic
from documents.models import Document


class StatisticsViewSet(viewsets.ViewSet):
    """
    Statistics ViewSet - Provides comprehensive analytics
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Get overall statistics overview
        GET /api/statistics/overview/
        """
        user = request.user
        now = timezone.now()
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Total counts
        total_vehicles = Vehicle.objects.filter(user=user).count()
        total_maintenances = Maintenance.objects.filter(vehicle__user=user).count()
        total_diagnostics = Diagnostic.objects.filter(vehicle__user=user).count()
        total_documents = Document.objects.filter(vehicle__user=user).count()
        
        # Pending/Critical
        pending_maintenances = Maintenance.objects.filter(
            vehicle__user=user,
            status__in=['scheduled', 'pending']
        ).count()
        
        critical_diagnostics = Diagnostic.objects.filter(
            vehicle__user=user,
            severity='critical',
            status='unresolved'
        ).count()
        
        expiring_documents = Document.objects.filter(
            vehicle__user=user,
            expiration_date__lte=now + timedelta(days=30),
            expiration_date__gte=now
        ).count()
        
        # Costs
        maintenances_ytd = Maintenance.objects.filter(
            vehicle__user=user,
            completed_at__gte=year_start
        ).aggregate(total=Sum('cost'))['total'] or Decimal('0.00')
        
        diagnostics_ytd = Diagnostic.objects.filter(
            vehicle__user=user,
            created_at__gte=year_start
        ).aggregate(total=Sum('estimated_cost'))['total'] or Decimal('0.00')
        
        total_cost_ytd = maintenances_ytd + diagnostics_ytd
        
        maintenances_mtd = Maintenance.objects.filter(
            vehicle__user=user,
            completed_at__gte=month_start
        ).aggregate(total=Sum('cost'))['total'] or Decimal('0.00')
        
        diagnostics_mtd = Diagnostic.objects.filter(
            vehicle__user=user,
            created_at__gte=month_start
        ).aggregate(total=Sum('estimated_cost'))['total'] or Decimal('0.00')
        
        total_cost_mtd = maintenances_mtd + diagnostics_mtd
        
        avg_cost_per_vehicle = total_cost_ytd / total_vehicles if total_vehicles > 0 else Decimal('0.00')
        
        data = {
            'total_vehicles': total_vehicles,
            'total_maintenances': total_maintenances,
            'total_diagnostics': total_diagnostics,
            'total_documents': total_documents,
            'pending_maintenances': pending_maintenances,
            'critical_diagnostics': critical_diagnostics,
            'expiring_documents': expiring_documents,
            'total_cost_ytd': total_cost_ytd,
            'total_cost_mtd': total_cost_mtd,
            'avg_cost_per_vehicle': avg_cost_per_vehicle,
        }
        
        serializer = OverviewStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def costs_breakdown(self, request):
        """
        Get cost breakdown by category
        GET /api/statistics/costs-breakdown/?period=30days
        """
        user = request.user
        period = request.query_params.get('period', '30days')
        
        # Calculate date range
        now = timezone.now()
        if period == '7days':
            start_date = now - timedelta(days=7)
        elif period == '30days':
            start_date = now - timedelta(days=30)
        elif period == '90days':
            start_date = now - timedelta(days=90)
        elif period == '1year':
            start_date = now - timedelta(days=365)
        else:
            start_date = None
        
        # Get maintenances by type
        maintenances_query = Maintenance.objects.filter(vehicle__user=user)
        if start_date:
            maintenances_query = maintenances_query.filter(completed_at__gte=start_date)
        
        maintenance_breakdown = maintenances_query.values('maintenance_type').annotate(
            amount=Sum('cost'),
            count=Count('id')
        )
        
        # Get diagnostics costs
        diagnostics_query = Diagnostic.objects.filter(vehicle__user=user)
        if start_date:
            diagnostics_query = diagnostics_query.filter(created_at__gte=start_date)
        
        diagnostic_total = diagnostics_query.aggregate(
            amount=Sum('estimated_cost'),
            count=Count('id')
        )
        
        # Calculate total for percentages
        total_amount = Decimal('0.00')
        breakdown_list = []
        
        for item in maintenance_breakdown:
            amount = item['amount'] or Decimal('0.00')
            total_amount += amount
            breakdown_list.append({
                'category': item['maintenance_type'] or 'Autre',
                'amount': amount,
                'count': item['count'],
            })
        
        if diagnostic_total['amount']:
            total_amount += diagnostic_total['amount']
            breakdown_list.append({
                'category': 'Diagnostics',
                'amount': diagnostic_total['amount'],
                'count': diagnostic_total['count'],
            })
        
        # Calculate percentages
        for item in breakdown_list:
            item['percentage'] = (item['amount'] / total_amount * 100) if total_amount > 0 else Decimal('0.00')
        
        serializer = CostBreakdownSerializer(breakdown_list, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def monthly_trends(self, request):
        """
        Get monthly cost trends
        GET /api/statistics/monthly-trends/?months=12
        """
        user = request.user
        months = int(request.query_params.get('months', 12))
        
        now = timezone.now()
        start_date = now - timedelta(days=months * 30)
        
        # Get all maintenances and diagnostics
        maintenances = Maintenance.objects.filter(
            vehicle__user=user,
            completed_at__gte=start_date
        ).values('completed_at', 'cost')
        
        diagnostics = Diagnostic.objects.filter(
            vehicle__user=user,
            created_at__gte=start_date
        ).values('created_at', 'estimated_cost')
        
        # Group by month
        monthly_data = {}
        
        for m in maintenances:
            if m['completed_at']:
                month_key = m['completed_at'].strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'month': m['completed_at'].strftime('%B'),
                        'year': m['completed_at'].year,
                        'total_cost': Decimal('0.00'),
                        'maintenance_cost': Decimal('0.00'),
                        'diagnostic_cost': Decimal('0.00'),
                        'count': 0,
                    }
                monthly_data[month_key]['maintenance_cost'] += m['cost'] or Decimal('0.00')
                monthly_data[month_key]['total_cost'] += m['cost'] or Decimal('0.00')
                monthly_data[month_key]['count'] += 1
        
        for d in diagnostics:
            month_key = d['created_at'].strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': d['created_at'].strftime('%B'),
                    'year': d['created_at'].year,
                    'total_cost': Decimal('0.00'),
                    'maintenance_cost': Decimal('0.00'),
                    'diagnostic_cost': Decimal('0.00'),
                    'count': 0,
                }
            monthly_data[month_key]['diagnostic_cost'] += d['estimated_cost'] or Decimal('0.00')
            monthly_data[month_key]['total_cost'] += d['estimated_cost'] or Decimal('0.00')
            monthly_data[month_key]['count'] += 1
        
        # Sort by date
        sorted_data = sorted(monthly_data.values(), key=lambda x: (x['year'], x['month']))
        
        serializer = MonthlyTrendSerializer(sorted_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vehicles_stats(self, request):
        """
        Get per-vehicle statistics
        GET /api/statistics/vehicles-stats/
        """
        user = request.user
        vehicles = Vehicle.objects.filter(user=user)
        
        stats_list = []
        
        for vehicle in vehicles:
            maintenances = Maintenance.objects.filter(vehicle=vehicle)
            diagnostics = Diagnostic.objects.filter(vehicle=vehicle)
            
            total_cost = (maintenances.aggregate(Sum('cost'))['cost__sum'] or Decimal('0.00')) + \
                        (diagnostics.aggregate(Sum('estimated_cost'))['estimated_cost__sum'] or Decimal('0.00'))
            
            maintenance_count = maintenances.count()
            diagnostic_count = diagnostics.count()
            
            avg_cost_per_maintenance = (maintenances.aggregate(Avg('cost'))['cost__avg'] or Decimal('0.00'))
            
            last_maintenance = maintenances.filter(status='completed').order_by('-completed_at').first()
            next_maintenance = maintenances.filter(status='scheduled').order_by('scheduled_at').first()
            
            stats_list.append({
                'vehicle_id': vehicle.id,
                'vehicle_name': f"{vehicle.brand} {vehicle.model}",
                'brand': vehicle.brand,
                'model': vehicle.model,
                'year': vehicle.year,
                'total_cost': total_cost,
                'maintenance_count': maintenance_count,
                'diagnostic_count': diagnostic_count,
                'avg_cost_per_maintenance': avg_cost_per_maintenance,
                'last_maintenance_date': last_maintenance.completed_at if last_maintenance else None,
                'next_maintenance_date': next_maintenance.scheduled_at if next_maintenance else None,
            })
        
        serializer = VehicleStatsSerializer(stats_list, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def maintenance_stats(self, request):
        """
        Get maintenance statistics
        GET /api/statistics/maintenance-stats/
        """
        user = request.user
        now = timezone.now()
        
        maintenances = Maintenance.objects.filter(vehicle__user=user)
        
        total_count = maintenances.count()
        completed_count = maintenances.filter(status='completed').count()
        pending_count = maintenances.filter(status__in=['scheduled', 'pending']).count()
        overdue_count = maintenances.filter(
            status='scheduled',
            scheduled_at__lt=now
        ).count()
        
        total_cost = maintenances.aggregate(Sum('cost'))['cost__sum'] or Decimal('0.00')
        avg_cost = maintenances.aggregate(Avg('cost'))['cost__avg'] or Decimal('0.00')
        
        most_common = maintenances.values('maintenance_type').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        upcoming_7days = maintenances.filter(
            status='scheduled',
            scheduled_at__gte=now,
            scheduled_at__lte=now + timedelta(days=7)
        ).count()
        
        upcoming_30days = maintenances.filter(
            status='scheduled',
            scheduled_at__gte=now,
            scheduled_at__lte=now + timedelta(days=30)
        ).count()
        
        data = {
            'total_count': total_count,
            'completed_count': completed_count,
            'pending_count': pending_count,
            'overdue_count': overdue_count,
            'total_cost': total_cost,
            'avg_cost': avg_cost,
            'most_common_type': most_common['maintenance_type'] if most_common else 'N/A',
            'upcoming_7days': upcoming_7days,
            'upcoming_30days': upcoming_30days,
        }
        
        serializer = MaintenanceStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def diagnostic_stats(self, request):
        """
        Get diagnostic statistics
        GET /api/statistics/diagnostic-stats/
        """
        user = request.user
        
        diagnostics = Diagnostic.objects.filter(vehicle__user=user)
        
        total_count = diagnostics.count()
        critical_count = diagnostics.filter(severity='critical').count()
        high_count = diagnostics.filter(severity='high').count()
        medium_count = diagnostics.filter(severity='medium').count()
        low_count = diagnostics.filter(severity='low').count()
        
        resolved_count = diagnostics.filter(status='resolved').count()
        unresolved_count = diagnostics.filter(status='unresolved').count()
        
        # Calculate avg resolution time
        resolved = diagnostics.filter(status='resolved', resolved_at__isnull=False)
        resolution_times = []
        for d in resolved:
            delta = d.resolved_at - d.created_at
            resolution_times.append(delta.days)
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else None
        
        # Most common issue
        most_common = diagnostics.values('diagnostic_code').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        data = {
            'total_count': total_count,
            'critical_count': critical_count,
            'high_count': high_count,
            'medium_count': medium_count,
            'low_count': low_count,
            'resolved_count': resolved_count,
            'unresolved_count': unresolved_count,
            'avg_resolution_time_days': Decimal(str(avg_resolution_time)) if avg_resolution_time else None,
            'most_common_issue': most_common['diagnostic_code'] if most_common else None,
        }
        
        serializer = DiagnosticStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def cost_comparison(self, request):
        """
        Compare costs between periods
        GET /api/statistics/cost-comparison/?period=monthly
        """
        user = request.user
        period = request.query_params.get('period', 'monthly')
        
        now = timezone.now()
        
        if period == 'weekly':
            current_start = now - timedelta(days=7)
            previous_start = now - timedelta(days=14)
            previous_end = current_start
        elif period == 'monthly':
            current_start = now.replace(day=1, hour=0, minute=0, second=0)
            previous_month = (current_start - timedelta(days=1)).replace(day=1)
            previous_start = previous_month
            previous_end = current_start
        else:  # yearly
            current_start = now.replace(month=1, day=1, hour=0, minute=0, second=0)
            previous_start = current_start.replace(year=current_start.year - 1)
            previous_end = current_start
        
        # Current period
        current_maintenances = Maintenance.objects.filter(
            vehicle__user=user,
            completed_at__gte=current_start
        ).aggregate(Sum('cost'))['cost__sum'] or Decimal('0.00')
        
        current_diagnostics = Diagnostic.objects.filter(
            vehicle__user=user,
            created_at__gte=current_start
        ).aggregate(Sum('estimated_cost'))['estimated_cost__sum'] or Decimal('0.00')
        
        current_period_cost = current_maintenances + current_diagnostics
        
        # Previous period
        previous_maintenances = Maintenance.objects.filter(
            vehicle__user=user,
            completed_at__gte=previous_start,
            completed_at__lt=previous_end
        ).aggregate(Sum('cost'))['cost__sum'] or Decimal('0.00')
        
        previous_diagnostics = Diagnostic.objects.filter(
            vehicle__user=user,
            created_at__gte=previous_start,
            created_at__lt=previous_end
        ).aggregate(Sum('estimated_cost'))['estimated_cost__sum'] or Decimal('0.00')
        
        previous_period_cost = previous_maintenances + previous_diagnostics
        
        difference = current_period_cost - previous_period_cost
        percentage_change = (difference / previous_period_cost * 100) if previous_period_cost > 0 else Decimal('0.00')
        
        if abs(percentage_change) < 5:
            trend = 'stable'
        elif percentage_change > 0:
            trend = 'up'
        else:
            trend = 'down'
        
        data = {
            'current_period_cost': current_period_cost,
            'previous_period_cost': previous_period_cost,
            'difference': difference,
            'percentage_change': percentage_change,
            'trend': trend,
        }
        
        serializer = CostComparisonSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """
        Export statistics report
        POST /api/statistics/export/
        Body: {
            "format": "pdf" | "excel" | "csv",
            "period": "7days" | "30days" | "90days" | "1year" | "all",
            "vehicle_id": 123,  // optional
            "include_charts": true,
            "include_details": true
        }
        """
        serializer = ExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        export_format = serializer.validated_data['format']
        period = serializer.validated_data['period']
        vehicle_id = serializer.validated_data.get('vehicle_id')
        
        # TODO: Implement actual export logic with reportlab (PDF) or openpyxl (Excel)
        # For now, return a placeholder response
        
        return Response({
            'message': f'Export {export_format} will be generated',
            'download_url': '/api/statistics/download/xyz123/',
            'status': 'processing'
        })
