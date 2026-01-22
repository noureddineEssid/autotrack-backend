from django.contrib import admin
from .models import Vehicle, CarBrand, CarModel


@admin.register(CarBrand)
class CarBrandAdmin(admin.ModelAdmin):
    """Car brand admin"""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    """Car model admin"""
    list_display = ['name', 'brand', 'year_start', 'year_end']
    list_filter = ['brand']
    search_fields = ['name', 'brand__name']
    ordering = ['brand', 'name']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Vehicle admin"""
    list_display = ['make', 'model', 'year', 'owner', 'license_plate', 'vin', 'created_at']
    list_filter = ['fuel_type', 'transmission', 'year']
    search_fields = ['make', 'model', 'license_plate', 'vin', 'owner__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

