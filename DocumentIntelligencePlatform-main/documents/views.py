"""
API views for document management and querying.
"""
import os
import time
import logging
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Document, DocumentChunk
from .serializers import (
    DocumentSerializer, DocumentUploadSerializer, 
    QueryRequestSerializer, QueryResponseSerializer
)
from .processing import DocumentProcessor
from .vector_store import vector_store
from .llm_service import llm_service

logger = logging.getLogger(__name__)


class DocumentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET'])
def list_documents(request):
    """
    GET /api/documents/
    List all uploaded documents with metadata.
    """
    try:
        documents = Document.objects.all().order_by('-created_at')
        
        # Apply pagination
        paginator = DocumentPagination()
        page = paginator.paginate_queryset(documents, request)
        
        if page is not None:
            serializer = DocumentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = DocumentSerializer(documents, many=True)
        return Response({
            'success': True,
            'documents': serializer.data,
            'count': len(serializer.data)
        })
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve documents',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_document(request, document_id):
    """
    GET /api/documents/{id}/
    Get specific document with chunks.
    """
    try:
        document = Document.objects.get(id=document_id)
        serializer = DocumentSerializer(document)
        
        return Response({
            'success': True,
            'document': serializer.data
        })
        
    except Document.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve document',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    POST /api/documents/upload/
    Upload and process documents.
    """
    try:
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid document data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create document instance
        with transaction.atomic():
            document = serializer.save()
            document.file_size = document.file_path.size
            document.status = 'processing'
            document.save()
        
        # Process document asynchronously (or synchronously for simplicity)
        try:
            _process_document(document)
            return Response({
                'success': True,
                'message': 'Document uploaded and processed successfully',
                'document': DocumentSerializer(document).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Update document status on processing error
            document.status = 'error'
            document.error_message = str(e)
            document.save()
            
            logger.error(f"Error processing document {document.id}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Document uploaded but processing failed',
                'details': str(e),
                'document_id': document.id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to upload document',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def query_document(request):
    """
    POST /api/documents/query/
    Query document using RAG pipeline.
    """
    start_time = time.time()
    
    try:
        serializer = QueryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid query data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        document_id = serializer.validated_data['document_id']
        question = serializer.validated_data['question']
        num_chunks = serializer.validated_data['num_chunks']
        
        # Get document
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Document not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check document status
        if document.status != 'processed':
            return Response({
                'success': False,
                'error': f'Document is not ready for querying. Status: {document.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Search similar chunks
        similar_chunks = vector_store.search_similar_chunks(
            query=question,
            document_id=document_id,
            num_results=num_chunks
        )
        
        if not similar_chunks:
            return Response({
                'success': False,
                'error': 'No relevant content found for your question'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate answer using LLM
        llm_response = llm_service.generate_answer(
            question=question,
            context_chunks=similar_chunks,
            document_title=document.title
        )
        
        processing_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            'success': True,
            'answer': llm_response.get('answer', 'No answer generated'),
            'confidence': llm_response.get('confidence', 0.0),
            'reasoning': llm_response.get('reasoning', ''),
            'sources': llm_response.get('sources', []),
            'processing_time': round(processing_time, 2),
            'document_title': document.title,
            'chunks_used': len(similar_chunks)
        }
        
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to process query',
            'details': str(e),
            'processing_time': round(time.time() - start_time, 2)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_document(request, document_id):
    """
    DELETE /api/documents/{id}/
    Delete document and associated chunks.
    """
    try:
        document = Document.objects.get(id=document_id)
        
        # Delete from vector store
        vector_store.delete_document_chunks(document_id)
        
        # Delete file from filesystem
        if document.file_path and os.path.exists(document.file_path.path):
            os.remove(document.file_path.path)
        
        # Delete document (cascades to chunks)
        document.delete()
        
        return Response({
            'success': True,
            'message': 'Document deleted successfully'
        })
    
    except Document.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete document',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def vector_store_stats(request):
    """
    GET /api/vector-store/stats/
    Get vector store statistics.
    """
    try:
        stats = vector_store.get_collection_stats()
        
        # Add database stats
        total_documents = Document.objects.count()
        processed_documents = Document.objects.filter(status='processed').count()
        total_chunks = DocumentChunk.objects.count()
        
        stats.update({
            'database_documents': total_documents,
            'processed_documents': processed_documents,
            'database_chunks': total_chunks
        })
        
        return Response({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting vector store stats: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get statistics',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _process_document(document):
    """
    Internal function to process document.
    This could be moved to a background task with Celery.
    """
    processor = DocumentProcessor()
    
    try:
        # Extract text
        text, page_count = processor.extract_text(
            document.file_path.path,
            document.file_type
        )
        
        # Update page count
        document.page_count = page_count
        document.save()
        
        # Chunk text
        chunks_data = processor.chunk_text(text, document.id)
        
        if not chunks_data:
            raise ValueError("No chunks generated from document")
        
        # Add to vector store
        embedding_ids = vector_store.add_chunks(chunks_data)
        
        # Save chunks to database
        chunk_objects = []
        for chunk_data, embedding_id in zip(chunks_data, embedding_ids):
            chunk = DocumentChunk(
                document=document,
                chunk_index=chunk_data['chunk_index'],
                text=chunk_data['text'],
                page_numbers=chunk_data['page_numbers'],
                embedding_id=embedding_id,
                token_count=chunk_data['token_count']
            )
            chunk_objects.append(chunk)
        
        DocumentChunk.objects.bulk_create(chunk_objects)
        
        # Mark as processed
        document.status = 'processed'
        document.error_message = None
        document.save()
        
        logger.info(f"Successfully processed document {document.id} with {len(chunks_data)} chunks")
        
    except Exception as e:
        logger.error(f"Error in _process_document: {str(e)}")
        raise
