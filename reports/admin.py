from django.contrib import admin
from .models import Report, ReportTemplate


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'report_type', 'format', 'status', 'created_at', 'file_size_mb']
    list_filter = ['report_type', 'format', 'status', 'created_at']
    search_fields = ['user__username', 'user__email', 'vehicle__license_plate']
    readonly_fields = ['id', 'created_at', 'completed_at', 'download_url']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'report_type', 'format', 'status')
        }),
        ('Filters', {
            'fields': ('vehicle', 'date_from', 'date_to')
        }),
        ('Configuration', {
            'fields': ('include_charts', 'include_images', 'include_summary', 'include_details')
        }),
        ('File Info', {
            'fields': ('file_path', 'file_size', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at', 'expires_at')
        }),
    )
    
    def file_size_mb(self, obj):
        """Display file size in MB"""
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "N/A"
    file_size_mb.short_description = "File Size"


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'report_type', 'default_format', 'is_default', 'created_at']
    list_filter = ['report_type', 'default_format', 'is_default']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'name', 'description')
        }),
        ('Template Configuration', {
            'fields': ('report_type', 'default_format', 'is_default')
        }),
        ('Default Settings', {
            'fields': ('include_charts', 'include_images', 'include_summary', 'include_details')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
