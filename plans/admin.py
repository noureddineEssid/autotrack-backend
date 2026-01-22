from django.contrib import admin
from .models import Plan, PlanFeature, PlanFeatureValue


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    """Plan feature admin"""
    list_display = ['name', 'feature_key', 'created_at']
    search_fields = ['name', 'feature_key', 'description']
    ordering = ['name']


class PlanFeatureValueInline(admin.TabularInline):
    """Inline for plan feature values"""
    model = PlanFeatureValue
    extra = 1


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Plan admin"""
    list_display = ['name', 'price', 'currency', 'interval', 'is_active']
    list_filter = ['interval', 'is_active', 'is_popular']
    search_fields = ['name', 'description', 'stripe_price_id']
    ordering = ['price']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PlanFeatureValueInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active', 'is_popular')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'interval', 'stripe_price_id', 'stripe_product_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
