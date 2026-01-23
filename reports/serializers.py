from rest_framework import serializers
from .models import Report, ReportTemplate
from vehicles.models import Vehicle


class ReportCreateSerializer(serializers.Serializer):
    """Serializer for creating a new report"""
    
    report_type = serializers.ChoiceField(choices=Report.REPORT_TYPES)
    format = serializers.ChoiceField(choices=Report.FORMATS)
    vehicle_id = serializers.UUIDField(required=False, allow_null=True)
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
    include_charts = serializers.BooleanField(default=True)
    include_images = serializers.BooleanField(default=True)
    include_summary = serializers.BooleanField(default=True)
    include_details = serializers.BooleanField(default=True)
    
    def validate_vehicle_id(self, value):
        """Validate that vehicle exists and belongs to user"""
        if value:
            user = self.context['request'].user
            if not Vehicle.objects.filter(id=value, user=user).exists():
                raise serializers.ValidationError("Vehicle not found or doesn't belong to you")
        return value
    
    def validate(self, data):
        """Validate date range"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({
                'date_from': 'Start date must be before end date'
            })
        
        return data


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model"""
    
    download_url = serializers.SerializerMethodField()
    vehicle_name = serializers.SerializerMethodField()
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'report_type_display', 'format', 'format_display',
            'vehicle', 'vehicle_name', 'date_from', 'date_to',
            'include_charts', 'include_images', 'include_summary', 'include_details',
            'status', 'status_display', 'file_size', 'error_message',
            'created_at', 'completed_at', 'expires_at', 'download_url'
        ]
        read_only_fields = [
            'id', 'status', 'file_size', 'error_message',
            'created_at', 'completed_at', 'expires_at', 'download_url'
        ]
    
    def get_download_url(self, obj):
        """Get download URL if report is completed"""
        if obj.status == 'completed' and obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/api/reports/{obj.id}/download/')
        return None
    
    def get_vehicle_name(self, obj):
        """Get vehicle name if specified"""
        if obj.vehicle:
            return f"{obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.license_plate})"
        return None


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ReportTemplate model"""
    
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    format_display = serializers.CharField(source='get_default_format_display', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type', 'report_type_display',
            'default_format', 'format_display', 'include_charts', 'include_images',
            'include_summary', 'include_details', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_is_default(self, value):
        """Ensure only one default template per report type"""
        if value:
            user = self.context['request'].user
            report_type = self.initial_data.get('report_type')
            
            # Check if another default exists for this report type
            existing_default = ReportTemplate.objects.filter(
                user=user,
                report_type=report_type,
                is_default=True
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing_default.exists():
                raise serializers.ValidationError(
                    f"A default template already exists for {report_type}"
                )
        
        return value


class ReportStatsSerializer(serializers.Serializer):
    """Serializer for report statistics"""
    
    total_reports = serializers.IntegerField()
    by_type = serializers.DictField()
    by_format = serializers.DictField()
    by_status = serializers.DictField()
    total_size_mb = serializers.FloatField()
    completed_today = serializers.IntegerField()
    pending = serializers.IntegerField()
