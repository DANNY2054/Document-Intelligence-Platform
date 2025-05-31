"""
Simple vector store using OpenAI embeddings for document chunks.
"""
import os
import json
import logging
from typing import List, Dict, Any
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class VectorStore:
    """Simple vector store using OpenAI embeddings."""
    
    def __init__(self):
        # Initialize OpenAI client for embeddings
        api_key = getattr(settings, 'OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found")
        
        self.client = OpenAI(api_key=api_key)
        self.embedding_model = "text-embedding-ada-002"
        
        # Simple file-based storage for embeddings
        self.storage_path = os.path.join(settings.BASE_DIR, 'embeddings_data.json')
        self.embeddings_data = self._load_embeddings()
    
    def _load_embeddings(self):
        """Load embeddings from file storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return {}
    
    def _save_embeddings(self):
        """Save embeddings to file storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.embeddings_data, f)
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
    
    def add_chunks(self, chunks: List[Dict]) -> List[str]:
        """
        Add document chunks to vector store.
        Returns list of embedding IDs.
        """
        if not chunks:
            return []
        
        try:
            # Extract texts for embedding
            texts = [chunk['text'] for chunk in chunks]
            
            # Generate embeddings using OpenAI
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            
            # Create unique IDs for each chunk
            ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"doc_{chunk['document_id']}_chunk_{chunk['chunk_index']}"
                ids.append(chunk_id)
                
                # Store embedding and metadata
                self.embeddings_data[chunk_id] = {
                    'embedding': response.data[i].embedding,
                    'text': chunk['text'],
                    'document_id': chunk['document_id'],
                    'chunk_index': chunk['chunk_index'],
                    'page_numbers': chunk.get('page_numbers', []),
                    'token_count': chunk.get('token_count', 0)
                }
            
            # Save to file
            self._save_embeddings()
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {str(e)}")
            raise
    
    def search_similar_chunks(self, query: str, document_id: int, num_results: int = 3) -> List[Dict]:
        """
        Search for similar chunks in the vector store.
        Returns list of similar chunks with metadata.
        """
        try:
            # Generate query embedding using OpenAI
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=[query]
            )
            query_embedding = response.data[0].embedding
            
            # Calculate similarities with stored embeddings
            similarities = []
            for chunk_id, chunk_data in self.embeddings_data.items():
                if chunk_data['document_id'] == document_id:
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_embedding, chunk_data['embedding'])
                    similarities.append({
                        'id': chunk_id,
                        'similarity': similarity,
                        'data': chunk_data
                    })
            
            # Sort by similarity and get top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = similarities[:num_results]
            
            # Format results
            similar_chunks = []
            for result in top_results:
                chunk = {
                    'id': result['id'],
                    'text': result['data']['text'],
                    'similarity': result['similarity'],
                    'chunk_index': result['data']['chunk_index'],
                    'page_numbers': result['data']['page_numbers'],
                    'token_count': result['data']['token_count']
                }
                similar_chunks.append(chunk)
            
            logger.info(f"Found {len(similar_chunks)} similar chunks for query")
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def delete_document_chunks(self, document_id: int) -> bool:
        """Delete all chunks for a specific document."""
        try:
            # Find and delete chunks for the document
            chunks_to_delete = []
            for chunk_id, chunk_data in self.embeddings_data.items():
                if chunk_data['document_id'] == document_id:
                    chunks_to_delete.append(chunk_id)
            
            # Delete chunks
            for chunk_id in chunks_to_delete:
                del self.embeddings_data[chunk_id]
            
            # Save updated data
            self._save_embeddings()
            
            logger.info(f"Deleted {len(chunks_to_delete)} chunks for document {document_id}")
            return len(chunks_to_delete) > 0
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        try:
            total_chunks = len(self.embeddings_data)
            document_counts = {}
            for chunk_data in self.embeddings_data.values():
                doc_id = chunk_data['document_id']
                document_counts[doc_id] = document_counts.get(doc_id, 0) + 1
            
            return {
                'total_chunks': total_chunks,
                'documents_with_chunks': len(document_counts),
                'embedding_model': self.embedding_model,
                'storage_path': self.storage_path
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def reset_collection(self) -> bool:
        """Reset the entire collection (use with caution)."""
        try:
            self.embeddings_data = {}
            self._save_embeddings()
            logger.warning("Vector store has been reset")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            return False


# Global vector store instance
vector_store = VectorStore()
