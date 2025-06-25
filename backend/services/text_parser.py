from bs4 import BeautifulSoup, Tag
import re
import logging
from typing import Dict, List
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextParser:
    """Service for parsing website content and converting to markdown"""
    
    def __init__(self):
        """Initialize the text parser"""
        self.logger = logger
    
    def parse_html_to_markdown(self, html_content: str) -> Dict:
        """
        Parse HTML content and convert to markdown format
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Dictionary containing:
            - markdown_content: The generated markdown content
            - metadata: Information about the parsing
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script, style, and other non-content elements
            for element in soup(['script', 'style', 'nav', 'footer', 'meta', 'link']):
                element.decompose()
            
            # Convert HTML to markdown
            markdown_content = self._html_to_markdown(soup)
            
            result = {
                "markdown_content": markdown_content,
                "metadata": {
                    "has_content": len(markdown_content.strip()) > 0,
                    "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML content: {e}")
            raise
    
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