from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Document admin"""
    list_display = ['title', 'vehicle', 'document_type', 'file_size', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['title', 'description', 'vehicle__make', 'vehicle__model']
    ordering = ['-created_at']
    readonly_fields = ['file_size', 'mime_type', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Vehicle & Type', {
            'fields': ('user', 'vehicle', 'document_type')
        }),
        ('Document Information', {
            'fields': ('title', 'description', 'file')
        }),
        ('File Details', {
            'fields': ('file_size', 'mime_type', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
