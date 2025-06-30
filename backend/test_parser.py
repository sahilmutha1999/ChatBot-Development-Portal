#!/usr/bin/env python3
"""
Test script for the enhanced text parser with OpenAPI detection
"""

import os
import sys
import json
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.text_parser import TextParser

def test_parser():
    """Test the enhanced text parser with the test HTML content"""
    
    print("🔍 Enhanced Text Parser Test")
    print("=" * 50)
    
    # Initialize the parser
    parser = TextParser()
    
    # Read the test HTML content
    test_file = backend_dir / "test_content.html"
    
    if not test_file.exists():
        print(f"❌ Error: Test file not found at {test_file}")
        print("Make sure test_content.html exists in the backend directory")
        return False
    
    print(f"📄 Reading test content from: {test_file.name}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"📊 HTML content length: {len(html_content):,} characters")
    
    # Parse the content
    print(f"\n🔄 Parsing HTML content...")
    
    try:
        result = parser.parse_html_to_markdown(html_content)
        
        # Display results
        print(f"\n📋 PARSING RESULTS:")
        print("-" * 30)
        
        metadata = result['metadata']
        print(f"✅ Has content: {metadata['has_content']}")
        print(f"🔧 Has OpenAPI: {metadata['has_openapi']}")
        print(f"📅 Processing date: {metadata['processing_date']}")
        
        # Show markdown content info
        markdown_content = result['markdown_content']
        print(f"\n📝 Markdown content: {len(markdown_content):,} characters")
        
        # Show OpenAPI specification info
        openapi_spec = result['openapi_spec']
        if openapi_spec:
            print(f"\n🎯 OpenAPI SPECIFICATION FOUND!")
            print(f"   📄 OpenAPI version: {openapi_spec.get('openapi', 'Unknown')}")
            print(f"   🏷️  API title: {openapi_spec.get('info', {}).get('title', 'Unknown')}")
            print(f"   🔢 API version: {openapi_spec.get('info', {}).get('version', 'Unknown')}")
            print(f"   📝 Description: {openapi_spec.get('info', {}).get('description', 'None')[:80]}...")
            
            # Count servers and paths
            servers = openapi_spec.get('servers', [])
            paths = openapi_spec.get('paths', {})
            print(f"   🌐 Servers: {len(servers)}")
            print(f"   🛣️  Paths: {len(paths)}")
            
            if servers:
                print(f"   📍 Server URLs:")
                for i, server in enumerate(servers[:3], 1):  # Show first 3
                    print(f"      {i}. {server.get('url', 'Unknown')} - {server.get('description', 'No description')}")
        else:
            print(f"\n❌ No OpenAPI specification found")
        
        # Save files
        if metadata['has_content']:
            print(f"\n💾 SAVING FILES...")
            print("-" * 20)
            
            # Save markdown file
            md_file = parser.save_markdown_file(markdown_content)
            print(f"📄 Markdown saved: {md_file}")
            
            # Save OpenAPI file if found
            if openapi_spec:
                json_file = parser.save_openapi_file(openapi_spec)
                print(f"🔧 OpenAPI spec saved: {json_file}")
        
        print(f"\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = test_parser()
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
