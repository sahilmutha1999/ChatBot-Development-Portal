# Development Portal Assistant

A domain-specific chatbot for parsing and understanding technical documentation, swim lane diagrams, and OpenAPI specifications. Built with **FastAPI backend** and **Streamlit frontend** with **Pinecone vector search**.

## ✨ Features

- **Clean Chat Interface**: ChatGPT-like UI with left-right message flow
- **Text Parsing**: Intelligent chunking of documentation and API specs
- **Vector Search**: Pinecone-powered semantic search
- **Multi-format Support**: HTML, PDF, DOCX, and OpenAPI specifications
- **Real-time Processing**: Fast document indexing and question answering

## 🏗️ Architecture

```
├── frontend/          # Streamlit chat interface
├── backend/           # FastAPI server
│   ├── main.py       # Main API endpoints
│   ├── services/     # Core services
│   │   ├── text_parser.py    # Document parsing
│   │   ├── chunking.py       # Text chunking
│   │   ├── embeddings.py     # Sentence transformers
│   │   └── vector_store.py   # Pinecone integration
│   └── config.py     # Configuration management
├── test_content.html  # Sample test content
└── requirements.txt   # Frontend dependencies
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd ChatBot-Development-Portal

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Required: Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=dev-portal-chatbot

# Optional: Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Optional: Advanced Features
GOOGLE_API_KEY=your_google_api_key_here
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
```

### 3. Start Backend Server

```bash
# Option 1: Using the runner script
python run_backend.py

# Option 2: Manual setup
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Start Frontend

```bash
# Option 1: Using the original runner script
python run_app.py

# Option 2: Manual setup
pip install -r requirements.txt
cd frontend
streamlit run app.py
```

### 5. Initialize with Test Content

1. **Backend**: http://localhost:8000
2. **Frontend**: http://localhost:8501
3. **API Docs**: http://localhost:8000/docs

**Parse test content:**

```bash
# Use the API endpoint to parse test webpage
curl -X POST "http://localhost:8000/parse-webpage"
```

## 📖 Usage

### Parsing Content

**Parse HTML content:**

```python
import requests

response = requests.post("http://localhost:8000/parse", json={
    "content": "Your document content here",
    "source": "document_name"
})
```

**Parse test webpage:**

```python
response = requests.post("http://localhost:8000/parse-webpage")
```

### Asking Questions

Use the Streamlit frontend or API directly:

```python
response = requests.post("http://localhost:8000/chat", json={
    "query": "How does payment processing work?"
})
```

### Sample Questions

- "What happens when a payment is declined?"
- "What are the available API endpoints?"
- "Explain the order management workflow"
- "How does inventory tracking work?"

## 🔧 Configuration

### Embedding Models

Supported sentence-transformer models:

- `all-MiniLM-L6-v2` (default, 384 dimensions)
- `all-mpnet-base-v2` (768 dimensions)
- `multi-qa-MiniLM-L6-cos-v1` (384 dimensions)

### Chunking Parameters

```env
MAX_CHUNK_SIZE=500      # Maximum characters per chunk
CHUNK_OVERLAP=50        # Overlap between chunks
MIN_CHUNK_SIZE=100      # Minimum chunk size
```

### Vector Search

```env
DEFAULT_TOP_K=5         # Number of results to return
SIMILARITY_THRESHOLD=0.7 # Minimum similarity score
```

## 🛠️ Development

### Project Structure

```
backend/services/
├── text_parser.py      # HTML/document parsing
├── chunking.py         # Intelligent text chunking
├── embeddings.py       # Sentence transformer embeddings
└── vector_store.py     # Pinecone vector operations
```

### Adding New Parsers

1. Extend `TextParser` class in `text_parser.py`
2. Add new chunking strategies in `chunking.py`
3. Update API endpoints in `main.py`

### Custom Embedding Models

```python
# In embeddings.py
embedding_service = EmbeddingService(model_name="your-model-name")
```

## 📊 API Endpoints

### Health Check

- `GET /` - Basic health check
- `GET /health` - Detailed system status

### Content Management

- `POST /parse` - Parse and store content
- `POST /parse-webpage` - Parse test webpage

### Chat Interface

- `POST /chat` - Ask questions about parsed content

### Vector Operations

- Search is handled automatically during chat requests

## 🎨 Frontend Features

### Clean Chat Interface

- **Right-aligned user messages** (blue gradient)
- **Left-aligned assistant responses** (white with border)
- **Auto-scroll** to latest messages
- **Responsive design** for mobile and desktop

### Real-time Features

- **Typing indicators** during processing
- **Error handling** with user-friendly messages
- **Backend connection status**

## 🔍 Troubleshooting

### Common Issues

**Backend not starting:**

```bash
# Check if port 8000 is available
netstat -an | findstr 8000

# Try different port
uvicorn main:app --port 8001
```

**Pinecone connection errors:**

- Verify API key in `.env` file
- Check Pinecone index name
- Ensure you have an active Pinecone account

**Frontend connection errors:**

- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`

**Embedding model download:**

- First run downloads the model (~100MB)
- Ensure stable internet connection
- Models are cached locally after first download

### Performance Tips

1. **Batch processing**: Use `/parse` endpoint for multiple documents
2. **Chunking optimization**: Adjust `MAX_CHUNK_SIZE` based on content type
3. **Vector search**: Use metadata filters for faster queries

## 🚧 Roadmap

- [ ] **Image parsing** for swim lane diagrams
- [ ] **PDF document support**
- [ ] **Hugging Face model integration**
- [ ] **Gemini API integration**
- [ ] **Advanced chunking strategies**
- [ ] **User authentication**
- [ ] **Conversation memory**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Ready to get started?** Run `python run_backend.py` and `python run_app.py` to launch your chatbot! 🚀
