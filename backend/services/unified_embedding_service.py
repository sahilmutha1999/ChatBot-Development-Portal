import os
import re
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import base64
import requests
from PIL import Image
import google.generativeai as genai
import dotenv

dotenv.load_dotenv()

# Import existing services
from .embeddings import EmbeddingService
from .chunking import ChunkingService
from .text_parser import TextParser


logger = logging.getLogger(__name__)

class UnifiedEmbeddingService:
    """Unified service for processing text and images into embeddings for RAG pipeline"""
    
    def __init__(self):
        """Initialize the unified embedding service"""
        self.logger = logger
        self.text_embedding_service = EmbeddingService()
        self.chunking_service = ChunkingService()
        self.text_parser = TextParser()
        
        # Initialize Gemini for image processing
        self.gemini_model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini for image processing"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                self.logger.warning("GOOGLE_API_KEY not found. Image processing will be skipped.")
                return
            
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Gemini model initialized for image processing")
            
        except Exception as e:
            self.logger.error(f"Error initializing Gemini: {e}")
            self.gemini_model = None
    
    def process_html_content(self, html_content: str, source_name: str = "webpage") -> Dict[str, Any]:
        """
        Process HTML content and extract both text and images for embedding
        
        Args:
            html_content: HTML content to process
            source_name: Name of the source (for metadata)
            
        Returns:
            Dictionary containing processed embeddings and metadata
        """
        try:
            self.logger.info(f"Processing HTML content from: {source_name}")
            
            # Step 1: Parse HTML to markdown
            parsed_result = self.text_parser.parse_html_to_markdown(html_content)
            markdown_content = parsed_result["markdown_content"]
            
            # Step 1.5: Save markdown file for reference
            try:
                markdown_filepath = self.text_parser.save_markdown_file(markdown_content)
                self.logger.info(f"Saved markdown file: {markdown_filepath}")
            except Exception as e:
                self.logger.warning(f"Could not save markdown file: {e}")
                markdown_filepath = None
            
            # Step 2: Extract image references from markdown
            image_refs = self._extract_image_references(markdown_content)
            
            # Step 3: Process text chunks
            text_chunks = self._process_text_content(markdown_content, source_name)
            
            # Step 4: Process images if any
            image_chunks = []
            if image_refs and self.gemini_model:
                image_chunks = self._process_image_content(image_refs, source_name)
            elif image_refs and not self.gemini_model:
                self.logger.warning("Images found but Gemini not available. Skipping image processing.")
            
            # Combine results
            all_chunks = text_chunks + image_chunks
            
            result = {
                "total_chunks": len(all_chunks),
                "text_chunks": len(text_chunks),
                "image_chunks": len(image_chunks),
                "chunks": all_chunks,
                "source": source_name,
                "markdown_file": markdown_filepath,
                "markdown_content": markdown_content,
                "processed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Processed {source_name}: {len(text_chunks)} text chunks, {len(image_chunks)} image chunks")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing HTML content: {e}")
            raise
    
    def _extract_image_references(self, markdown_content: str) -> List[Dict[str, str]]:
        """Extract image references from markdown content"""
        image_refs = []
        
        # Pattern to match markdown images: ![alt](src)
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(image_pattern, markdown_content)
        
        for alt_text, src_path in matches:
            image_refs.append({
                "alt_text": alt_text,
                "src_path": src_path,
                "original_path": src_path
            })
        
        self.logger.info(f"Found {len(image_refs)} image references")
        return image_refs
    
    def _process_text_content(self, markdown_content: str, source_name: str) -> List[Dict[str, Any]]:
        """Process text content into embedded chunks"""
        try:
            # Remove image markdown syntax for text processing
            text_only = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', '', markdown_content)
            text_only = re.sub(r'\n\s*\n', '\n\n', text_only).strip()
            
            self.logger.debug(f"Text content for chunking: {text_only[:200]}...")
            
            # Temporarily enable debug logging for chunking
            original_level = self.chunking_service.logger.level
            self.chunking_service.logger.setLevel(logging.DEBUG)
            
            # Chunk the text
            text_chunks = self.chunking_service.chunk_text(text_only, source_name, "general")
            
            # Restore original logging level
            self.chunking_service.logger.setLevel(original_level)
            
            self.logger.info(f"Generated {len(text_chunks)} text chunks from content")
            # Generate embeddings for text chunks
            embedded_chunks = []
            for chunk in text_chunks:
                try:
                    embedding = self.text_embedding_service.embed_text(chunk["content"])
                    
                    embedded_chunk = {
                        "id": chunk["chunk_id"],  # Fixed: use chunk_id instead of id
                        "content": chunk["content"],
                        "embedding": embedding,
                        "metadata": {
                            "content_type": "text",
                            "source": source_name,
                            "chunk_type": chunk.get("chunk_type", "general"),
                            "chunk_index": chunk.get("chunk_index", 0),
                            "content_length": chunk.get("content_length", len(chunk["content"])),
                            "word_count": chunk.get("word_count", len(chunk["content"].split()))
                        }
                    }
                    embedded_chunks.append(embedded_chunk)
                    
                except Exception as e:
                    self.logger.error(f"Error embedding text chunk {chunk['chunk_id']}: {e}")
                    continue
            
            self.logger.info(f"Successfully embedded {len(embedded_chunks)} text chunks")
            return embedded_chunks
            
        except Exception as e:
            self.logger.error(f"Error processing text content: {e}")
            return []
    
    def _process_image_content(self, image_refs: List[Dict[str, str]], source_name: str) -> List[Dict[str, Any]]:
        """Process images using Gemini and create embedded chunks"""
        image_chunks = []
        
        for i, image_ref in enumerate(image_refs):
            try:
                # Resolve image path
                image_path = self._resolve_image_path(image_ref["src_path"])
                
                if not os.path.exists(image_path):
                    self.logger.warning(f"Image file not found: {image_path}")
                    continue
                
                # Process image with Gemini
                image_description = self._analyze_image_with_gemini(image_path, image_ref["alt_text"])
                
                if not image_description:
                    self.logger.warning(f"Failed to process image: {image_path}")
                    continue
                
                # Create comprehensive content for embedding
                image_content = self._create_image_content_for_embedding(image_ref, image_description)
                
                # Generate embedding for image content
                embedding = self.text_embedding_service.embed_text(image_content)
                
                # Create image chunk
                chunk_id = f"{source_name}_image_{i+1}"
                image_chunk = {
                    "id": chunk_id,
                    "content": image_content,
                    "embedding": embedding,
                    "metadata": {
                        "content_type": "image",
                        "source": source_name,
                        "image_path": image_path,
                        "alt_text": image_ref["alt_text"],
                        "original_src": image_ref["original_path"],
                        "gemini_description": image_description,
                        "processed_at": datetime.now().isoformat()
                    }
                }
                
                image_chunks.append(image_chunk)
                self.logger.info(f"Successfully processed image: {image_path}")
                
            except Exception as e:
                self.logger.error(f"Error processing image {image_ref['src_path']}: {e}")
                continue
        
        return image_chunks
    
    def _resolve_image_path(self, src_path: str) -> str:
        """Resolve image path relative to current working directory"""
        # Remove ../ if present and adjust for current working directory
        if src_path.startswith('../'):
            resolved_path = src_path[3:]  # Remove ../
        else:
            resolved_path = src_path
        
        # Make path relative to project root
        if not os.path.isabs(resolved_path):
            project_root = os.getcwd()
            resolved_path = os.path.join(project_root, resolved_path)
        
        return resolved_path
    
    def _analyze_image_with_gemini(self, image_path: str, alt_text: str = "") -> Optional[str]:
        """Analyze image using Google Gemini"""
        try:
            if not self.gemini_model:
                return None
            
            # Load and prepare image
            image = Image.open(image_path)
            
            # Create detailed prompt for business process diagrams
            prompt = f"""
            Analyze this image in detail. This appears to be a business process diagram or workflow.
            
            Context: {alt_text if alt_text else "Business process diagram"}
            
            Please provide a comprehensive analysis including:
            
            1. **Diagram Type**: What type of diagram is this (flowchart, swim lane, process flow, etc.)?
            
            2. **Process Overview**: What business process or workflow does this represent?
            
            3. **Key Components**: 
               - What are the main steps or stages?
               - What are the decision points?
               - What are the different roles/actors involved?
            
            4. **Process Flow**: Describe the sequence of activities from start to end.
            
            5. **Business Logic**: What business rules or conditions are represented?
            
            6. **Stakeholders**: Who are the different parties involved in this process?
            
            Please be detailed and specific, as this information will be used to answer user questions about the business process.
            """
            
            # Generate response
            response = self.gemini_model.generate_content([prompt, image])
            
            if response and response.text:
                return response.text.strip()
            else:
                self.logger.warning("Gemini returned empty response for image")
                return None
                
        except Exception as e:
            self.logger.error(f"Error analyzing image with Gemini: {e}")
            return None
    
    def _create_image_content_for_embedding(self, image_ref: Dict[str, str], description: str) -> str:
        """Create comprehensive content for image embedding"""
        alt_text = image_ref.get("alt_text", "")
        
        # Combine alt text and Gemini description for embedding
        content_parts = []
        
        if alt_text:
            content_parts.append(f"Image Description: {alt_text}")
        
        content_parts.append(f"Detailed Analysis: {description}")
        
        # Add context about it being an image/diagram
        content_parts.append("This is a visual diagram or image that shows business processes, workflows, or system architecture.")
        
        return "\n\n".join(content_parts)
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding service"""
        model_info = self.text_embedding_service.get_model_info()
        
        return {
            "text_embedding_model": model_info,
            "image_processing": "Gemini-1.5-Flash" if self.gemini_model else "Not available",
            "chunking_config": {
                "chunk_size": self.chunking_service.chunk_size,
                "overlap_size": self.chunking_service.overlap_size,
                "min_chunk_size": self.chunking_service.min_chunk_size
            }
        } 