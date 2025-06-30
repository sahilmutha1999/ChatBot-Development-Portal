import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import json
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RAGEvaluationService:
    """
    Real-time RAG evaluation service that calculates accuracy metrics
    for each query including retrieval quality, answer relevance, and content coverage
    """
    
    def __init__(self):
        self.logger = logger
        self.embedding_model = None
        self.genai_model = None
        self._initialize_models()
        
        # Evaluation thresholds
        self.SIMILARITY_THRESHOLD = 0.3  # Minimum score for relevant retrieval
        self.HIGH_CONFIDENCE_THRESHOLD = 0.7
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.5
        
    def _initialize_models(self):
        """Initialize models for evaluation"""
        try:
            # Initialize embedding model for semantic similarity
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize Gemini for AI-based evaluation
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.genai_model = genai.GenerativeModel('gemini-1.5-flash')
                
            self.logger.info("Evaluation models initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing evaluation models: {e}")
    
    def calculate_retrieval_metrics(self, 
                                  query: str, 
                                  retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate retrieval-specific metrics
        """
        try:
            if not retrieved_chunks:
                return {
                    "hit_rate": 0.0,
                    "precision_at_k": 0.0,
                    "mean_similarity": 0.0,
                    "relevant_chunks": 0,
                    "total_chunks": 0
                }
            
            # Extract similarity scores
            scores = [chunk.get('score', 0.0) for chunk in retrieved_chunks]
            
            # Calculate relevant chunks (above threshold)
            relevant_chunks = [s for s in scores if s >= self.SIMILARITY_THRESHOLD]
            
            # Hit Rate: Did we retrieve at least one relevant chunk?
            hit_rate = 1.0 if len(relevant_chunks) > 0 else 0.0
            
            # Precision@K: What percentage of retrieved chunks are relevant?
            precision_at_k = len(relevant_chunks) / len(retrieved_chunks) if retrieved_chunks else 0.0
            
            # Mean similarity score
            mean_similarity = np.mean(scores) if scores else 0.0
            
            return {
                "hit_rate": round(hit_rate, 3),
                "precision_at_k": round(precision_at_k, 3),
                "mean_similarity": round(mean_similarity, 3),
                "relevant_chunks": len(relevant_chunks),
                "total_chunks": len(retrieved_chunks),
                "similarity_scores": [round(s, 3) for s in scores]
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating retrieval metrics: {e}")
            return {"error": str(e)}
    
    def calculate_content_coverage(self, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze content type distribution and coverage
        """
        try:
            content_types = {}
            sources = set()
            
            for chunk in retrieved_chunks:
                metadata = chunk.get('metadata', {})
                content_type = metadata.get('content_type', 'unknown')
                source = metadata.get('source', 'unknown')
                
                content_types[content_type] = content_types.get(content_type, 0) + 1
                sources.add(source)
            
            # Calculate coverage metrics
            total_chunks = len(retrieved_chunks)
            unique_content_types = len(content_types)
            unique_sources = len(sources)
            
            # Content diversity score (0-1)
            diversity_score = min(unique_content_types / 3.0, 1.0)  # Normalize by expected 3 types
            
            return {
                "content_types": content_types,
                "unique_content_types": unique_content_types,
                "unique_sources": unique_sources,
                "diversity_score": round(diversity_score, 3),
                "coverage_analysis": {
                    "has_text": "text" in content_types,
                    "has_image": "image" in content_types,
                    "has_openapi": "openapi" in content_types
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating content coverage: {e}")
            return {"error": str(e)}
    
    def calculate_answer_relevance(self, query: str, answer: str) -> Dict[str, Any]:
        """
        Calculate semantic relevance between query and answer
        """
        try:
            if not self.embedding_model or not query.strip() or not answer.strip():
                return {"relevance_score": 0.0, "explanation": "Missing data for relevance calculation"}
            
            # Generate embeddings
            query_embedding = self.embedding_model.encode([query])
            answer_embedding = self.embedding_model.encode([answer])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, answer_embedding)[0][0]
            
            # Assess relevance quality
            if similarity >= 0.8:
                quality = "Excellent"
            elif similarity >= 0.6:
                quality = "Good"
            elif similarity >= 0.4:
                quality = "Fair"
            else:
                quality = "Poor"
            
            return {
                "relevance_score": round(float(similarity), 3),
                "quality_assessment": quality,
                "explanation": f"Answer relevance to query: {quality} ({round(similarity*100, 1)}%)"
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating answer relevance: {e}")
            return {"relevance_score": 0.0, "error": str(e)}
    
    def assess_answer_quality(self, query: str, answer: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        AI-based assessment of answer quality and faithfulness
        """
        try:
            if not self.genai_model:
                return self._fallback_quality_assessment(query, answer, retrieved_chunks)
            
            # Prepare context from retrieved chunks
            context_texts = []
            for chunk in retrieved_chunks[:3]:  # Use top 3 chunks
                metadata = chunk.get('metadata', {})
                content = metadata.get('content', '')[:500]  # Limit content length
                content_type = metadata.get('content_type', 'text')
                context_texts.append(f"[{content_type.upper()}] {content}")
            
            context = "\n\n".join(context_texts)
            
            evaluation_prompt = f"""
            Evaluate this RAG system response on a scale of 0-100 for each criterion:

            QUERY: "{query}"
            
            RETRIEVED CONTEXT:
            {context}
            
            GENERATED ANSWER: "{answer}"
            
            Evaluate these aspects (return JSON format):
            1. faithfulness: Is the answer grounded in the provided context? (0-100)
            2. completeness: Does the answer fully address the query? (0-100)
            3. clarity: Is the answer clear and well-structured? (0-100)
            4. accuracy: Is the information factually correct? (0-100)
            
            Return only a JSON object with these scores and a brief explanation.
            """
            
            response = self.genai_model.generate_content(evaluation_prompt)
            
            if response and response.text:
                # Try to parse JSON response
                try:
                    evaluation = json.loads(response.text.strip())
                    
                    # Calculate overall quality score
                    scores = [
                        evaluation.get('faithfulness', 50),
                        evaluation.get('completeness', 50),
                        evaluation.get('clarity', 50),
                        evaluation.get('accuracy', 50)
                    ]
                    overall_score = np.mean(scores)
                    
                    return {
                        "faithfulness": evaluation.get('faithfulness', 50),
                        "completeness": evaluation.get('completeness', 50),
                        "clarity": evaluation.get('clarity', 50),
                        "accuracy": evaluation.get('accuracy', 50),
                        "overall_quality": round(overall_score, 1),
                        "explanation": evaluation.get('explanation', 'AI-based quality assessment'),
                        "evaluation_method": "ai_based"
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to simple parsing
                    return self._parse_ai_response(response.text)
            
            return self._fallback_quality_assessment(query, answer, retrieved_chunks)
            
        except Exception as e:
            self.logger.error(f"Error in AI quality assessment: {e}")
            return self._fallback_quality_assessment(query, answer, retrieved_chunks)
    
    def _fallback_quality_assessment(self, query: str, answer: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback quality assessment using heuristics
        """
        try:
            # Simple heuristic scoring
            word_count = len(answer.split())
            has_specifics = bool(re.search(r'\d+|%|\$|API|endpoint|process|system', answer, re.IGNORECASE))
            mentions_context = any(
                chunk.get('metadata', {}).get('content_type', '') in answer.lower() 
                for chunk in retrieved_chunks
            )
            
            # Score components
            length_score = min(word_count / 50.0 * 100, 100)  # Normalize by expected 50 words
            specificity_score = 80 if has_specifics else 40
            context_score = 90 if mentions_context else 50
            
            overall_score = (length_score + specificity_score + context_score) / 3
            
            return {
                "faithfulness": round(context_score, 1),
                "completeness": round(length_score, 1),
                "clarity": round(specificity_score, 1),
                "accuracy": round((context_score + specificity_score) / 2, 1),
                "overall_quality": round(overall_score, 1),
                "explanation": "Heuristic-based assessment",
                "evaluation_method": "heuristic"
            }
            
        except Exception as e:
            self.logger.error(f"Error in fallback assessment: {e}")
            return {
                "faithfulness": 50, "completeness": 50, "clarity": 50, 
                "accuracy": 50, "overall_quality": 50, 
                "explanation": "Error in assessment", "evaluation_method": "error"
            }
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response when JSON parsing fails"""
        scores = {}
        
        # Extract numeric scores using regex
        patterns = {
            'faithfulness': r'faithfulness[:\s]*(\d+)',
            'completeness': r'completeness[:\s]*(\d+)',
            'clarity': r'clarity[:\s]*(\d+)',
            'accuracy': r'accuracy[:\s]*(\d+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text, re.IGNORECASE)
            scores[key] = int(match.group(1)) if match else 50
        
        overall_score = np.mean(list(scores.values()))
        
        return {
            **scores,
            "overall_quality": round(overall_score, 1),
            "explanation": "Parsed from AI response",
            "evaluation_method": "ai_parsed"
        }
    
    def calculate_confidence_score(self, 
                                 retrieval_metrics: Dict[str, Any],
                                 answer_relevance: Dict[str, Any],
                                 quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall confidence score based on all metrics
        """
        try:
            # Weight different components
            weights = {
                'retrieval_quality': 0.3,  # How good is the retrieval?
                'answer_relevance': 0.3,   # How relevant is the answer?
                'answer_quality': 0.4      # How good is the answer quality?
            }
            
            # Normalize scores to 0-1 range
            retrieval_score = min(
                (retrieval_metrics.get('precision_at_k', 0) + 
                 retrieval_metrics.get('mean_similarity', 0)) / 2, 1.0
            )
            
            relevance_score = answer_relevance.get('relevance_score', 0)
            quality_score = quality_assessment.get('overall_quality', 50) / 100.0
            
            # Calculate weighted confidence
            confidence_score = (
                retrieval_score * weights['retrieval_quality'] +
                relevance_score * weights['answer_relevance'] + 
                quality_score * weights['answer_quality']
            )
            
            # Determine confidence level
            if confidence_score >= self.HIGH_CONFIDENCE_THRESHOLD:
                confidence_level = "High"
                confidence_color = "green"
            elif confidence_score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
                confidence_level = "Medium"
                confidence_color = "orange"
            else:
                confidence_level = "Low"
                confidence_color = "red"
            
            return {
                "confidence_score": round(confidence_score, 3),
                "confidence_level": confidence_level,
                "confidence_color": confidence_color,
                "component_scores": {
                    "retrieval_quality": round(retrieval_score, 3),
                    "answer_relevance": round(relevance_score, 3),
                    "answer_quality": round(quality_score, 3)
                },
                "weights_used": weights
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {e}")
            return {
                "confidence_score": 0.5,
                "confidence_level": "Medium",
                "confidence_color": "orange",
                "error": str(e)
            }
    
    def evaluate_query_response(self, 
                              query: str,
                              answer: str, 
                              retrieved_chunks: List[Dict[str, Any]],
                              processing_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Main evaluation function that calculates all metrics for a query-response pair
        """
        try:
            start_time = datetime.now()
            
            # Calculate all metrics
            retrieval_metrics = self.calculate_retrieval_metrics(query, retrieved_chunks)
            content_coverage = self.calculate_content_coverage(retrieved_chunks)
            answer_relevance = self.calculate_answer_relevance(query, answer)
            quality_assessment = self.assess_answer_quality(query, answer, retrieved_chunks)
            confidence_metrics = self.calculate_confidence_score(
                retrieval_metrics, answer_relevance, quality_assessment
            )
            
            evaluation_time = (datetime.now() - start_time).total_seconds()
            
            # Compile comprehensive evaluation results
            evaluation_results = {
                "query": query,
                "evaluation_timestamp": datetime.now().isoformat(),
                "evaluation_time_seconds": round(evaluation_time, 3),
                "overall_accuracy": {
                    "score": confidence_metrics.get('confidence_score', 0.5),
                    "level": confidence_metrics.get('confidence_level', 'Medium'),
                    "color": confidence_metrics.get('confidence_color', 'orange')
                },
                "retrieval_performance": retrieval_metrics,
                "content_analysis": content_coverage,
                "answer_quality": {
                    "relevance": answer_relevance,
                    "quality_metrics": quality_assessment
                },
                "confidence_breakdown": confidence_metrics,
                "summary": {
                    "retrieved_chunks": len(retrieved_chunks),
                    "relevant_chunks": retrieval_metrics.get('relevant_chunks', 0),
                    "content_types_used": content_coverage.get('unique_content_types', 0),
                    "processing_time": processing_time
                }
            }
            
            self.logger.info(f"Evaluation completed for query: {query[:50]}... "
                           f"Overall accuracy: {confidence_metrics.get('confidence_score', 0):.2f}")
            
            return evaluation_results
            
        except Exception as e:
            self.logger.error(f"Error in complete evaluation: {e}")
            return {
                "query": query,
                "evaluation_timestamp": datetime.now().isoformat(),
                "error": str(e),
                "overall_accuracy": {"score": 0.5, "level": "Error", "color": "red"}
            } 