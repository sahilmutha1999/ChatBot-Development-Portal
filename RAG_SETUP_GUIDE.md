# 🚀 Integrated RAG Pipeline Setup Guide

This guide will help you set up the complete RAG pipeline with text and image processing capabilities.

## 📋 **What's Been Created**

### 1. **Unified Embedding Service** (`backend/services/unified_embedding_service.py`)
- Processes both text and images from HTML content
- Uses Gemini-1.5-Flash for image analysis
- Generates embeddings for both content types
- Handles image path resolution

### 2. **RAG Pipeline** (`backend/services/rag_pipeline.py`) 
- Complete pipeline: HTML → Embeddings → Vector Storage
- Batch processing and storage in Pinecone
- Search functionality with content type filtering
- Health monitoring and statistics

### 3. **Updated Test Parser** (`backend/test_parser.py`)
- Now tests the complete RAG pipeline
- Processes text + images and stores in Pinecone
- Tests search functionality across content types

## ⚙️ **Setup Instructions**

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Environment Configuration
Create a `.env` file in your project root with:

```bash
# Pinecone Configuration (Required)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=dev-portal-chatbot
EMBEDDING_DIMENSION=384

# Google Gemini Configuration (Optional - for image processing)
GOOGLE_API_KEY=your_google_api_key_here

# Embedding Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Logging Level
LOG_LEVEL=INFO
```

### Step 3: Get API Keys

#### **Pinecone (Required)**
1. Go to [pinecone.io](https://pinecone.io)
2. Create account and get API key
3. Add to your `.env` file

#### **Google Gemini (Optional but Recommended)**
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Get API key for Gemini
3. Add to your `.env` file

**Note:** Without Gemini, images will be skipped but text processing will work fine.

## 🧪 **Testing Your Setup**

### Run the Complete Test
```bash
cd backend
python test_parser.py
```

### Expected Output:
```
🚀 Starting Integrated RAG Pipeline Test
======================================================================

⚙️ Step 1: Initializing RAG Pipeline...
✅ RAG Pipeline initialized
   📊 Pipeline ready: True
   🔧 Embedding model: all-MiniLM-L6-v2
   🖼️ Image processing: Gemini-1.5-Flash

📄 Step 2: Reading HTML content...
✅ Read HTML file: test_content.html

🔄 Step 3: Processing content and storing embeddings...
   🧹 Cleaning up existing content for: test_content_webpage
   ⚡ Processing HTML content...
✅ Processing completed!
   📝 Text chunks: 6
   🖼️ Image chunks: 1
   💾 Successfully stored: 7/7 chunks

🔍 Step 4: Testing search functionality...
   Query 1: How does the order management process work?
   📊 Found 3 relevant chunks:
      1. [TEXT] Score: 0.789
         Product Ordering System Overview Our product ordering system is designed to provide a seamless...
      2. [IMAGE] Score: 0.654  
         Image Description: Swim Lane Diagram - Order Management Process Flow Detailed Analysis: This is a swim...

🎉 Integrated RAG Pipeline Test Completed!
```

## 🔧 **How It Works**

### **Text Processing Flow:**
1. **HTML Parsing** → Markdown conversion with fixed image paths
2. **Text Chunking** → Intelligent section-based chunking  
3. **Embedding Generation** → Using sentence-transformers
4. **Vector Storage** → Batch upsert to Pinecone with metadata

### **Image Processing Flow:**
1. **Image Detection** → Extract image references from markdown
2. **Path Resolution** → Resolve relative paths correctly
3. **Gemini Analysis** → Detailed business process analysis
4. **Content Creation** → Combine alt-text + Gemini description
5. **Embedding Generation** → Convert image content to embeddings
6. **Vector Storage** → Store with "image" content type metadata

### **Search & Retrieval:**
- **Unified Search** → Search across both text and image content
- **Content Filtering** → Filter by "text" or "image" content types
- **Metadata Rich** → Full context preserved in vector metadata

## 📊 **Metadata Structure**

### **Text Chunks:**
```json
{
  "content_type": "text",
  "source": "test_content_webpage", 
  "chunk_type": "general",
  "char_count": 156
}
```

### **Image Chunks:**
```json
{
  "content_type": "image",
  "source": "test_content_webpage",
  "image_path": "/path/to/media/swim_lane.png",
  "alt_text": "Swim Lane Diagram - Order Management Process Flow",
  "has_gemini_analysis": true
}
```

## 🎯 **Usage in Your Chatbot**

```python
from backend.services.rag_pipeline import RAGPipeline

# Initialize
rag = RAGPipeline()

# Process content
result = await rag.process_and_store_html(html_content, "my_webpage")

# Search for answers
results = await rag.search_similar_content("How does the process work?", top_k=3)

# Filter by content type
text_only = await rag.search_similar_content("query", content_type_filter="text")
images_only = await rag.search_similar_content("query", content_type_filter="image")
```

## 🚨 **Troubleshooting**

### **Issue: Image paths not working**
- **Solution**: The text parser now automatically adjusts image paths from markdown location to actual file location

### **Issue: Gemini not working**
- **Check**: GOOGLE_API_KEY in .env file
- **Fallback**: System will work without Gemini, just skip image processing

### **Issue: Pinecone connection failed** 
- **Check**: PINECONE_API_KEY in .env file
- **Check**: Internet connection
- **Check**: Index name matches your Pinecone dashboard

### **Issue: Embeddings dimension mismatch**
- **Solution**: Delete and recreate Pinecone index, or change EMBEDDING_DIMENSION in .env

## ✅ **Next Steps**

1. **Run the test** to ensure everything works
2. **Integrate with your chatbot** using the RAGPipeline class
3. **Add more content** by processing additional HTML files
4. **Customize chunking** by modifying the ChunkingService parameters
5. **Enhance search** by adding filters and ranking algorithms

Your RAG pipeline is now ready to handle both text and visual content for your chatbot! 🎉 