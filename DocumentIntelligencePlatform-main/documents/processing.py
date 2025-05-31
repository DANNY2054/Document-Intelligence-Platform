"""
Document processing pipeline for text extraction and chunking.
"""
import os
import re
import logging
from typing import List, Dict, Tuple
from django.conf import settings

# Text extraction libraries
import docx
import PyPDF2
from io import BytesIO

# Tokenization and chunking
import tiktoken

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document text extraction and chunking."""
    
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        self.chunk_size = getattr(settings, 'CHUNK_SIZE', 500)
        self.chunk_overlap = getattr(settings, 'CHUNK_OVERLAP', 50)
    
    def extract_text(self, file_path: str, file_type: str) -> Tuple[str, int]:
        """
        Extract text from document based on file type.
        Returns: (extracted_text, page_count)
        """
        try:
            if file_type == 'txt' or file_type == 'md':
                return self._extract_from_txt(file_path)
            elif file_type == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type == 'docx':
                return self._extract_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    def _extract_from_txt(self, file_path: str) -> Tuple[str, int]:
        """Extract text from TXT/MD files."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
        
        # Estimate page count (assuming ~500 words per page)
        word_count = len(text.split())
        page_count = max(1, word_count // 500)
        
        return text, page_count
    
    def _extract_from_pdf(self, file_path: str) -> Tuple[str, int]:
        """Extract text from PDF files."""
        text = ""
        page_count = 0
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n[Page {page_num + 1}]\n{page_text}\n"
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1}: {str(e)}")
                    continue
        
        return text, page_count
    
    def _extract_from_docx(self, file_path: str) -> Tuple[str, int]:
        """Extract text from DOCX files."""
        doc = docx.Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        
        # Estimate page count (assuming ~500 words per page)
        word_count = len(text.split())
        page_count = max(1, word_count // 500)
        
        return text, page_count
    
    def chunk_text(self, text: str, document_id: int) -> List[Dict]:
        """
        Split text into chunks with overlap.
        Returns list of chunk dictionaries.
        """
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split into sentences for better chunking
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk.strip(),
                    chunk_index,
                    document_id
                ))
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence
                current_tokens = len(self.tokenizer.encode(current_chunk))
                chunk_index += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens
        
        # Add final chunk if there's remaining text
        if current_chunk.strip():
            chunks.append(self._create_chunk(
                current_chunk.strip(),
                chunk_index,
                document_id
            ))
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page markers for cleaner chunks
        text = re.sub(r'\[Page \d+\]', '', text)
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (can be improved with NLTK or spaCy)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk."""
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= self.chunk_overlap:
            return text
        
        overlap_tokens = tokens[-self.chunk_overlap:]
        return self.tokenizer.decode(overlap_tokens)
    
    def _create_chunk(self, text: str, chunk_index: int, document_id: int) -> Dict:
        """Create chunk dictionary."""
        # Extract page numbers from text (if any)
        page_numbers = self._extract_page_numbers(text)
        
        return {
            'text': text,
            'chunk_index': chunk_index,
            'page_numbers': page_numbers,
            'token_count': len(self.tokenizer.encode(text)),
            'document_id': document_id
        }
    
    def _extract_page_numbers(self, text: str) -> List[int]:
        """Extract page numbers from text."""
        page_matches = re.findall(r'\[Page (\d+)\]', text)
        return [int(page) for page in page_matches] if page_matches else [1]


class ChunkingStrategy:
    """Advanced chunking strategies."""
    
    @staticmethod
    def semantic_chunking(text: str, similarity_threshold: float = 0.7) -> List[str]:
        """
        Semantic chunking using sentence similarity.
        This is a placeholder for more advanced semantic chunking.
        """
        # This would require sentence-transformers for semantic similarity
        # For now, return basic paragraph-based chunking
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    @staticmethod
    def fixed_size_chunking(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Fixed size chunking with token overlap."""
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - overlap if end < len(tokens) else end
        
        return chunks
