import asyncio
from typing import Dict, Any, List
import logging
from datetime import datetime
import time

from .rag_pipeline import RAGPipeline
from .qa_processor import QAProcessor
from .evaluation_service import RAGEvaluationService

logger = logging.getLogger(__name__)

class QAPipeline:
    """Complete Q&A pipeline that combines vector search with Gemini processing"""
    
    def __init__(self):
        """Initialize the Q&A pipeline"""
        self.logger = logger
        self.rag_pipeline = RAGPipeline()
        self.qa_processor = QAProcessor()
        self.evaluation_service = RAGEvaluationService()
    
    async def answer_question(self, user_question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Complete Q&A pipeline: Question → Vector Search → Gemini → Answer → Evaluation
        
        Args:
            user_question: The user's question
            top_k: Number of top chunks to retrieve from vector search (default: 3)
            
        Returns:
            Dictionary containing the answer, sources, evaluation metrics, and metadata
        """
        try:
            start_time = time.time()
            self.logger.info(f"Processing question: {user_question[:100]}...")
            
            # Step 1: Vector search to find relevant content
            self.logger.info("Step 1: Searching vector database...")
            search_results = await self.rag_pipeline.search_similar_content(
                query=user_question,
                top_k=top_k
            )
            
            self.logger.info(f"Found {len(search_results)} relevant chunks")
            
            # Step 2: Generate answer using Gemini
            self.logger.info("Step 2: Generating answer with Gemini...")
            qa_result = self.qa_processor.generate_answer(user_question, search_results)
            
            # Step 3: Generate follow-up suggestions
            self.logger.info("Step 3: Generating follow-up suggestions...")
            suggestions = self.qa_processor.generate_followup_suggestions(user_question, search_results)
            
            # Step 4: Calculate accuracy metrics
            processing_time = time.time() - start_time
            self.logger.info("Step 4: Calculating accuracy metrics...")
            
            answer_text = qa_result.get("answer", "")
            evaluation_metrics = self.evaluation_service.evaluate_query_response(
                query=user_question,
                answer=answer_text,
                retrieved_chunks=search_results,
                processing_time=processing_time
            )
            
            # Step 5: Compile complete response with evaluation
            complete_response = {
                "question": user_question,
                "answer": answer_text,
                "success": qa_result.get("success", False),
                "confidence": qa_result.get("confidence", "low"),
                "sources": {
                    "total_sources": qa_result.get("sources_used", 0),
                    "source_details": qa_result.get("source_details", []),
                    "search_results": [
                        {
                            "content_preview": result['metadata'].get('content', '')[:200] + "...",
                            "content_type": result['metadata'].get('content_type', 'unknown'),
                            "source": result['metadata'].get('source', 'unknown'),
                            "similarity_score": round(result['score'], 3)
                        }
                        for result in search_results
                    ]
                },
                "follow_up_suggestions": suggestions,
                "accuracy_metrics": evaluation_metrics,
                "processing_info": {
                    "vector_search_results": len(search_results),
                    "qa_success": qa_result.get("success", False),
                    "processing_time_seconds": round(processing_time, 3),
                    "processed_at": datetime.now().isoformat()
                }
            }
            
            # Add error information if available
            if "error" in qa_result:
                complete_response["error"] = qa_result["error"]
            
            self.logger.info(f"Q&A pipeline completed successfully for question: {user_question[:50]}... "
                           f"Overall accuracy: {evaluation_metrics.get('overall_accuracy', {}).get('score', 0):.2f}")
            return complete_response
            
        except Exception as e:
            self.logger.error(f"Error in Q&A pipeline: {e}")
            return {
                "question": user_question,
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again.",
                "success": False,
                "confidence": "low",
                "sources": {"total_sources": 0, "source_details": [], "search_results": []},
                "follow_up_suggestions": [],
                "error": str(e),
                "processing_info": {
                    "vector_search_results": 0,
                    "qa_success": False,
                    "processed_at": datetime.now().isoformat()
                }
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get the status of all Q&A pipeline components"""
        try:
            # Check RAG pipeline status
            rag_status = await self.rag_pipeline.get_pipeline_status()
            
            # Check QA processor status
            qa_available = self.qa_processor.gemini_model is not None
            
            status = {
                "qa_pipeline_ready": rag_status.get("pipeline_ready", False) and qa_available,
                "components": {
                    "vector_search": {
                        "ready": rag_status.get("pipeline_ready", False),
                        "vector_store": rag_status.get("vector_store", {}),
                        "embedding_service": rag_status.get("embedding_service", {})
                    },
                    "qa_processor": {
                        "ready": qa_available,
                        "gemini_available": qa_available
                    }
                },
                "checked_at": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                "qa_pipeline_ready": False,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }
    
    async def process_and_index_content(self, html_content: str, source_name: str) -> Dict[str, Any]:
        """
        Process and index new content for the Q&A system
        
        Args:
            html_content: HTML content to process and index
            source_name: Name identifier for the content source
            
        Returns:
            Processing result with success/failure information
        """
        try:
            self.logger.info(f"Processing and indexing content: {source_name}")
            
            # Use the RAG pipeline to process and store content
            result = await self.rag_pipeline.process_and_store_html(html_content, source_name)
            
            self.logger.info(f"Successfully indexed {source_name}: "
                           f"{result['processing']['total_chunks']} chunks stored")
            
            return {
                "success": result.get("success", False),
                "source": source_name,
                "processing": result.get("processing", {}),
                "storage": result.get("storage", {}),
                "message": f"Successfully processed and indexed {source_name}"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing content {source_name}: {e}")
            return {
                "success": False,
                "source": source_name,
                "error": str(e),
                "message": f"Failed to process {source_name}"
            } 