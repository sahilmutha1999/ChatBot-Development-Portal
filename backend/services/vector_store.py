import os
from typing import List, Dict, Any, Optional
import logging
from pinecone import Pinecone, ServerlessSpec
import asyncio
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class VectorStore:
    """Service for managing vector storage with Pinecone"""
    
    def __init__(self):
        """Initialize Pinecone connection"""
        self.logger = logger
        self.pc = None
        self.index = None
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "dev-portal-chatbot")
        self.dimension = int(os.getenv("EMBEDDING_DIMENSION", "384"))  # Default for sentence-transformers
        
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index"""
        try:
            api_key = os.getenv("PINECONE_API_KEY")
            if not api_key:
                raise ValueError("PINECONE_API_KEY environment variable is required")
            
            # Initialize Pinecone
            self.pc = Pinecone(api_key=api_key)
            
            # Check if index exists, create if not
            existing_indexes = [index_info["name"] for index_info in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                self.logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"  # Use the region closest to you
                    )
                )
                self.logger.info(f"Created Pinecone index: {self.index_name}")
            
            # Connect to the index
            self.index = self.pc.Index(self.index_name)
            self.logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            self.logger.error(f"Error initializing Pinecone: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Pinecone connection is healthy"""
        try:
            if self.index is None:
                return False
            
            # Try to get index stats
            stats = self.index.describe_index_stats()
            return True
            
        except Exception as e:
            self.logger.error(f"Pinecone health check failed: {e}")
            return False
    
    async def upsert_chunk(self, 
        chunk_id: str, 
        embedding: List[float], 
        metadata: Dict[str, Any]) -> bool:
        """
        Store a chunk embedding in Pinecone
        
        Args:
            chunk_id: Unique identifier for the chunk
            embedding: Vector embedding of the chunk
            metadata: Metadata associated with the chunk
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.index is None:
                raise ValueError("Pinecone index not initialized")
            
            # Prepare the vector for upsert
            vector_data = {
                "id": chunk_id,
                "values": embedding,
                "metadata": metadata
            }
            
            # Upsert to Pinecone
            self.index.upsert(vectors=[vector_data])
            
            self.logger.debug(f"Successfully upserted chunk: {chunk_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error upserting chunk {chunk_id}: {e}")
            return False
    
    async def upsert_batch(self, 
                          chunks: List[Dict[str, Any]]) -> int:
        """
        Batch upsert multiple chunks
        
        Args:
            chunks: List of chunk dictionaries with id, embedding, and metadata
        
        Returns:
            Number of successfully upserted chunks
        """
        try:
            if self.index is None:
                raise ValueError("Pinecone index not initialized")
            
            # Prepare batch data
            vectors = []
            for chunk in chunks:
                vectors.append({
                    "id": chunk["id"],
                    "values": chunk["embedding"],
                    "metadata": chunk["metadata"]
                })
            
            # Batch upsert (Pinecone recommends batches of 100 or fewer)
            batch_size = 100
            successful_upserts = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                try:
                    self.index.upsert(vectors=batch)
                    successful_upserts += len(batch)
                except Exception as e:
                    self.logger.error(f"Error upserting batch {i//batch_size + 1}: {e}")
                    continue
            
            self.logger.info(f"Successfully upserted {successful_upserts}/{len(chunks)} chunks")
            return successful_upserts
            
        except Exception as e:
            self.logger.error(f"Error in batch upsert: {e}")
            return 0
    
    async def search(self, 
                    query_embedding: List[float], 
                    top_k: int = 5,
                    filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar chunks
        
        Args:
            query_embedding: Vector embedding of the query
            top_k: Number of top results to return
            filter_dict: Optional metadata filters
        
        Returns:
            List of matching chunks with scores
        """
        try:
            if self.index is None:
                raise ValueError("Pinecone index not initialized")
            
            # Perform the search
            search_response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_values=False,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            results = []
            for match in search_response.matches:
                results.append({
                    "id": match.id,
                    "score": float(match.score),
                    "metadata": match.metadata
                })
            
            self.logger.debug(f"Found {len(results)} matches for query")
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching vectors: {e}")
            return []
    
    async def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a specific chunk"""
        try:
            if self.index is None:
                raise ValueError("Pinecone index not initialized")
            
            self.index.delete(ids=[chunk_id])
            self.logger.debug(f"Deleted chunk: {chunk_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting chunk {chunk_id}: {e}")
            return False
    
    async def delete_by_source(self, source: str) -> bool:
        """Delete all chunks from a specific source"""
        try:
            if self.index is None:
                raise ValueError("Pinecone index not initialized")
            
            # Delete by metadata filter
            self.index.delete(filter={"source": source})
            self.logger.info(f"Deleted all chunks from source: {source}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting chunks from source {source}: {e}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the index"""
        try:
            if self.index is None:
                raise ValueError("Pinecone index not initialized")
            
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
            
        except Exception as e:
            self.logger.error(f"Error getting index stats: {e}")
            return {}
    
    async def list_chunks_by_source(self, source: str) -> List[Dict[str, Any]]:
        """List all chunks from a specific source"""
        try:
            # Note: Pinecone doesn't have a direct "list" operation
            # This would require fetching by known IDs or using a different approach
            # For now, we'll return an empty list and log that this feature needs implementation
            self.logger.warning("list_chunks_by_source not fully implemented - Pinecone limitations")
            return []
            
        except Exception as e:
            self.logger.error(f"Error listing chunks by source {source}: {e}")
            return [] 