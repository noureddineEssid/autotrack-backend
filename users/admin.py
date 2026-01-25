from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Session


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User admin"""
    
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'email_verified', 'created_at']
    list_filter = ['is_staff', 'is_active', 'email_verified', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name', 'phone_number')}),
        ('Stripe', {'fields': ('stripe_customer_id',)}),
        ('Verification', {'fields': ('email_verified', 'code_otp', 'expire_otp')}),
        ('Password Reset', {'fields': ('password_reset_token', 'password_reset_token_expiration')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'roles', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Session admin"""
    
    list_display = ['user', 'ip_address', 'is_active', 'expires_at', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

