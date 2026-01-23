"""
Statistics Admin
"""
from django.contrib import admin
from .models import StatisticsCache


@admin.register(StatisticsCache)
class StatisticsCacheAdmin(admin.ModelAdmin):
    list_display = ['user', 'cache_type', 'cache_key', 'created_at', 'expires_at']
    list_filter = ['cache_type', 'created_at']
    search_fields = ['user__email', 'cache_key']
    readonly_fields = ['created_at']
