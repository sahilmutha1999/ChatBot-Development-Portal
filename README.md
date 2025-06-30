# 🤖 Development Portal RAG Chatbot

A domain-specific chatbot that parses **HTML documents**, **swimlane diagrams**, and **OpenAPI specifications** to answer questions using advanced RAG (Retrieval-Augmented Generation) architecture.

## 🔄 RAG Data Flow

```
HTML Documents → BeautifulSoup Parsing → Header-based Chunking → 
Sentence Transformers Embeddings → Pinecone Vector DB → 
Semantic Search → Gemini 1.5 Flash → Contextual Answers
```

## 🛠️ Technologies Used

- **Document Scraping**: BeautifulSoup4, html2text
- **Content Parsing**: Custom HTML parser with OpenAPI detection
- **Text Chunking**: Header-based semantic chunking
- **Image Processing**: Gemini 1.5 Flash for swimlane diagrams
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Database**: Pinecone
- **LLM**: Google Gemini 1.5 Flash for answer generation
- **Backend**: FastAPI with real-time accuracy metrics
- **Frontend**: Streamlit chat interface

## 🚀 Quick Start

### 1. Start Frontend
```bash
cd frontend
streamlit run app.py
```
*Frontend will run on: http://localhost:8501*

### 2. Start Backend (New Terminal)
```bash
cd backend  
uvicorn main:app --reload --port 8000
```
*Backend will run on: http://localhost:8000*

### 3. Parse Documents (Optional)
To add new content to the chatbot:
```bash
cd backend
python run_data_pipeline.py test_content.html --clear-db
```
*This parses test content and clears existing vectors*

## 📋 Environment Setup

Create `.env` file in root directory:
```env
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=dev-portal-chatbot
GEMINI_API_KEY=your_gemini_key
```

## ✨ Features

- **Real-time Accuracy Metrics** after every query
- **Multi-modal Content** (Text + Images + API specs)  
- **Semantic Search** with top-3 chunk retrieval
- **Professional Chat Interface** with expandable metrics
- **Automatic Content Detection** (Text/Swimlane/OpenAPI)

## 💬 Usage

1. Ask questions about your documents
2. View real-time accuracy scores 
3. Explore detailed performance metrics
4. Get AI-powered contextual answers