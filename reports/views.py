from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta
import os
from .models import Report, ReportTemplate
from .serializers import (
    ReportSerializer,
    ReportCreateSerializer,
    ReportTemplateSerializer,
    ReportStatsSerializer
)
from .generators import (
    VehicleSummaryPDFGenerator,
    VehicleSummaryExcelGenerator,
    CSVGenerator,
    BasePDFGenerator,
    BaseExcelGenerator
)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reports
    
    Endpoints:
    - GET /api/reports/ - List all reports
    - POST /api/reports/ - Create new report
    - GET /api/reports/{id}/ - Get report details
    - DELETE /api/reports/{id}/ - Delete report
    - GET /api/reports/{id}/download/ - Download report file
    - GET /api/reports/stats/ - Get report statistics
    """
    
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter reports by current user"""
        queryset = Report.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by report type
        report_type = self.request.query_params.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Filter by vehicle
        vehicle_id = self.request.query_params.get('vehicle_id')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new report"""
        serializer = ReportCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Create report instance
        report = Report.objects.create(
            user=request.user,
            report_type=serializer.validated_data['report_type'],
            format=serializer.validated_data['format'],
            vehicle_id=serializer.validated_data.get('vehicle_id'),
            date_from=serializer.validated_data.get('date_from'),
            date_to=serializer.validated_data.get('date_to'),
            include_charts=serializer.validated_data.get('include_charts', True),
            include_images=serializer.validated_data.get('include_images', True),
            include_summary=serializer.validated_data.get('include_summary', True),
            include_details=serializer.validated_data.get('include_details', True),
        )
        
        # Generate report asynchronously (in a real app, use Celery)
        try:
            report.status = 'processing'
            report.save()
            
            # Generate report file
            file_path = self._generate_report_file(report)
            
            # Update report with file info
            report.status = 'completed'
            report.file_path = file_path
            report.file_size = os.path.getsize(file_path)
            report.completed_at = timezone.now()
            report.expires_at = timezone.now() + timedelta(days=7)
            report.save()
            
        except Exception as e:
            report.status = 'failed'
            report.error_message = str(e)
            report.save()
        
        # Return report details
        response_serializer = ReportSerializer(report, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def _generate_report_file(self, report):
        """Generate report file based on format and type"""
        # Create reports directory if it doesn't exist
        from django.conf import settings
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports', str(report.user.id))
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        extension = {
            'pdf': 'pdf',
            'excel': 'xlsx',
            'csv': 'csv'
        }[report.format]
        
        filename = f"{report.report_type}_{timestamp}.{extension}"
        file_path = os.path.join(reports_dir, filename)
        
        # Generate report based on format
        if report.format == 'pdf':
            generator = VehicleSummaryPDFGenerator(report)
            generator.generate(file_path)
        elif report.format == 'excel':
            generator = VehicleSummaryExcelGenerator(report)
            generator.generate(file_path)
        elif report.format == 'csv':
            generator = CSVGenerator(report)
            generator.generate(file_path)
        
        return file_path
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report file"""
        report = self.get_object()
        
        # Check if report is completed
        if report.status != 'completed':
            return Response(
                {'error': 'Report is not ready for download'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if file exists
        if not report.file_path or not os.path.exists(report.file_path):
            return Response(
                {'error': 'Report file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if expired
        if report.is_expired:
            return Response(
                {'error': 'Report has expired'},
                status=status.HTTP_410_GONE
            )
        
        # Return file
        file_handle = open(report.file_path, 'rb')
        content_types = {
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv'
        }
        
        response = FileResponse(
            file_handle,
            content_type=content_types.get(report.format, 'application/octet-stream')
        )
        
        filename = os.path.basename(report.file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get report statistics"""
        reports = self.get_queryset()
        
        # Calculate statistics
        total_reports = reports.count()
        
        by_type = dict(
            reports.values('report_type')
            .annotate(count=Count('id'))
            .values_list('report_type', 'count')
        )
        
        by_format = dict(
            reports.values('format')
            .annotate(count=Count('id'))
            .values_list('format', 'count')
        )
        
        by_status = dict(
            reports.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        # Total size in MB
        total_size = reports.aggregate(total=Sum('file_size'))['total'] or 0
        total_size_mb = total_size / (1024 * 1024)
        
        # Reports completed today
        today = timezone.now().date()
        completed_today = reports.filter(
            completed_at__date=today,
            status='completed'
        ).count()
        
        # Pending reports
        pending = reports.filter(status__in=['pending', 'processing']).count()
        
        stats_data = {
            'total_reports': total_reports,
            'by_type': by_type,
            'by_format': by_format,
            'by_status': by_status,
            'total_size_mb': round(total_size_mb, 2),
            'completed_today': completed_today,
            'pending': pending,
        }
        
        serializer = ReportStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def cleanup(self, request):
        """Delete expired reports"""
        now = timezone.now()
        expired_reports = self.get_queryset().filter(
            expires_at__lt=now
        )
        
        # Delete files
        for report in expired_reports:
            if report.file_path and os.path.exists(report.file_path):
                try:
                    os.remove(report.file_path)
                except:
                    pass
        
        # Delete database records
        count = expired_reports.delete()[0]
        
        return Response({
            'message': f'{count} expired reports deleted successfully'
        })


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing report templates
    
    Endpoints:
    - GET /api/report-templates/ - List all templates
    - POST /api/report-templates/ - Create new template
    - GET /api/report-templates/{id}/ - Get template details
    - PUT /api/report-templates/{id}/ - Update template
    - DELETE /api/report-templates/{id}/ - Delete template
    """
    
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter templates by current user"""
        return ReportTemplate.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Save template with current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def defaults(self, request):
        """Get default templates for each report type"""
        defaults = self.get_queryset().filter(is_default=True)
        serializer = self.get_serializer(defaults, many=True)
        return Response(serializer.data)
