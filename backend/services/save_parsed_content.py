from bs4 import BeautifulSoup
import os
import logging
from datetime import datetime
import json
from .text_parser import TextParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_parsed_content(html_content: str) -> str:
    """
    Parse HTML content and save header-based chunks in markdown format.
    
    Args:
        html_content: Raw HTML string
    
    Returns:
        Path to the saved markdown file
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'parsed_content')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Parse content using TextParser
        parser = TextParser()
        result = parser.parse_html_content(html_content)
        
        # Prepare markdown content
        md_content = []
        
        # Add header for the file
        md_content.extend([
            "# Parsed Content\n",
            "This file contains the parsed content organized by headers.\n",
            "Each section represents a chunk that will be used for embeddings.\n\n",
            "---\n\n"
        ])
        
        # Add chunks
        for i, chunk in enumerate(result["chunks"], 1):
            # Add header with level indicator
            header_prefix = '#' * (chunk['header_level'] + 1) if chunk['header_level'] > 0 else '#'
            md_content.extend([
                f"{header_prefix} {chunk['header']}\n",
                f"*Chunk {i} - Level {chunk['header_level']} - Type: {chunk['source_type']}*\n\n",
                chunk['content'],
                "\n---\n\n"
            ])
        
        # Add metadata section
        md_content.extend([
            "# Metadata\n",
            "```json",
            json.dumps(result["metadata"], indent=2),
            "```\n"
        ])
        
        # Save to markdown file
        md_filename = f'parsed_content_{timestamp}.md'
        md_path = os.path.join(output_dir, md_filename)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        logger.info(f"Content saved successfully to markdown file: {md_path}")
        
        return md_path
        
    except Exception as e:
        logger.error(f"Error saving parsed content: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    with open('../test_content.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    output_path = save_parsed_content(html_content)
    print(f"\nContent saved to: {output_path}") 