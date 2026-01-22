from django.contrib import admin
from .models import Maintenance


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    """Maintenance admin"""
    list_display = ['service_type', 'vehicle', 'service_date', 'status', 'cost', 'created_by']
    list_filter = ['status', 'service_type', 'service_date']
    search_fields = ['service_type', 'description', 'vehicle__make', 'vehicle__model']
    ordering = ['-service_date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'service_date'
