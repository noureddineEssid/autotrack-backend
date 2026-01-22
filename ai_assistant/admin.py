from django.contrib import admin
from .models import AIConversation, AIMessage


class AIMessageInline(admin.TabularInline):
    """Inline for AI messages"""
    model = AIMessage
    extra = 0
    readonly_fields = ['created_at']


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    """AI conversation admin"""
    list_display = ['title', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'user__email', 'user__first_name', 'user__last_name']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AIMessageInline]
    
    fieldsets = (
        ('Conversation', {
            'fields': ('user', 'title', 'context')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    """AI message admin"""
    list_display = ['conversation', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'conversation__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Message', {
            'fields': ('conversation', 'role', 'content')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
