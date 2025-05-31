"""
Models for document management and chunking.
"""
from django.db import models
from django.core.validators import FileExtensionValidator
import os


def document_upload_path(instance, filename):
    """Generate upload path for documents."""
    return f'documents/{instance.id}/{filename}'


class Document(models.Model):
    """Model for storing document metadata."""
    
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('error', 'Error'),
    ]
    
    title = models.CharField(max_length=255, help_text="Document title")
    file_path = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['txt', 'pdf', 'docx', 'md'])],
        help_text="Uploaded document file"
    )
    file_type = models.CharField(max_length=10, help_text="File extension")
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    page_count = models.PositiveIntegerField(default=0, help_text="Number of pages")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploading',
        help_text="Processing status"
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error details if processing failed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.file_path:
            # Set file type from extension
            self.file_type = os.path.splitext(self.file_path.name)[1].lower().lstrip('.')
            # Set title from filename if not provided
            if not self.title:
                self.title = os.path.splitext(os.path.basename(self.file_path.name))[0]
        super().save(*args, **kwargs)


class DocumentChunk(models.Model):
    """Model for storing document chunks with embeddings."""
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks',
        help_text="Parent document"
    )
    chunk_index = models.PositiveIntegerField(help_text="Sequential chunk number")
    text = models.TextField(help_text="Chunk text content")
    page_numbers = models.JSONField(
        default=list,
        help_text="List of page numbers this chunk spans"
    )
    embedding_id = models.CharField(
        max_length=255,
        help_text="Reference ID in vector store"
    )
    token_count = models.PositiveIntegerField(default=0, help_text="Number of tokens in chunk")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['document', 'chunk_index']
        unique_together = ['document', 'chunk_index']
        verbose_name = 'Document Chunk'
        verbose_name_plural = 'Document Chunks'
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
