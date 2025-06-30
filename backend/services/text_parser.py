from bs4 import BeautifulSoup, Tag
import re
import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextParser:
    """Service for parsing website content and converting to markdown, with OpenAPI detection"""
    
    def __init__(self):
        """Initialize the text parser"""
        self.logger = logger
    
    def parse_html_to_markdown(self, html_content: str) -> Dict:
        """
        Parse HTML content and convert to markdown format, with OpenAPI detection
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Dictionary containing:
            - markdown_content: The generated markdown content
            - openapi_spec: Extracted OpenAPI specification (if found)
            - metadata: Information about the parsing
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect and extract OpenAPI specification
            openapi_spec = self._extract_openapi_specification(soup, html_content)
            
            # Remove script, style, and other non-content elements for markdown processing
            content_soup = BeautifulSoup(html_content, 'html.parser')
            for element in content_soup(['script', 'style', 'nav', 'footer', 'meta', 'link']):
                element.decompose()
            
            # Convert HTML to markdown
            markdown_content = self._html_to_markdown(content_soup)
            
            result = {
                "markdown_content": markdown_content,
                "openapi_spec": openapi_spec,
                "metadata": {
                    "has_content": len(markdown_content.strip()) > 0,
                    "has_openapi": openapi_spec is not None,
                    "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML content: {e}")
            raise
    
    def _extract_openapi_specification(self, soup: BeautifulSoup, html_content: str) -> Optional[Dict]:
        """
        Dynamically detect and extract OpenAPI specification from HTML content
        
        Args:
            soup: BeautifulSoup object of the HTML
            html_content: Raw HTML content
            
        Returns:
            OpenAPI specification as dictionary if found, None otherwise
        """
        try:
            # Check for Swagger UI indicators
            swagger_indicators = self._detect_swagger_ui_presence(soup, html_content)
            
            if not swagger_indicators:
                self.logger.info("No Swagger UI indicators found")
                return None
            
            self.logger.info(f"Swagger UI indicators detected: {swagger_indicators}")
            
            # Extract OpenAPI spec from JavaScript
            openapi_spec = self._extract_openapi_from_javascript(soup, html_content)
            
            if openapi_spec:
                self.logger.info("Successfully extracted OpenAPI specification")
                return openapi_spec
            
            # Try alternative extraction methods
            openapi_spec = self._extract_openapi_from_data_attributes(soup)
            
            if openapi_spec:
                self.logger.info("Successfully extracted OpenAPI specification from data attributes")
                return openapi_spec
            
            self.logger.info("OpenAPI specification detected but could not be extracted")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting OpenAPI specification: {e}")
            return None
    
    def _detect_swagger_ui_presence(self, soup: BeautifulSoup, html_content: str) -> List[str]:
        """
        Dynamically detect presence of Swagger UI components
        
        Returns:
            List of detected indicators
        """
        indicators = []
        
        # Check for Swagger UI script references
        swagger_scripts = [
            'swagger-ui-bundle',
            'swagger-ui-dist',
            'swagger-ui.js',
            'SwaggerUIBundle',
            'swagger-ui-standalone'
        ]
        
        for script_name in swagger_scripts:
            if script_name in html_content:
                indicators.append(f"script:{script_name}")
        
        # Check for CSS references
        if 'swagger-ui.css' in html_content or 'swagger-ui-dist' in html_content:
            indicators.append("css:swagger-ui")
        
        # Check for DOM elements that might contain Swagger UI
        swagger_containers = soup.find_all(id=re.compile(r'swagger', re.I))
        if swagger_containers:
            indicators.append("dom:swagger-container")
        
        # Check for JavaScript patterns that suggest OpenAPI/Swagger
        js_patterns = [
            r'openapi\s*[:\=]\s*["\']3\.',  # OpenAPI version 3.x
            r'swagger\s*[:\=]\s*["\']2\.',  # Swagger version 2.x
            r'SwaggerUIBundle\s*\(',        # SwaggerUIBundle initialization
            r'openApiSpec\s*[:\=]',         # OpenAPI spec variable
            r'apiSpec\s*[:\=]',             # API spec variable
        ]
        
        for pattern in js_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                indicators.append(f"pattern:{pattern}")
        
        return indicators
    
    def _extract_openapi_from_javascript(self, soup: BeautifulSoup, html_content: str) -> Optional[Dict]:
        """
        Extract OpenAPI specification from JavaScript code
        """
        # First try a simpler regex-based approach for common patterns
        simple_spec = self._extract_openapi_simple_regex(html_content)
        if simple_spec:
            return simple_spec
        
        # Find all script tags
        script_tags = soup.find_all('script', string=True)
        
        for script in script_tags:
            script_content = script.string
            if not script_content:
                continue
            
            # Try simple regex first
            simple_spec = self._extract_openapi_simple_regex(script_content)
            if simple_spec:
                return simple_spec
            
            # Try complex extraction as fallback
            openapi_spec = self._parse_openapi_from_js_content(script_content)
            if openapi_spec:
                return openapi_spec
        
        # If not found in script tags, search in the entire HTML content
        return self._parse_openapi_from_js_content(html_content)
    
    def _parse_openapi_from_js_content(self, js_content: str) -> Optional[Dict]:
        """
        Parse OpenAPI specification from JavaScript content using improved extraction
        """
        # First, try to find OpenAPI spec using balanced brace matching
        openapi_spec = self._extract_with_balanced_braces(js_content)
        if openapi_spec:
            return openapi_spec
        
        # Fallback to regex patterns for simpler cases
        patterns = [
            # const openApiSpec = { ... };
            r'(?:const|let|var)\s+(\w*[Oo]pen[Aa]pi\w*|\w*[Ss]pec\w*|\w*[Aa]pi\w*)\s*=\s*({.*?});',
            # openApiSpec: { ... }
            r'(\w*[Oo]pen[Aa]pi\w*|\w*[Ss]pec\w*|\w*[Aa]pi\w*):\s*({.*?})\s*[,}]',
            # spec: { ... } in SwaggerUIBundle
            r'spec:\s*({.*?})\s*,',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, js_content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                try:
                    # Get the JSON object part
                    if len(match.groups()) == 2:
                        json_str = match.group(2)
                    else:
                        json_str = match.group(1)
                    
                    # Clean up the JSON string
                    json_str = self._clean_js_object_string(json_str)
                    
                    # Try to parse as JSON
                    spec_obj = json.loads(json_str)
                    
                    # Validate if it's an OpenAPI specification
                    if self._is_valid_openapi_spec(spec_obj):
                        return spec_obj
                        
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.debug(f"Failed to parse potential OpenAPI spec: {e}")
                    continue
        
        return None
    
    def _extract_with_balanced_braces(self, js_content: str) -> Optional[Dict]:
        """
        Extract OpenAPI spec using balanced brace matching for complex nested objects
        """
        # Look for openApiSpec variable assignment
        spec_patterns = [
            r'(?:const|let|var)\s+openApiSpec\s*=\s*',
            r'openApiSpec\s*[:\=]\s*',
            r'spec:\s*'
        ]
        
        for pattern in spec_patterns:
            match = re.search(pattern, js_content, re.IGNORECASE)
            if match:
                start_pos = match.end()
                
                # Find the opening brace
                while start_pos < len(js_content) and js_content[start_pos] != '{':
                    start_pos += 1
                
                if start_pos >= len(js_content):
                    continue
                
                # Extract the complete object using balanced brace counting
                obj_str = self._extract_balanced_object(js_content, start_pos)
                if obj_str:
                    try:
                        # Try to convert JS object to valid JSON
                        json_str = self._js_to_json(obj_str)
                        spec_obj = json.loads(json_str)
                        
                        if self._is_valid_openapi_spec(spec_obj):
                            return spec_obj
                    except (json.JSONDecodeError, ValueError) as e:
                        self.logger.debug(f"Failed to parse extracted object: {e}")
                        # Try ultra-aggressive cleanup as fallback
                        try:
                            ultra_cleaned = self._ultra_aggressive_cleanup(obj_str)
                            spec_obj = json.loads(ultra_cleaned)
                            
                            if self._is_valid_openapi_spec(spec_obj):
                                self.logger.info("Successfully parsed OpenAPI spec with ultra-aggressive cleanup")
                                return spec_obj
                        except (json.JSONDecodeError, ValueError) as e2:
                            self.logger.debug(f"Ultra-aggressive cleanup also failed: {e2}")
                        continue
        
        return None
    
    def _extract_openapi_simple_regex(self, content: str) -> Optional[Dict]:
        """
        Extract OpenAPI specification using simpler regex patterns for known structures
        """
        try:
            # Look for OpenAPI specification with common patterns (unquoted property names)
            # Pattern 1: openapi: "3.0.0" followed by info section
            openapi_pattern = r'openapi:\s*"3\.0\.0".*?info:\s*\{.*?title:\s*"([^"]*)"'
            match = re.search(openapi_pattern, content, re.DOTALL)
            
            if match:
                self.logger.info(f"Found OpenAPI 3.0.0 spec with title: {match.group(1)}")
                
                # Try to construct a basic OpenAPI spec from the content
                basic_spec = self._construct_basic_openapi_spec(content)
                if basic_spec:
                    return basic_spec
            
            # Pattern 2: Look for swagger: "2.0" 
            swagger_pattern = r'swagger:\s*"2\.0".*?info:\s*\{.*?title:\s*"([^"]*)"'
            match = re.search(swagger_pattern, content, re.DOTALL)
            
            if match:
                self.logger.info(f"Found Swagger 2.0 spec with title: {match.group(1)}")
                
                # Try to construct a basic Swagger spec from the content
                basic_spec = self._construct_basic_swagger_spec(content)
                if basic_spec:
                    return basic_spec
            
        except Exception as e:
            self.logger.debug(f"Simple regex extraction failed: {e}")
        
        return None
    
    def _construct_basic_openapi_spec(self, content: str) -> Optional[Dict]:
        """
        Construct a basic OpenAPI specification from content using regex extraction
        """
        try:
            spec = {"openapi": "3.0.0"}
            
            # Extract info section (handling unquoted property names)
            info_match = re.search(r'info:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', content, re.DOTALL)
            if info_match:
                info_content = info_match.group(1)
                info = {}
                
                # Extract title
                title_match = re.search(r'title:\s*"([^"]*)"', info_content)
                if title_match:
                    info["title"] = title_match.group(1)
                
                # Extract version
                version_match = re.search(r'version:\s*"([^"]*)"', info_content)
                if version_match:
                    info["version"] = version_match.group(1)
                
                # Extract description
                desc_match = re.search(r'description:\s*"([^"]*)"', info_content)
                if desc_match:
                    info["description"] = desc_match.group(1)
                
                if info:
                    spec["info"] = info
            
            # Extract servers (handling unquoted property names)
            servers_match = re.search(r'servers:\s*\[([^\]]+)\]', content, re.DOTALL)
            if servers_match:
                servers_content = servers_match.group(1)
                servers = []
                
                # Find individual server objects
                server_matches = re.finditer(r'\{([^}]+)\}', servers_content)
                for server_match in server_matches:
                    server_content = server_match.group(1)
                    server = {}
                    
                    url_match = re.search(r'url:\s*"([^"]*)"', server_content)
                    if url_match:
                        server["url"] = url_match.group(1)
                    
                    desc_match = re.search(r'description:\s*"([^"]*)"', server_content)
                    if desc_match:
                        server["description"] = desc_match.group(1)
                    
                    if server:
                        servers.append(server)
                
                if servers:
                    spec["servers"] = servers
            
            # Extract paths (simplified, just check if they exist)
            paths_match = re.search(r'paths:\s*\{', content)
            if paths_match:
                # For now, just mark that paths exist
                spec["paths"] = {}
                self.logger.info("Found paths section in OpenAPI spec")
            
            # Validate we have minimum required fields
            if "info" in spec and spec["info"].get("title"):
                self.logger.info(f"Successfully constructed basic OpenAPI spec: {spec['info']['title']}")
                return spec
            
        except Exception as e:
            self.logger.debug(f"Failed to construct basic OpenAPI spec: {e}")
        
        return None
    
    def _construct_basic_swagger_spec(self, content: str) -> Optional[Dict]:
        """
        Construct a basic Swagger 2.0 specification from content using regex extraction
        """
        try:
            spec = {"swagger": "2.0"}
            
            # Extract info section (handling unquoted property names)
            info_match = re.search(r'info:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', content, re.DOTALL)
            if info_match:
                info_content = info_match.group(1)
                info = {}
                
                title_match = re.search(r'title:\s*"([^"]*)"', info_content)
                if title_match:
                    info["title"] = title_match.group(1)
                
                version_match = re.search(r'version:\s*"([^"]*)"', info_content)
                if version_match:
                    info["version"] = version_match.group(1)
                
                if info:
                    spec["info"] = info
            
            # Validate we have minimum required fields
            if "info" in spec and spec["info"].get("title"):
                self.logger.info(f"Successfully constructed basic Swagger spec: {spec['info']['title']}")
                return spec
            
        except Exception as e:
            self.logger.debug(f"Failed to construct basic Swagger spec: {e}")
        
        return None
    
    def _extract_balanced_object(self, content: str, start_pos: int) -> Optional[str]:
        """
        Extract a balanced JavaScript object starting from the given position
        """
        if start_pos >= len(content) or content[start_pos] != '{':
            return None
        
        brace_count = 0
        current_pos = start_pos
        in_string = False
        escape_next = False
        string_char = None
        
        while current_pos < len(content):
            char = content[current_pos]
            
            if escape_next:
                escape_next = False
                current_pos += 1
                continue
            
            if char == '\\':
                escape_next = True
                current_pos += 1
                continue
            
            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found the closing brace
                        return content[start_pos:current_pos + 1]
            else:
                if char == string_char:
                    in_string = False
                    string_char = None
            
            current_pos += 1
        
        return None
    
    def _js_to_json(self, js_obj_str: str) -> str:
        """
        Convert JavaScript object notation to valid JSON
        """
        # Remove comments
        js_obj_str = re.sub(r'//.*?$', '', js_obj_str, flags=re.MULTILINE)
        js_obj_str = re.sub(r'/\*.*?\*/', '', js_obj_str, flags=re.DOTALL)
        
        # Convert single quotes to double quotes first
        js_obj_str = self._fix_quotes(js_obj_str)
        
        # Fix unquoted property names - more comprehensive approach
        # This regex looks for unquoted property names that are not already in quotes
        # It handles cases like: property: value, { property: value, , property: value
        js_obj_str = re.sub(r'([{\s,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'\1"\2":', js_obj_str)
        
        # Also handle the case where the property is at the start of the object
        js_obj_str = re.sub(r'^(\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'\1"\2":', js_obj_str, flags=re.MULTILINE)
        
        # Remove trailing commas
        js_obj_str = re.sub(r',(\s*[}\]])', r'\1', js_obj_str)
        
        return js_obj_str
    
    def _fix_quotes(self, text: str) -> str:
        """
        Convert single quotes to double quotes while preserving quoted content
        """
        result = []
        i = 0
        in_double_quotes = False
        in_single_quotes = False
        
        while i < len(text):
            char = text[i]
            
            # Handle escape sequences first
            if char == '\\':
                result.append(char)
                i += 1
                if i < len(text):
                    result.append(text[i])
                i += 1
                continue
            
            if char == '"' and not in_single_quotes:
                in_double_quotes = not in_double_quotes
                result.append(char)
            elif char == "'" and not in_double_quotes:
                # Convert single quotes to double quotes
                result.append('"')
                in_single_quotes = not in_single_quotes
            else:
                result.append(char)
            
            i += 1
        
        return ''.join(result)
    
    def _ultra_aggressive_cleanup(self, js_str: str) -> str:
        """
        Ultra-aggressive cleanup for problematic JavaScript objects
        """
        # Remove comments
        js_str = re.sub(r'//.*?$', '', js_str, flags=re.MULTILINE)
        js_str = re.sub(r'/\*.*?\*/', '', js_str, flags=re.DOTALL)
        
        # Remove all control characters except standard whitespace
        cleaned_chars = []
        for char in js_str:
            if ord(char) >= 32 or char in ['\n', '\r', '\t', ' ']:
                cleaned_chars.append(char)
        js_str = ''.join(cleaned_chars)
        
        # Convert single quotes to double quotes
        js_str = js_str.replace("'", '"')
        
        # Fix unquoted property names with multiple passes
        for _ in range(3):  # Multiple passes for nested structures
            # Handle property names after braces, commas, or start of line
            js_str = re.sub(r'([{\[\s,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'\1"\2":', js_str)
            js_str = re.sub(r'^(\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'\1"\2":', js_str, flags=re.MULTILINE)
        
        # Remove trailing commas
        js_str = re.sub(r',(\s*[}\]])', r'\1', js_str)
        
        # Fix common JSON formatting issues
        js_str = re.sub(r'\s*:\s*', ': ', js_str)  # Normalize colons
        js_str = re.sub(r'\s*,\s*', ', ', js_str)  # Normalize commas
        
        # Clean up excessive whitespace
        js_str = re.sub(r'\n\s*\n', '\n', js_str)  # Remove empty lines
        js_str = re.sub(r'\s+', ' ', js_str)       # Normalize spaces
        
        return js_str.strip()
    
    def _clean_js_object_string(self, js_obj_str: str) -> str:
        """
        Clean JavaScript object string to make it valid JSON
        """
        # Remove trailing semicolons and commas
        js_obj_str = re.sub(r'[;,]\s*$', '', js_obj_str.strip())
        
        # Fix unquoted property names (basic cases)
        js_obj_str = re.sub(r'(\w+):\s*', r'"\1": ', js_obj_str)
        
        # Fix single quotes to double quotes
        js_obj_str = re.sub(r"'([^']*)'", r'"\1"', js_obj_str)
        
        # Handle trailing commas in arrays and objects
        js_obj_str = re.sub(r',(\s*[}\]])', r'\1', js_obj_str)
        
        return js_obj_str
    
    def _is_valid_openapi_spec(self, spec_obj: Dict) -> bool:
        """
        Validate if the object is a valid OpenAPI specification
        """
        if not isinstance(spec_obj, dict):
            return False
        
        # Check for required OpenAPI fields
        required_fields = ['openapi', 'info']
        if not all(field in spec_obj for field in required_fields):
            # Check for Swagger 2.0
            if 'swagger' in spec_obj and 'info' in spec_obj:
                return True
            return False
        
        # Check OpenAPI version
        openapi_version = spec_obj.get('openapi', '')
        if isinstance(openapi_version, str) and openapi_version.startswith(('2.', '3.')):
            return True
        
        # Check Swagger version
        swagger_version = spec_obj.get('swagger', '')
        if isinstance(swagger_version, str) and swagger_version.startswith('2.'):
            return True
        
        return False
    
    def _extract_openapi_from_data_attributes(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract OpenAPI spec from data attributes or other HTML elements
        """
        # Look for data attributes that might contain the spec
        elements_with_data = soup.find_all(attrs={"data-spec": True})
        for element in elements_with_data:
            try:
                spec_data = element.get('data-spec')
                spec_obj = json.loads(spec_data)
                if self._is_valid_openapi_spec(spec_obj):
                    return spec_obj
            except (json.JSONDecodeError, TypeError):
                continue
        
        return None
    
    def _html_to_markdown(self, soup: BeautifulSoup) -> str:
        """Convert HTML content to markdown format"""
        markdown_lines = []
        
        # Process all elements in order
        for element in soup.find('body').descendants if soup.find('body') else soup.descendants:
            if not isinstance(element, Tag):
                continue
            
            # Handle images first (before text check)
            if element.name == 'img':
                print("img element: ", element)
                src = element.get('src', '')
                alt = element.get('alt', '')
                if src:
                    # Adjust image path for markdown location
                    adjusted_src = self._adjust_image_path(src)
                    markdown_lines.append(f"![{alt}]({adjusted_src})\n")
                continue  # Skip to next element
            
            # Skip if element is empty (for text elements)
            text = element.get_text(strip=True)
            if not text:
                continue
            
            # Handle different HTML elements
            if element.name == 'h1':
                markdown_lines.append(f"# {text}\n")
            elif element.name == 'h2':
                markdown_lines.append(f"## {text}\n")
            elif element.name == 'h3':
                markdown_lines.append(f"### {text}\n")
            elif element.name == 'h4':
                markdown_lines.append(f"#### {text}\n")
            elif element.name == 'h5':
                markdown_lines.append(f"##### {text}\n")
            elif element.name == 'h6':
                markdown_lines.append(f"###### {text}\n")
            elif element.name == 'p':
                # Only add if it's a direct paragraph, not nested
                if not any(ancestor.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'] for ancestor in element.parents):
                    markdown_lines.append(f"{text}\n")
            elif element.name == 'ul':
                # Process list items
                for li in element.find_all('li', recursive=False):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        markdown_lines.append(f"- {li_text}")
                markdown_lines.append("")  # Empty line after list
            elif element.name == 'ol':
                # Process ordered list items
                for i, li in enumerate(element.find_all('li', recursive=False), 1):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        markdown_lines.append(f"{i}. {li_text}")
                markdown_lines.append("")  # Empty line after list
            elif element.name == 'strong' or element.name == 'b':
                # Bold text - only if it's not already processed by parent
                if not any(ancestor.name in ['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'] for ancestor in element.parents):
                    markdown_lines.append(f"**{text}**\n")
        
        # Clean up the markdown content
        cleaned_markdown = self._clean_markdown(markdown_lines)
        return cleaned_markdown
    
    def _adjust_image_path(self, src: str) -> str:
        """
        Adjust image path to be relative to the markdown file location
        
        Args:
            src: Original image source path from HTML
            
        Returns:
            Adjusted path relative to markdown file location
        """
        # If it's an absolute URL (http/https), keep as is
        if src.startswith(('http://', 'https://')):
            return src
        
        # If it's already an absolute path, keep as is
        if os.path.isabs(src):
            return src
        
        # For relative paths, adjust based on markdown location
        # Since markdown is saved in 'docs/' by default, adjust relative to that
        # From docs/ folder, to access media/swim_lane.png, we need ../media/swim_lane.png
        
        # If the source starts with 'media/', adjust the path
        if src.startswith('media/'):
            adjusted_path = f"../{src}"
            self.logger.info(f"Adjusted image path: {src} -> {adjusted_path}")
            return adjusted_path
        
        # For other relative paths, add ../ to go up one level from docs/
        if not src.startswith('../'):
            adjusted_path = f"../{src}"
            self.logger.info(f"Adjusted image path: {src} -> {adjusted_path}")
            return adjusted_path
        
        return src
    
    def _clean_markdown(self, markdown_lines: List[str]) -> str:
        """Clean up markdown content by removing duplicates and formatting"""
        if not markdown_lines:
            return ""
        
        cleaned_lines = []
        seen_content = set()
        
        for line in markdown_lines:
            # Skip empty lines and whitespace
            if not line.strip():
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue
            
            # Normalize content for duplicate detection
            normalized = re.sub(r'\s+', ' ', line.strip().lower())
            
            # Skip duplicate content
            if normalized in seen_content:
                continue
            
            seen_content.add(normalized)
            cleaned_lines.append(line.strip())
        
        # Join lines and clean up extra whitespace
        markdown_content = '\n'.join(cleaned_lines)
        
        # Remove excessive blank lines
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        return markdown_content.strip()
    
    def save_markdown_file(self, markdown_content: str, output_dir: str = "docs") -> str:
        """
        Save markdown content to a file
        
        Args:
            markdown_content: The markdown content to save
            output_dir: Directory to save the file in
            
        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"website_content_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Save content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        self.logger.info(f"Saved markdown file: {filepath}")
        self.logger.info(f"Image paths in markdown are relative to: {os.path.abspath(output_dir)}")
        return filepath
    
    def save_openapi_file(self, openapi_spec: Dict, output_dir: str = "docs") -> str:
        """
        Save OpenAPI specification to a JSON file
        
        Args:
            openapi_spec: The OpenAPI specification dictionary
            output_dir: Directory to save the file in
            
        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"openapi_spec_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save content
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved OpenAPI specification: {filepath}")
        return filepath 