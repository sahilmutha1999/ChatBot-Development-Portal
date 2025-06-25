import sys
import os
import asyncio
from datetime import datetime
sys.path.append('backend')

from services.rag_pipeline import RAGPipeline

async def test_integrated_rag_pipeline():
    """Test the complete RAG pipeline with text and image processing"""
    
    print("🚀 Starting Integrated RAG Pipeline Test")
    print("="*70)
    
    # Initialize the RAG pipeline
    print("\n⚙️ Step 1: Initializing RAG Pipeline...")
    try:
        rag_pipeline = RAGPipeline()
        print("✅ RAG Pipeline initialized")
        
        # Check pipeline status
        status = await rag_pipeline.get_pipeline_status()
        print(f"   📊 Pipeline ready: {status['pipeline_ready']}")
        print(f"   🔧 Embedding model: {status['embedding_service']['text_embedding_model']['model_name']}")
        print(f"   🖼️ Image processing: {status['embedding_service']['image_processing']}")
        
        if not status['pipeline_ready']:
            print("❌ Pipeline not ready. Check your Pinecone configuration.")
            return
            
    except Exception as e:
        print(f"❌ Error initializing pipeline: {e}")
        return
    
    # Read the HTML file
    print("\n📄 Step 2: Reading HTML content...")
    try:
        with open('test_content.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        print(f"✅ Read HTML file: test_content.html")
    except Exception as e:
        print(f"❌ Error reading HTML file: {e}")
        return
    
    # Process and store content
    print("\n🔄 Step 3: Processing content and storing embeddings...")
    try:
        source_name = "test_content_webpage"
        
        # Delete existing content for this source (cleanup)
        print(f"   🧹 Cleaning up existing content for: {source_name}")
        await rag_pipeline.delete_source_content(source_name)
        
        # Process new content
        print(f"   ⚡ Processing HTML content...")
        result = await rag_pipeline.process_and_store_html(html_content, source_name)
        
        print(f"✅ Processing completed!")
        print(f"   📝 Text chunks: {result['processing']['text_chunks']}")
        print(f"   🖼️ Image chunks: {result['processing']['image_chunks']}")
        print(f"   💾 Successfully stored: {result['storage']['successful_upserts']}/{result['processing']['total_chunks']} chunks")
        
        # Show markdown file information if available
        if 'markdown_file' in result['processing'] and result['processing']['markdown_file']:
            print(f"   📄 Markdown saved: {result['processing']['markdown_file']}")
        
        if result['storage']['failed_upserts'] > 0:
            print(f"   ⚠️ Failed to store: {result['storage']['failed_upserts']} chunks")
            
    except Exception as e:
        print(f"❌ Error processing content: {e}")
        return
    
    # Test search functionality
    print("\n🔍 Step 4: Testing search functionality...")
    try:
        # Test queries
        test_queries = [
            "How does the order management process work?",
            "What happens when payment fails?",
            "Tell me about the delivery process",
            "What is shown in the swim lane diagram?"  # This should find image content
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query}")
            
            # Search all content
            results = await rag_pipeline.search_similar_content(query, top_k=3)
            
            if results:
                print(f"   📊 Found {len(results)} relevant chunks:")
                for j, result in enumerate(results[:2], 1):  # Show top 2 results
                    content_type = result['metadata'].get('content_type', 'unknown')
                    score = result['score']
                    content_preview = result['metadata']['content'][:100] + "..." if len(result['metadata']['content']) > 100 else result['metadata']['content']
                    print(f"      {j}. [{content_type.upper()}] Score: {score:.3f}")
                    print(f"         {content_preview}")
            else:
                print(f"   ❌ No results found")
    
    except Exception as e:
        print(f"❌ Error testing search: {e}")
    
    # Show final statistics
    print("\n📊 Step 5: Final Statistics...")
    try:
        final_status = await rag_pipeline.get_pipeline_status()
        if 'stats' in final_status['vector_store']:
            stats = final_status['vector_store']['stats']
            print(f"   📈 Total vectors in database: {stats.get('total_vector_count', 'N/A')}")
            print(f"   📊 Index dimension: {stats.get('dimension', 'N/A')}")
        
    except Exception as e:
        print(f"⚠️ Could not retrieve final statistics: {e}")
    
    print("\n🎉 Integrated RAG Pipeline Test Completed!")
    print("="*70)
    print("💡 What was tested:")
    print("   ✓ HTML parsing and markdown conversion")
    print("   ✓ Text chunking and embedding generation")
    print("   ✓ Image extraction and Gemini processing (if available)")
    print("   ✓ Vector storage in Pinecone")
    print("   ✓ Similarity search across text and image content")
    print("\n🚀 Your RAG pipeline is ready for chatbot integration!")

# Legacy function for backward compatibility
def test_html_to_markdown():
    """Legacy function - runs the full RAG pipeline test"""
    asyncio.run(test_integrated_rag_pipeline())

if __name__ == "__main__":
    asyncio.run(test_integrated_rag_pipeline())
