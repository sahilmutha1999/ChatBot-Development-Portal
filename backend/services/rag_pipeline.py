import asyncio
from typing import Dict, Any, List
import logging
from datetime import datetime

from .unified_embedding_service import UnifiedEmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class RAGPipeline:
    """Complete RAG pipeline for processing and storing content with embeddings"""
    
    def __init__(self):
        """Initialize the RAG pipeline"""
        self.logger = logger
        self.embedding_service = UnifiedEmbeddingService()
        self.vector_store = VectorStore()
    
    async def process_and_store_html(self, html_content: str, source_name: str) -> Dict[str, Any]:
        """
        Complete pipeline: HTML → Embeddings → Vector Store
        
        Args:
            html_content: HTML content to process
            source_name: Name of the source (used for metadata and identification)
            
        Returns:
            Dictionary containing processing and storage results
        """
        try:
            self.logger.info(f"Starting RAG pipeline for: {source_name}")
            
            # Step 1: Process content into embeddings
            self.logger.info("Step 1: Processing content and generating embeddings...")
            processing_result = self.embedding_service.process_html_content(html_content, source_name)
            
            # Step 2: Store embeddings in vector database
            self.logger.info("Step 2: Storing embeddings in Pinecone...")
            storage_result = await self._store_embeddings(processing_result["chunks"], source_name)
            
            # Step 3: Compile final results
            pipeline_result = {
                "source": source_name,
                "processing": {
                    "total_chunks": processing_result["total_chunks"],
                    "text_chunks": processing_result["text_chunks"],
                    "image_chunks": processing_result["image_chunks"],
                    "markdown_file": processing_result.get("markdown_file"),
                    "processed_at": processing_result["processed_at"]
                },
                "storage": storage_result,
                "success": storage_result["successful_upserts"] > 0
            }
            
            self.logger.info(f"RAG pipeline completed for {source_name}: "
                           f"{storage_result['successful_upserts']}/{processing_result['total_chunks']} chunks stored")
            
            return pipeline_result
            
        except Exception as e:
            self.logger.error(f"Error in RAG pipeline for {source_name}: {e}")
            raise
    
    async def _store_embeddings(self, chunks: List[Dict[str, Any]], source_name: str) -> Dict[str, Any]:
        """Store embedding chunks in Pinecone vector database"""
        try:
            # Prepare chunks for batch upsert
            vector_chunks = []
            
            for chunk in chunks:
                # Ensure proper metadata structure
                metadata = {
                    "content": chunk["content"],
                    "source": source_name,
                    "content_type": chunk["metadata"]["content_type"],
                    "created_at": datetime.now().isoformat()
                }
                
                # Add content-type specific metadata
                if chunk["metadata"]["content_type"] == "text":
                    metadata.update({
                        "chunk_type": chunk["metadata"].get("chunk_type", "general"),
                        "char_count": len(chunk["content"])
                    })
                elif chunk["metadata"]["content_type"] == "image":
                    metadata.update({
                        "image_path": chunk["metadata"].get("image_path", ""),
                        "alt_text": chunk["metadata"].get("alt_text", ""),
                        "original_src": chunk["metadata"].get("original_src", ""),
                        "has_gemini_analysis": bool(chunk["metadata"].get("gemini_description"))
                    })
                
                vector_chunk = {
                    "id": chunk["id"],
                    "embedding": chunk["embedding"],
                    "metadata": metadata
                }
                vector_chunks.append(vector_chunk)
            
            # Batch upsert to Pinecone
            successful_upserts = await self.vector_store.upsert_batch(vector_chunks)
            
            result = {
                "total_chunks": len(chunks),
                "successful_upserts": successful_upserts,
                "failed_upserts": len(chunks) - successful_upserts,
                "storage_timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing embeddings: {e}")
            raise
    
    async def search_similar_content(self, 
                                   query: str, 
                                   top_k: int = 5,
                                   content_type_filter: str = None) -> List[Dict[str, Any]]:
        """
        Search for similar content in the vector database
        
        Args:
            query: Search query text
            top_k: Number of results to return
            content_type_filter: Filter by content type ("text" or "image")
            
        Returns:
            List of similar chunks with scores
        """
        try:
            # Generate embedding for query
            query_embedding = self.embedding_service.text_embedding_service.embed_text(query)
            
            # Prepare filter
            filter_dict = None
            if content_type_filter:
                filter_dict = {"content_type": content_type_filter}
            
            # Search in vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict
            )
            
            self.logger.info(f"Found {len(results)} similar chunks for query: {query[:50]}...")
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching similar content: {e}")
            return []
    
    async def delete_source_content(self, source_name: str) -> bool:
        """Delete all content from a specific source"""
        try:
            success = await self.vector_store.delete_by_source(source_name)
            if success:
                self.logger.info(f"Successfully deleted all content for source: {source_name}")
            else:
                self.logger.warning(f"Failed to delete content for source: {source_name}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting source content: {e}")
            return False
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of the RAG pipeline components"""
        try:
            # Check vector store health
            vector_store_healthy = await self.vector_store.health_check()
            
            # Get index stats
            index_stats = await self.vector_store.get_index_stats()
            
            # Get embedding service stats
            embedding_stats = self.embedding_service.get_embedding_stats()
            
            status = {
                "vector_store": {
                    "healthy": vector_store_healthy,
                    "stats": index_stats
                },
                "embedding_service": embedding_stats,
                "pipeline_ready": vector_store_healthy,
                "checked_at": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting pipeline status: {e}")
            return {
                "error": str(e),
                "pipeline_ready": False,
                "checked_at": datetime.now().isoformat()
            } 