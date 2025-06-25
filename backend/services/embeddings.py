import os
from typing import List
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the embedding service
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.logger = logger
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = None
        self.dimension = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Get the embedding dimension
            test_embedding = self.model.encode(["test"], convert_to_numpy=True)
            self.dimension = test_embedding.shape[1]
            
            self.logger.info(f"Loaded model {self.model_name} with dimension {self.dimension}")
            
        except Exception as e:
            self.logger.error(f"Error loading embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if self.model is None:
                raise ValueError("Model not loaded")
            
            # Generate embedding
            embedding = self.model.encode([text.strip()], convert_to_numpy=True)
            
            # Convert to list and ensure it's float32
            embedding_list = embedding[0].astype(np.float32).tolist()
            
            return embedding_list
            
        except Exception as e:
            self.logger.error(f"Error generating embedding for text: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        try:
            if not texts:
                return []
            
            if self.model is None:
                raise ValueError("Model not loaded")
            
            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not valid_texts:
                return []
            
            # Generate embeddings
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
            
            # Convert to list of lists
            embeddings_list = [emb.astype(np.float32).tolist() for emb in embeddings]
            
            self.logger.debug(f"Generated {len(embeddings_list)} embeddings")
            return embeddings_list
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings for texts: {e}")
            raise
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_sequence_length": getattr(self.model, 'max_seq_length', 'unknown') if self.model else None
        }
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        try:
            # Convert to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
        candidate_embeddings: List[List[float]], 
        top_k: int = 5) -> List[tuple]:
        """
        Find the most similar embeddings to a query
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            
        Returns:
            List of tuples (index, similarity_score) sorted by similarity
        """
        try:
            similarities = []
            
            for i, candidate_emb in enumerate(candidate_embeddings):
                sim_score = self.similarity(query_embedding, candidate_emb)
                similarities.append((i, sim_score))
            
            # Sort by similarity score (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top_k results
            return similarities[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error finding most similar embeddings: {e}")
            return [] 