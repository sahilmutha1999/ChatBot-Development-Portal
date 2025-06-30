#!/usr/bin/env python3
"""
End-to-End Data Pipeline for Development Portal Chatbot
This script handles the complete workflow:
1. Clear old vector database content (optional)
2. Parse HTML content (with OpenAPI detection)
3. Generate embeddings for text and images
4. Store everything in vector database
5. Verify the results
"""

import asyncio
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.services.rag_pipeline import RAGPipeline
from backend.services.text_parser import TextParser

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.OKBLUE):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.ENDC}")

def print_banner():
    """Print pipeline banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════════╗
    ║             🚀 End-to-End Data Pipeline                        ║
    ║                                                                ║
    ║  HTML → Parse (Text + Images + OpenAPI) → Embeddings → VectorDB  ║
    ║  Enhanced with OpenAPI/Swagger Detection                       ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print_colored(banner, Colors.HEADER)

def clear_vector_database():
    """Clear all vectors from Pinecone (imported from clear_vectors.py)"""
    try:
        print_colored("🧹 Clearing vector database...", Colors.WARNING)
        
        # Import and use the clear function
        from dotenv import load_dotenv
        from pinecone import Pinecone
        
        load_dotenv()
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "dev-portal-chatbot")
        
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        
        # Get current stats
        stats = index.describe_index_stats()
        vector_count = stats.total_vector_count
        
        if vector_count == 0:
            print_colored("✅ Vector database is already empty", Colors.OKGREEN)
            return
        
        print_colored(f"📊 Found {vector_count} vectors in database", Colors.OKBLUE)
        print_colored("🗑️  Deleting all vectors...", Colors.WARNING)
        
        index.delete(delete_all=True)
        
        # Verify deletion
        new_stats = index.describe_index_stats()
        if new_stats.total_vector_count == 0:
            print_colored("✅ Successfully cleared vector database", Colors.OKGREEN)
        else:
            print_colored(f"⚠️  Some vectors may remain: {new_stats.total_vector_count}", Colors.WARNING)
            
    except Exception as e:
        print_colored(f"❌ Error clearing vector database: {e}", Colors.FAIL)
        raise

async def process_html_content(html_file: str, source_name: str) -> Dict[str, Any]:
    """
    Process HTML content through the complete pipeline
    
    Args:
        html_file: Path to HTML file
        source_name: Name identifier for the content source
        
    Returns:
        Complete processing results
    """
    try:
        # Step 1: Read HTML content
        print_colored(f"📄 Reading HTML file: {html_file}", Colors.OKBLUE)
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print_colored(f"📊 HTML content: {len(html_content):,} characters", Colors.OKBLUE)
        
        # Step 2: Enhanced parsing with OpenAPI detection
        print_colored("🔍 Parsing content (Text + Images + OpenAPI)...", Colors.OKBLUE)
        
        parser = TextParser()
        parse_result = parser.parse_html_to_markdown(html_content)
        
        # Display parsing results
        metadata = parse_result['metadata']
        print_colored(f"   ✅ Has content: {metadata['has_content']}", Colors.OKGREEN)
        print_colored(f"   🔧 Has OpenAPI: {metadata['has_openapi']}", Colors.OKGREEN if metadata['has_openapi'] else Colors.WARNING)
        
        if metadata['has_openapi']:
            openapi_spec = parse_result['openapi_spec']
            print_colored(f"   📋 OpenAPI: {openapi_spec.get('info', {}).get('title', 'Unknown')} v{openapi_spec.get('info', {}).get('version', 'Unknown')}", Colors.OKCYAN)
            
            # Save OpenAPI spec
            openapi_file = parser.save_openapi_file(openapi_spec)
            print_colored(f"   💾 OpenAPI saved: {openapi_file}", Colors.OKGREEN)
        
        # Save markdown content
        markdown_file = parser.save_markdown_file(parse_result['markdown_content'])
        print_colored(f"   📝 Markdown saved: {markdown_file}", Colors.OKGREEN)
        
        # Step 3: RAG Pipeline Processing
        print_colored("⚡ Processing through RAG pipeline...", Colors.OKBLUE)
        
        rag_pipeline = RAGPipeline()
        rag_result = await rag_pipeline.process_and_store_html(html_content, source_name)
        
        # Display RAG results
        processing = rag_result['processing']
        storage = rag_result['storage']
        
        print_colored(f"   📊 Total chunks: {processing['total_chunks']}", Colors.OKBLUE)
        print_colored(f"   📝 Text chunks: {processing['text_chunks']}", Colors.OKBLUE)
        print_colored(f"   🖼️  Image chunks: {processing['image_chunks']}", Colors.OKBLUE)
        print_colored(f"   💾 Stored successfully: {storage['successful_upserts']}/{processing['total_chunks']}", Colors.OKGREEN)
        
        if storage['failed_upserts'] > 0:
            print_colored(f"   ⚠️  Failed to store: {storage['failed_upserts']} chunks", Colors.WARNING)
        
        # Combine results
        complete_result = {
            "parsing": parse_result,
            "rag_processing": rag_result,
            "files_created": {
                "markdown": markdown_file,
                "openapi": openapi_file if metadata['has_openapi'] else None
            },
            "success": rag_result['success'] and metadata['has_content']
        }
        
        return complete_result
        
    except Exception as e:
        print_colored(f"❌ Error processing content: {e}", Colors.FAIL)
        raise

async def verify_results(source_name: str):
    """Verify the pipeline results by testing search"""
    try:
        print_colored("🔍 Verifying results with test searches...", Colors.OKBLUE)
        
        rag_pipeline = RAGPipeline()
        
        # Test queries
        test_queries = [
            "How does the order management process work?",
            "What happens when payment fails?",
            "What APIs are available?",  # This should find OpenAPI content
            "Tell me about the delivery process"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print_colored(f"   Query {i}: {query}", Colors.OKCYAN)
            
            # Search for similar content
            results = await rag_pipeline.search_similar_content(query, top_k=2)
            
            if results:
                print_colored(f"   ✅ Found {len(results)} relevant chunks", Colors.OKGREEN)
                for j, result in enumerate(results, 1):
                    content_type = result['metadata'].get('content_type', 'unknown')
                    score = result['score']
                    content_preview = result['metadata']['content'][:80] + "..."
                    print_colored(f"      {j}. [{content_type.upper()}] Score: {score:.3f}", Colors.OKBLUE)
                    print_colored(f"         {content_preview}", Colors.OKBLUE)
            else:
                print_colored(f"   ❌ No results found", Colors.WARNING)
        
        # Get final statistics
        status = await rag_pipeline.get_pipeline_status()
        if 'stats' in status.get('vector_store', {}):
            stats = status['vector_store']['stats']
            total_vectors = stats.get('total_vector_count', 'N/A')
            print_colored(f"📈 Total vectors in database: {total_vectors}", Colors.OKGREEN)
        
    except Exception as e:
        print_colored(f"⚠️  Error during verification: {e}", Colors.WARNING)

async def run_pipeline(html_file: str, source_name: str, clear_db: bool = False):
    """Run the complete end-to-end pipeline"""
    
    print_banner()
    
    # Step 1: Clear database if requested
    if clear_db:
        try:
            clear_vector_database()
        except Exception as e:
            print_colored(f"❌ Failed to clear database: {e}", Colors.FAIL)
            return False
    
    # Step 2: Process content
    try:
        result = await process_html_content(html_file, source_name)
        
        if not result['success']:
            print_colored("❌ Pipeline failed during processing", Colors.FAIL)
            return False
            
    except Exception as e:
        print_colored(f"❌ Pipeline failed: {e}", Colors.FAIL)
        return False
    
    # # Step 3: Verify results
    # try:
    #     await verify_results(source_name)
    # except Exception as e:
    #     print_colored(f"⚠️  Verification had issues: {e}", Colors.WARNING)
    
    # Step 4: Success summary
    print_colored("\n🎉 PIPELINE COMPLETED SUCCESSFULLY!", Colors.OKGREEN)
    print_colored("="*60, Colors.OKGREEN)
    
    parsing_result = result['parsing']
    rag_result = result['rag_processing']
    
    print_colored("📋 SUMMARY:", Colors.BOLD)
    print_colored(f"   📄 Source: {source_name}", Colors.OKBLUE)
    print_colored(f"   📝 Markdown content: {len(parsing_result['markdown_content']):,} characters", Colors.OKBLUE)
    print_colored(f"   🔧 OpenAPI detected: {'Yes' if parsing_result['metadata']['has_openapi'] else 'No'}", Colors.OKBLUE)
    print_colored(f"   📊 Total chunks processed: {rag_result['processing']['total_chunks']}", Colors.OKBLUE)
    print_colored(f"   💾 Chunks stored in vector DB: {rag_result['storage']['successful_upserts']}", Colors.OKBLUE)
    
    files_created = result['files_created']
    print_colored(f"   📁 Files created:", Colors.OKBLUE)
    print_colored(f"      • Markdown: {files_created['markdown']}", Colors.OKBLUE)
    if files_created['openapi']:
        print_colored(f"      • OpenAPI: {files_created['openapi']}", Colors.OKBLUE)
    
    print_colored("\n🚀 Your chatbot is ready with the new content!", Colors.OKGREEN)
    
    return True

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="End-to-End Data Pipeline for Development Portal Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process test content without clearing database
  python run_data_pipeline.py backend/test_content.html

  # Process with custom source name
  python run_data_pipeline.py backend/test_content.html --source "my_webpage"

  # Clear database and process content
  python run_data_pipeline.py backend/test_content.html --clear-db

  # Full pipeline with custom settings
  python run_data_pipeline.py my_content.html --source "product_docs" --clear-db
        """
    )
    
    parser.add_argument(
        "html_file",
        help="Path to HTML file to process"
    )
    
    parser.add_argument(
        "--source", "-s",
        default=None,
        help="Source name for the content (default: derived from filename)"
    )
    
    parser.add_argument(
        "--clear-db", "-c",
        action="store_true",
        help="Clear vector database before processing new content"
    )
    
    args = parser.parse_args()
    
    # Validate HTML file
    if not os.path.exists(args.html_file):
        print_colored(f"❌ HTML file not found: {args.html_file}", Colors.FAIL)
        sys.exit(1)
    
    # Generate source name if not provided
    source_name = args.source
    if not source_name:
        source_name = Path(args.html_file).stem
    
    # Run the pipeline
    try:
        success = asyncio.run(run_pipeline(args.html_file, source_name, args.clear_db))
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print_colored("\n🛑 Pipeline interrupted by user", Colors.WARNING)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", Colors.FAIL)
        sys.exit(1)

if __name__ == "__main__":
    main() 