"""
URL configuration for documents app.
"""
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Document management
    path('documents/', views.list_documents, name='list_documents'),
    path('documents/<int:document_id>/', views.get_document, name='get_document'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    
    # Querying
    path('documents/query/', views.query_document, name='query_document'),
    
    # Statistics
    path('vector-store/stats/', views.vector_store_stats, name='vector_store_stats'),
]
