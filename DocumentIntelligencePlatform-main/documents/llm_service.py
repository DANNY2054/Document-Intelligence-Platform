"""
LLM service for generating answers using OpenAI API.
"""
import os
import json
import logging
from typing import Dict, List, Any
from django.conf import settings

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating answers using OpenAI."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in settings or environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Latest OpenAI model
        self.max_tokens = 1000
        self.temperature = 0.2  # Lower temperature for more consistent answers
    
    def generate_answer(self, question: str, context_chunks: List[Dict], document_title: str) -> Dict[str, Any]:
        """
        Generate answer using question and context chunks.
        Returns answer with confidence score and sources.
        """
        try:
            # Prepare context from chunks
            context = self._prepare_context(context_chunks)
            
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create user prompt
            user_prompt = self._create_user_prompt(question, context, document_title)
            
            # Generate answer
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Add source information
            result['sources'] = self._format_sources(context_chunks)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                'answer': f"I apologize, but I encountered an error while processing your question: {str(e)}",
                'confidence': 0.0,
                'sources': []
            }
    
    def _prepare_context(self, chunks: List[Dict]) -> str:
        """Prepare context text from chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            page_info = ""
            if chunk.get('page_numbers'):
                pages = chunk['page_numbers']
                if isinstance(pages, list) and pages:
                    page_info = f" (Page {', '.join(map(str, pages))})"
            
            context_parts.append(
                f"[Context {i}]{page_info}:\n{chunk['text']}\n"
            )
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the LLM."""
        return """You are a helpful AI assistant that answers questions based on provided document context. 

Your task is to:
1. Answer the user's question using ONLY the information provided in the context
2. Be accurate and concise
3. If the context doesn't contain enough information, say so clearly
4. Provide a confidence score between 0.0 and 1.0 based on how well the context supports your answer
5. Always respond in JSON format with the following structure:
{
    "answer": "Your detailed answer here",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why you have this confidence level"
}

Guidelines:
- If the context clearly answers the question: confidence 0.8-1.0
- If the context partially answers the question: confidence 0.4-0.7
- If the context barely relates to the question: confidence 0.1-0.3
- If the context doesn't help at all: confidence 0.0
"""
    
    def _create_user_prompt(self, question: str, context: str, document_title: str) -> str:
        """Create user prompt with question and context."""
        return f"""Document: "{document_title}"

Context:
{context}

Question: {question}

Please answer the question based on the provided context. Remember to respond in JSON format with answer, confidence, and reasoning fields."""
    
    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Format source information for response."""
        sources = []
        
        for chunk in chunks:
            source = {
                'chunk_index': chunk.get('chunk_index', 0),
                'page_numbers': chunk.get('page_numbers', []),
                'text_preview': chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
                'similarity': round(chunk.get('similarity', 0.0), 3),
                'token_count': chunk.get('token_count', 0)
            }
            sources.append(source)
        
        return sources
    
    def generate_embedding_summary(self, text: str) -> str:
        """Generate a brief summary for embedding purposes."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Create a brief, informative summary of the following text in 1-2 sentences."
                    },
                    {"role": "user", "content": text}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return text[:200] + "..." if len(text) > 200 else text
    
    def validate_question(self, question: str) -> Dict[str, Any]:
        """Validate and improve question quality."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the given question and provide feedback on its quality for document search.
                        Respond in JSON format with:
                        {
                            "is_valid": true/false,
                            "improved_question": "improved version if needed",
                            "suggestions": ["list of suggestions for better results"]
                        }"""
                    },
                    {"role": "user", "content": f"Question: {question}"}
                ],
                max_tokens=200,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error validating question: {str(e)}")
            return {
                "is_valid": True,
                "improved_question": question,
                "suggestions": []
            }


# Global LLM service instance
llm_service = LLMService()
