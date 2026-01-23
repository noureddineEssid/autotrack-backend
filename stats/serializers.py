"""
Statistics Serializers
"""
from rest_framework import serializers


class OverviewStatsSerializer(serializers.Serializer):
    """Overall statistics overview"""
    total_vehicles = serializers.IntegerField()
    total_maintenances = serializers.IntegerField()
    total_diagnostics = serializers.IntegerField()
    total_documents = serializers.IntegerField()
    pending_maintenances = serializers.IntegerField()
    critical_diagnostics = serializers.IntegerField()
    expiring_documents = serializers.IntegerField()
    total_cost_ytd = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cost_mtd = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_cost_per_vehicle = serializers.DecimalField(max_digits=10, decimal_places=2)


class CostBreakdownSerializer(serializers.Serializer):
    """Cost breakdown by category"""
    category = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    count = serializers.IntegerField()


class MonthlyTrendSerializer(serializers.Serializer):
    """Monthly trend data"""
    month = serializers.CharField()
    year = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    maintenance_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    diagnostic_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    count = serializers.IntegerField()


class VehicleStatsSerializer(serializers.Serializer):
    """Per-vehicle statistics"""
    vehicle_id = serializers.IntegerField()
    vehicle_name = serializers.CharField()
    brand = serializers.CharField()
    model = serializers.CharField()
    year = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    maintenance_count = serializers.IntegerField()
    diagnostic_count = serializers.IntegerField()
    avg_cost_per_maintenance = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_maintenance_date = serializers.DateTimeField(allow_null=True)
    next_maintenance_date = serializers.DateTimeField(allow_null=True)


class MaintenanceStatsSerializer(serializers.Serializer):
    """Maintenance statistics"""
    total_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    most_common_type = serializers.CharField()
    upcoming_7days = serializers.IntegerField()
    upcoming_30days = serializers.IntegerField()


class DiagnosticStatsSerializer(serializers.Serializer):
    """Diagnostic statistics"""
    total_count = serializers.IntegerField()
    critical_count = serializers.IntegerField()
    high_count = serializers.IntegerField()
    medium_count = serializers.IntegerField()
    low_count = serializers.IntegerField()
    resolved_count = serializers.IntegerField()
    unresolved_count = serializers.IntegerField()
    avg_resolution_time_days = serializers.DecimalField(max_digits=5, decimal_places=1, allow_null=True)
    most_common_issue = serializers.CharField(allow_null=True)


class CostComparisonSerializer(serializers.Serializer):
    """Cost comparison between periods"""
    current_period_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    previous_period_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    difference = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentage_change = serializers.DecimalField(max_digits=5, decimal_places=2)
    trend = serializers.CharField()  # 'up', 'down', 'stable'


class ExportRequestSerializer(serializers.Serializer):
    """Export request parameters"""
    format = serializers.ChoiceField(choices=['pdf', 'excel', 'csv'])
    period = serializers.ChoiceField(choices=['7days', '30days', '90days', '1year', 'all'])
    vehicle_id = serializers.IntegerField(required=False, allow_null=True)
    include_charts = serializers.BooleanField(default=True)
    include_details = serializers.BooleanField(default=True)
