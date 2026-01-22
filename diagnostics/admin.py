from django.contrib import admin
from .models import Diagnostic, DiagnosticReply


class DiagnosticReplyInline(admin.TabularInline):
    """Inline for diagnostic replies"""
    model = DiagnosticReply
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Diagnostic)
class DiagnosticAdmin(admin.ModelAdmin):
    """Diagnostic admin"""
    list_display = ['title', 'vehicle', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'vehicle__make', 'vehicle__model']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DiagnosticReplyInline]
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('user', 'vehicle')
        }),
        ('Diagnostic Details', {
            'fields': ('title', 'description', 'status')
        }),
        ('AI Analysis', {
            'fields': ('ai_analysis', 'confidence_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(DiagnosticReply)
class DiagnosticReplyAdmin(admin.ModelAdmin):
    """Diagnostic reply admin"""
    list_display = ['diagnostic', 'sender_type', 'created_at']
    list_filter = ['sender_type', 'created_at']
    search_fields = ['message', 'diagnostic__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
