import hashlib
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ChunkingService:
    """Service for intelligent text chunking"""
    
    def __init__(self, 
        chunk_size: int = 500, 
        overlap_size: int = 50,
        min_chunk_size: int = 100):
        """
        Initialize chunking service
        
        Args:
            chunk_size: Target size for each chunk (in characters)
            overlap_size: Overlap between chunks to maintain context
            min_chunk_size: Minimum chunk size to avoid tiny fragments
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        self.logger = logger
    
    def chunk_text(self, text: str, source: str, chunk_type: str = "general") -> List[Dict[str, Any]]:
        """
        Chunk text intelligently based on content type
        
        Args:
            text: Text content to chunk
            source: Source identifier for the text
            chunk_type: Type of content (general, api, process, etc.)
        
        Returns:
            List of chunk dictionaries
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            return []
        
        try:
            # Determine chunking strategy based on source name and content type
            detected_type = self._detect_content_type(text, source, chunk_type)
            
            if detected_type == "openapi":
                chunks = self._chunk_openapi_specification(text, source)
            elif detected_type == "process":
                chunks = self._chunk_process_documentation(text, source)
            else:
                chunks = self._chunk_general_text(text, source)
            
            self.logger.info(f"Created {len(chunks)} chunks from {source} (type: {detected_type})")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error chunking text from {source}: {e}")
            return []
    
    def _detect_content_type(self, text: str, source: str, chunk_type: str) -> str:
        """Detect content type from source name, explicit type, and content analysis"""
        
        # 1. Use explicit chunk_type if provided and not general
        if chunk_type and chunk_type != "general":
            return chunk_type
        
        # 2. Detect from source name patterns
        source_lower = source.lower()
        if "openapi" in source_lower or "swagger" in source_lower:
            return "openapi"
        
        # 3. Analyze content patterns for process documentation
        if any(keyword in text.lower() for keyword in ["process", "workflow", "step"]):
            # Further validate with numbered steps or process patterns
            if (re.search(r'^\s*\d+\.\s+', text, re.MULTILINE) or 
                re.search(r'^\s*Step\s+\d+', text, re.MULTILINE) or
                text.lower().count("step") >= 2):
                return "process"
        
        return "general"
    
    def _chunk_general_text(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Chunk general text content with header-aware strategy - NO SIZE LIMITS"""
        chunks = []
        
        # Use header-aware sectioning that keeps headers with their content
        sections = self._split_by_header_sections(text)
        
        chunk_index = 0
        for section in sections:
            section_content = section.strip()
            
            # Debug: Log section info
            self.logger.debug(f"Section {chunk_index}: {len(section_content)} chars, min_size: {self.min_chunk_size}")
            self.logger.debug(f"Section preview: '{section_content[:100]}...'")
            
            # Lower the minimum chunk size for header-based sections to ensure we don't lose content
            min_size_for_headers = min(self.min_chunk_size, 50)  # Allow smaller chunks for headers
            
            if len(section_content) < min_size_for_headers:
                self.logger.debug(f"Skipping section {chunk_index} - too small ({len(section_content)} < {min_size_for_headers})")
                continue
                
            # Keep entire sections together - NO SIZE SPLITTING for text content
            # Headers and their content should stay together for semantic search
            chunk = self._create_chunk(
                content=section_content,
                source=source,
                chunk_index=chunk_index,
                chunk_type="general"
            )
            chunks.append(chunk)
            self.logger.debug(f"Created chunk {chunk['chunk_id']} with {len(section_content)} chars")
            chunk_index += 1
        
        return chunks
    
    def _split_by_header_sections(self, text: str) -> List[str]:
        """
        Split text by headers while keeping headers WITH their content
        This ensures 'Inventory Management' stays with its description
        """
        lines = text.split('\n')
        sections = []
        current_section = []
        
        # Debug: Print all lines to see what we're working with
        self.logger.debug(f"Processing {len(lines)} lines for header-based splitting")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line is a header
            is_header = self._is_header_line(line, i, lines)
            
            if is_header:
                self.logger.debug(f"Found header at line {i}: '{line}'")
                
                # If we have content in current section, save it
                if current_section:
                    section_content = '\n'.join(current_section).strip()
                    sections.append(section_content)
                    self.logger.debug(f"Saved section with {len(section_content)} chars")
                    current_section = []
                
                # Start new section with this header
                current_section = [lines[i]]
                
                # Collect all content that belongs to this header
                i += 1
                while i < len(lines):
                    if i >= len(lines):
                        break
                        
                    next_line = lines[i].strip()
                    
                    # Stop if we hit another header
                    if self._is_header_line(next_line, i, lines):
                        break
                    
                    current_section.append(lines[i])
                    i += 1
                continue
            else:
                # Not a header, add to current section
                current_section.append(lines[i])
                i += 1
        
        # Add the last section
        if current_section:
            section_content = '\n'.join(current_section).strip()
            sections.append(section_content)
            self.logger.debug(f"Saved final section with {len(section_content)} chars")
        
        self.logger.info(f"Split into {len(sections)} header-based sections")
        return [s for s in sections if s.strip()]
    
    def _is_header_line(self, line: str, line_index: int, all_lines: List[str]) -> bool:
        """
        Detect if a line is a header based on markdown and content patterns
        """
        if not line.strip():
            return False
        
        line_stripped = line.strip()
        
        # Primary check: Markdown headers (# ## ### etc.)
        if re.match(r'^#{1,6}\s+', line_stripped):
            return True
        
        # Secondary check: Look ahead to see if next line has content
        has_content_after = False
        if line_index + 1 < len(all_lines):
            next_line = all_lines[line_index + 1].strip()
            if next_line and not self._looks_like_header(next_line):
                has_content_after = True
        
        # For non-markdown headers, use more flexible patterns
        header_patterns = [
            # Business/documentation terms that indicate sections
            r'^.*(Overview|Management|Processing|Policy|Information|Details|System|Tracking|Verification|Validation|Fulfillment|Cancellation).*$',
            
            # Title case patterns (but more flexible)
            r'^[A-Z][a-zA-Z\s]*[A-Z][a-zA-Z\s]*$',
            
            # Short lines that end sentences (likely headers)
            r'^[A-Z][a-zA-Z\s]{8,50}$',
        ]
        
        # Must be reasonable length for a header
        if len(line_stripped) > 100 or len(line_stripped) < 3:
            return False
        
        # Check if it matches header patterns AND has content after
        is_header_pattern = any(re.match(pattern, line_stripped, re.IGNORECASE) for pattern in header_patterns)
        
        return is_header_pattern and has_content_after
    
    def _looks_like_header(self, line: str) -> bool:
        """Quick check if line looks like a header (for lookahead)"""
        if len(line) > 80:
            return False
        
        quick_patterns = [
            r'^[A-Z][a-zA-Z\s]+$',
            r'^[A-Z][a-zA-Z\s]+:$',
        ]
        
        return any(re.match(pattern, line) for pattern in quick_patterns)
    
    def _split_large_section_intelligently(self, section: str) -> List[str]:
        """
        Split large sections while trying to maintain semantic coherence
        Priority: Keep headers with their immediate content
        """
        # If section has sub-headers, split by those
        lines = section.split('\n')
        
        # Look for sub-headers within the section
        subsections = []
        current_subsection = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for sub-headers (less strict than main headers)
            if (self._is_subheader_line(line_stripped) and 
                len(current_subsection) > 0):  # Don't split on the first line
                
                # Save current subsection
                if current_subsection:
                    subsections.append('\n'.join(current_subsection).strip())
                    current_subsection = []
            
            current_subsection.append(line)
        
        # Add the last subsection
        if current_subsection:
            subsections.append('\n'.join(current_subsection).strip())
        
        # If no subsections found, split by paragraphs as fallback
        if len(subsections) <= 1:
            paragraphs = re.split(r'\n\s*\n', section)
            return [p.strip() for p in paragraphs if len(p.strip()) >= self.min_chunk_size]
        
        return [s for s in subsections if len(s.strip()) >= self.min_chunk_size]
    
    def _is_subheader_line(self, line: str) -> bool:
        """Detect sub-headers within sections"""
        if not line or len(line) > 60:
            return False
        
        subheader_patterns = [
            r'^[A-Z][a-z]+\s+(and|&)\s+[A-Z][a-z]+$',  # "Payment and Processing"
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',             # "Order Validation"
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+$', # "Real Time Updates"
        ]
        
        return any(re.match(pattern, line) for pattern in subheader_patterns)
    
    def _chunk_openapi_specification(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Chunk OpenAPI specification content with improved strategy"""
        chunks = []
        chunk_index = 0
        
        # Strategy 1: Split by API endpoints (most important for search)
        endpoint_chunks = self._extract_endpoint_chunks(text)
        
        if endpoint_chunks:
            for endpoint_content in endpoint_chunks:
                if len(endpoint_content.strip()) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(
                        content=endpoint_content.strip(),
                        source=source,
                        chunk_index=chunk_index,
                        chunk_type="api_endpoint"
                    ))
                    chunk_index += 1
        
        # Strategy 2: Split by major OpenAPI sections
        section_chunks = self._extract_openapi_sections(text)
        
        for section_name, section_content in section_chunks.items():
            if len(section_content.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=section_content.strip(),
                    source=source,
                    chunk_index=chunk_index,
                    chunk_type=f"api_{section_name}"
                ))
                chunk_index += 1
        
        # If no structured chunks found, fall back to YAML-based splitting
        if not chunks:
            yaml_sections = self._split_by_yaml_sections(text)
            for section in yaml_sections:
                if len(section.strip()) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(
                        content=section.strip(),
                        source=source,
                        chunk_index=chunk_index,
                        chunk_type="api_section"
                    ))
                    chunk_index += 1
        
        return chunks
    
    def _extract_endpoint_chunks(self, text: str) -> List[str]:
        """Extract individual API endpoints as chunks"""
        endpoint_chunks = []
        
        # Pattern to match API paths and their complete definitions
        # Matches: /path: followed by all indented content until next path or end
        endpoint_pattern = r'(^\s*/[^:\n]+:.*?)(?=^\s*/[^:\n]+:|^\s*[a-zA-Z_][a-zA-Z0-9_]*:\s*$|$)'
        
        matches = re.finditer(endpoint_pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            endpoint_content = match.group(1).strip()
            
            # Validate this looks like a real endpoint
            if (re.search(r'(get|post|put|delete|patch):', endpoint_content, re.IGNORECASE) and
                len(endpoint_content) >= 50):  # Minimum content for meaningful endpoint
                endpoint_chunks.append(endpoint_content)
        
        return endpoint_chunks
    
    def _extract_openapi_sections(self, text: str) -> Dict[str, str]:
        """Extract major OpenAPI sections (info, paths, components, etc.)"""
        sections = {}
        
        # Major OpenAPI sections
        section_patterns = {
            'info': r'(^info:.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*:|$)',
            'servers': r'(^servers:.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*:|$)',
            'paths': r'(^paths:.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*:|$)',
            'components': r'(^components:.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*:|$)',
            'security': r'(^security:.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*:|$)',
            'tags': r'(^tags:.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*:|$)',
        }
        
        for section_name, pattern in section_patterns.items():
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                section_content = match.group(1).strip()
                if section_content and len(section_content) >= 30:
                    sections[section_name] = section_content
                    break  # Take first match only
        
        return sections
    
    def _chunk_process_documentation(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Chunk process and workflow documentation"""
        chunks = []
        chunk_index = 0
        
        # Split by numbered steps or bullet points
        step_pattern = r'(\d+\.\s+.*?)(?=\d+\.\s+|$)'
        steps = re.findall(step_pattern, text, re.DOTALL)
        
        if steps:
            for step in steps:
                if len(step.strip()) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(
                        content=step.strip(),
                        source=source,
                        chunk_index=chunk_index,
                        chunk_type="process_step"
                    ))
                    chunk_index += 1
        else:
            # Split by bullet points or sections
            bullet_pattern = r'([•\-\*]\s+.*?)(?=[•\-\*]\s+|$)'
            bullets = re.findall(bullet_pattern, text, re.DOTALL)
            
            if bullets:
                for bullet in bullets:
                    if len(bullet.strip()) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            content=bullet.strip(),
                            source=source,
                            chunk_index=chunk_index,
                            chunk_type="process_item"
                        ))
                        chunk_index += 1
            else:
                # Fallback to general chunking
                return self._chunk_general_text(text, source)
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences with overlap"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_yaml_sections(self, text: str) -> List[str]:
        """Split YAML/API content by logical sections"""
        # Split by top-level keys in YAML
        section_pattern = r'(^[a-zA-Z_][a-zA-Z0-9_]*:.*?)(?=^[a-zA-Z_][a-zA-Z0-9_]*:|$)'
        sections = re.findall(section_pattern, text, re.MULTILINE | re.DOTALL)
        
        if not sections:
            # Fallback to line-based splitting
            lines = text.split('\n')
            sections = []
            current_section = []
            
            for line in lines:
                if line.strip() and not line.startswith(' ') and ':' in line:
                    if current_section:
                        sections.append('\n'.join(current_section))
                        current_section = []
                current_section.append(line)
            
            if current_section:
                sections.append('\n'.join(current_section))
        
        return [s.strip() for s in sections if s.strip()]
    
    def _create_chunk(self, content: str, source: str, chunk_index: int, chunk_type: str) -> Dict[str, Any]:
        """Create a chunk dictionary with metadata"""
        # Generate unique chunk ID
        chunk_id = self._generate_chunk_id(content, source, chunk_index)
        
        return {
            "chunk_id": chunk_id,
            "content": content,
            "source": source,
            "chunk_index": chunk_index,
            "chunk_type": chunk_type,
            "content_length": len(content),
            "word_count": len(content.split())
        }
    
    def _generate_chunk_id(self, content: str, source: str, chunk_index: int) -> str:
        """Generate a unique ID for a chunk"""
        # Create a hash based on content and metadata
        hash_input = f"{source}_{chunk_index}_{content[:100]}"
        chunk_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{source}_{chunk_index}_{chunk_hash}" 