"""
Admin interface for document management.
"""
from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'file_size', 'page_count', 'status', 'created_at']
    list_filter = ['status', 'file_type', 'created_at']
    search_fields = ['title']
    readonly_fields = ['file_size', 'file_type', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'file_path', 'file_type', 'file_size')
        }),
        ('Processing Status', {
            'fields': ('status', 'error_message', 'page_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'token_count', 'created_at']
    list_filter = ['document', 'created_at']
    search_fields = ['document__title', 'text']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Chunk Information', {
            'fields': ('document', 'chunk_index', 'text', 'token_count')
        }),
        ('Metadata', {
            'fields': ('page_numbers', 'embedding_id', 'created_at')
        }),
    )
