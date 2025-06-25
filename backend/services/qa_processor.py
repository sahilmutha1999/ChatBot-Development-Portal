import os
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import google.generativeai as genai
import dotenv

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class QAProcessor:
    """Service for processing Q&A using Gemini with vector search results"""
    
    def __init__(self):
        """Initialize the QA processor with Gemini"""
        self.logger = logger
        self.gemini_model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini for Q&A processing"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                self.logger.error("GOOGLE_API_KEY not found. Q&A processing will not work.")
                return
            
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Gemini model initialized for Q&A processing")
            
        except Exception as e:
            self.logger.error(f"Error initializing Gemini: {e}")
            self.gemini_model = None
    
    def generate_answer(self, user_query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate an answer using Gemini based on user query and vector search results
        
        Args:
            user_query: The user's question
            search_results: Top chunks from vector search with scores and metadata
            
        Returns:
            Dictionary containing the generated answer and metadata
        """
        try:
            if not self.gemini_model:
                return {
                    "answer": "I'm sorry, but I'm currently unable to process your question. The Q&A service is not available.",
                    "success": False,
                    "error": "Gemini model not available"
                }
            
            if not search_results:
                return {
                    "answer": "I couldn't find any relevant information to answer your question. Please try rephrasing your question or ask about a different topic.",
                    "success": True,
                    "sources_used": 0,
                    "confidence": "low"
                }
            
            # Prepare context from search results
            context_info = self._prepare_context(search_results)
            
            # Generate the prompt
            prompt = self._create_qa_prompt(user_query, context_info)
            
            # Get response from Gemini
            response = self.gemini_model.generate_content(prompt)
            
            if response and response.text:
                answer = response.text.strip()
                
                return {
                    "answer": answer,
                    "success": True,
                    "sources_used": len(search_results),
                    "confidence": self._assess_confidence(search_results),
                    "source_details": [
                        {
                            "content_type": result['metadata'].get('content_type', 'unknown'),
                            "source": result['metadata'].get('source', 'unknown'),
                            "similarity_score": round(result['score'], 3)
                        }
                        for result in search_results
                    ],
                    "processed_at": datetime.now().isoformat()
                }
            else:
                return {
                    "answer": "I'm having trouble generating a response right now. Please try again.",
                    "success": False,
                    "error": "Empty response from Gemini"
                }
                
        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again.",
                "success": False,
                "error": str(e)
            }
    
    def _prepare_context(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare context information from search results"""
        context_chunks = []
        text_sources = 0
        image_sources = 0
        
        for i, result in enumerate(search_results, 1):
            content = result['metadata'].get('content', '')
            content_type = result['metadata'].get('content_type', 'unknown')
            source = result['metadata'].get('source', 'unknown')
            score = result.get('score', 0)
            
            # Categorize content types
            if content_type == 'text':
                text_sources += 1
            elif content_type == 'image':
                image_sources += 1
            
            context_chunks.append({
                "chunk_number": i,
                "content": content,
                "content_type": content_type,
                "source": source,
                "relevance_score": round(score, 3)
            })
        
        return {
            "chunks": context_chunks,
            "total_sources": len(search_results),
            "text_sources": text_sources,
            "image_sources": image_sources
        }
    
    def _create_qa_prompt(self, user_query: str, context_info: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for Gemini Q&A"""
        
        # Build the context section
        context_text = ""
        for chunk in context_info["chunks"]:
            context_text += f"""
CHUNK {chunk['chunk_number']}:
{chunk['content']}

---
"""
        
        prompt = f"""
You are an intelligent assistant helping users understand business processes and documentation.

USER QUESTION: "{user_query}"

RELEVANT INFORMATION:
{context_text}

INSTRUCTIONS:
1. **Answer the user's question directly and comprehensively** using ONLY the information provided above.

2. **Be specific and detailed** - if there are steps, processes, or procedures mentioned, explain them clearly.

3. **Present information naturally** - don't mention sources, diagrams, or reference materials. Just provide the information as if it's your knowledge.

4. **If the information doesn't fully answer the question**: 
   - Provide what you can from the available information
   - Simply state that you don't have additional details on that specific aspect

5. **Structure your response clearly**:
   - Start with a direct answer
   - Provide supporting details
   - Include relevant process steps if applicable

6. **Do not make up information** that is not in the provided context.

7. **Be conversational and helpful** - answer as if you're an expert on the topic.

Please answer the user's question:
"""

        return prompt
    
    def _assess_confidence(self, search_results: List[Dict[str, Any]]) -> str:
        """Assess confidence level based on search results"""
        if not search_results:
            return "low"
        
        # Check average similarity score
        avg_score = sum(result.get('score', 0) for result in search_results) / len(search_results)
        
        if avg_score >= 0.7:
            return "high"
        elif avg_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def generate_followup_suggestions(self, user_query: str, search_results: List[Dict[str, Any]]) -> List[str]:
        """Generate follow-up question suggestions based on the context"""
        try:
            if not self.gemini_model or not search_results:
                return []
            
            # Get content from search results
            content_summary = "\n".join([
                result['metadata'].get('content', '')[:200] + "..."
                for result in search_results[:2]  # Use top 2 results
            ])
            
            prompt = f"""
Based on the user's question: "{user_query}"
And this related content: {content_summary}

Generate 3 short, relevant follow-up questions that the user might want to ask. 
Focus on:
- Related aspects of the same topic
- Next steps in processes
- Clarifying details

Format as a simple list of questions, each on a new line starting with "- ".
Keep each question under 15 words.
"""
            
            response = self.gemini_model.generate_content(prompt)
            
            if response and response.text:
                # Parse the response to extract questions
                lines = response.text.strip().split('\n')
                suggestions = []
                for line in lines:
                    line = line.strip()
                    if line.startswith('- '):
                        suggestions.append(line[2:].strip())
                    elif line and not line.startswith('-') and len(suggestions) < 3:
                        suggestions.append(line.strip())
                
                return suggestions[:3]  # Return max 3 suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating follow-up suggestions: {e}")
        
        return [] 