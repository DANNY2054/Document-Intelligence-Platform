"""
Serializers for document API endpoints.
"""
from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for document chunks."""
    
    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'chunk_index', 'text', 'page_numbers', 
            'token_count', 'created_at'
        ]


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for documents."""
    
    chunks = DocumentChunkSerializer(many=True, read_only=True)
    chunk_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file_path', 'file_type', 'file_size',
            'page_count', 'status', 'error_message', 'created_at',
            'updated_at', 'chunks', 'chunk_count'
        ]
        read_only_fields = [
            'file_type', 'file_size', 'page_count', 'status',
            'error_message', 'created_at', 'updated_at'
        ]
    
    def get_chunk_count(self, obj):
        """Get the number of chunks for this document."""
        return obj.chunks.count()


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document upload."""
    
    class Meta:
        model = Document
        fields = ['title', 'file_path']
    
    def validate_file_path(self, value):
        """Validate uploaded file."""
        if not value:
            raise serializers.ValidationError("No file provided.")
        
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        
        # Check file extension
        allowed_extensions = ['txt', 'pdf', 'docx', 'md']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '{file_extension}' not supported. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value


class QueryRequestSerializer(serializers.Serializer):
    """Serializer for query requests."""
    
    document_id = serializers.IntegerField()
    question = serializers.CharField(max_length=1000)
    num_chunks = serializers.IntegerField(default=3, min_value=1, max_value=10)
    
    def validate_document_id(self, value):
        """Validate document exists and is processed."""
        try:
            document = Document.objects.get(id=value)
            if document.status != 'processed':
                raise serializers.ValidationError(
                    f"Document is not ready for querying. Status: {document.status}"
                )
        except Document.DoesNotExist:
            raise serializers.ValidationError("Document not found.")
        return value


class QueryResponseSerializer(serializers.Serializer):
    """Serializer for query responses."""
    
    answer = serializers.CharField()
    confidence = serializers.FloatField()
    sources = serializers.ListField(
        child=serializers.DictField()
    )
    processing_time = serializers.FloatField()
