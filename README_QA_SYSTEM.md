# 🤖 Development Portal Q&A System

A complete end-to-end question-answering system powered by vector search and Gemini AI that processes both text and images from HTML content.

## 🌟 Features

### Core Capabilities

- **Multi-modal Content Processing**: Handles both text and images from HTML documents
- **Vector Search**: Uses Pinecone for semantic similarity search
- **AI-Powered Answers**: Gemini AI generates comprehensive answers from search results
- **Interactive Web Interface**: Beautiful Streamlit frontend with chat interface
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Real-time Processing**: Live content indexing and search capabilities

### Advanced Features

- **Smart Chunking**: Header-based content segmentation for better context
- **Image Analysis**: Gemini processes diagrams and visual content for business insights
- **Follow-up Suggestions**: AI-generated question suggestions based on context
- **Confidence Scoring**: Assess answer reliability based on source similarity
- **Source Attribution**: Detailed source tracking with similarity scores
- **System Monitoring**: Real-time status monitoring of all components

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI       │    │    Pinecone     │
│   Frontend      │◄──►│    Backend       │◄──►│  Vector Store   │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Gemini AI      │    │  Embedding      │
                       │   Q&A Processor  │    │  Service        │
                       └──────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### Required

- Python 3.8+
- Pinecone API Key
- Internet connection for embeddings

### Optional (for enhanced features)

- Google Gemini API Key (for AI-powered answers and image processing)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd ChatBot-Development-Portal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
# Required
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional (for Gemini AI features)
GOOGLE_API_KEY=your_google_api_key_here
```

### 3. Start the System

```bash
# Option 1: Use the startup script (recommended)
python start_qa_system.py

# Option 2: Start manually
# Terminal 1 - Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
streamlit run app.py --server.port 8501
```

### 4. Access the System

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📱 How to Use

### Web Interface (Streamlit)

1. **Open the Frontend**: Visit http://localhost:8501
2. **Check System Status**: Use the sidebar to verify all components are ready
3. **Ask Questions**: Type your question in the input field
4. **Review Answers**: Get detailed responses with:
   - AI-generated answers
   - Confidence scores
   - Source attribution
   - Follow-up suggestions
5. **Index New Content**: Use the sidebar to upload and index HTML content

### Sample Questions

- "How does the order management process work?"
- "What happens when a payment fails?"
- "Tell me about the delivery and tracking process"
- "What is shown in the swim lane diagram?"
- "Explain the payment verification process"

### API Usage

#### Ask a Question

```bash
curl -X POST "http://localhost:8000/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "How does order processing work?", "top_k": 3}'
```

#### Index New Content

```bash
curl -X POST "http://localhost:8000/content/index" \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<html>...</html>",
    "source_name": "business_process_v2"
  }'
```

#### Check System Status

```bash
curl "http://localhost:8000/system/status"
```

## 🔧 System Components

### Backend Services

#### 1. QA Pipeline (`backend/services/qa_pipeline.py`)

- Orchestrates the complete Q&A flow
- Manages vector search and AI processing
- Handles content indexing

#### 2. QA Processor (`backend/services/qa_processor.py`)

- Gemini AI integration for answer generation
- Context preparation and prompt engineering
- Follow-up question suggestions

#### 3. RAG Pipeline (`backend/services/rag_pipeline.py`)

- Vector search functionality
- Content embedding and storage
- Similarity-based retrieval

#### 4. Unified Embedding Service (`backend/services/unified_embedding_service.py`)

- Text and image processing
- Multi-modal embedding generation
- Content chunking and preparation

### API Endpoints

| Endpoint            | Method | Description                                 |
| ------------------- | ------ | ------------------------------------------- |
| `/qa/ask`         | POST   | Ask a question and get an AI-powered answer |
| `/content/index`  | POST   | Index new HTML content into the system      |
| `/system/status`  | GET    | Check the status of all system components   |
| `/qa/suggestions` | GET    | Get sample questions                        |
| `/health`         | GET    | Basic health check                          |

### Frontend Features

- **Interactive Chat Interface**: Clean, responsive design
- **Real-time Status Monitoring**: Component health indicators
- **Content Upload**: Direct HTML content indexing
- **Answer Metadata**: Confidence scores, sources, timestamps
- **Follow-up Suggestions**: AI-generated related questions
- **Sample Questions**: Pre-defined question bank

## 📊 Response Format

### Question Answer Response

```json
{
  "question": "How does order processing work?",
  "answer": "Based on the documentation...",
  "success": true,
  "confidence": "high",
  "sources": {
    "total_sources": 3,
    "source_details": [
      {
        "content_type": "text",
        "source": "business_process_v1",
        "similarity_score": 0.854
      }
    ]
  },
  "follow_up_suggestions": [
    "What happens if an order fails?",
    "How long does order processing take?"
  ],
  "processing_info": {
    "vector_search_results": 3,
    "qa_success": true,
    "processed_at": "2024-01-01T12:00:00"
  }
}
```

## 🛠️ Configuration

### Environment Variables

| Variable                | Required | Description                           | Default            |
| ----------------------- | -------- | ------------------------------------- | ------------------ |
| `PINECONE_API_KEY`    | Yes      | Pinecone vector database API key      | -                  |
| `GOOGLE_API_KEY`      | No       | Google Gemini API key for AI features | -                  |
| `PINECONE_INDEX_NAME` | No       | Pinecone index name                   | development-portal |
| `EMBEDDING_MODEL`     | No       | Sentence transformer model            | all-MiniLM-L6-v2   |

### System Settings

- **Backend Port**: 8000 (configurable in `start_qa_system.py`)
- **Frontend Port**: 8501 (configurable in `start_qa_system.py`)
- **Default Top-K**: 3 search results per query
- **Max Chunk Size**: 1000 characters
- **Embedding Dimensions**: 384 (based on model)

## 🔍 Troubleshooting

### Common Issues

#### Backend Won't Start

```bash
# Check if port 8000 is in use
netstat -an | grep 8000

# Try a different port
uvicorn main:app --port 8001
```

#### Frontend Connection Error

- Ensure backend is running on port 8000
- Check `BACKEND_URL` in `frontend/app.py`
- Verify no firewall blocking connections

#### Empty Search Results

- Verify content has been indexed
- Check Pinecone connection and API key
- Ensure embedding model is loaded

#### Gemini Features Not Working

- Set `GOOGLE_API_KEY` environment variable
- Check Google Cloud billing and quotas
- Verify API key permissions

### Debug Mode

Enable debug logging by setting environment variable:

```bash
export LOG_LEVEL=DEBUG
```

### Health Checks

Visit these URLs to check component status:

- Backend Health: http://localhost:8000/health
- System Status: http://localhost:8000/system/status
- Frontend: http://localhost:8501 (should load without errors)

## 📈 Performance Tips

### Optimization

- Use appropriate `top_k` values (3-5 for most queries)
- Index content in batches for large datasets
- Monitor Pinecone usage and quotas
- Use caching for frequently accessed content

### Scaling

- Deploy backend with multiple workers: `uvicorn main:app --workers 4`
- Use load balancer for multiple frontend instances
- Consider Pinecone serverless for variable workloads
- Implement request rate limiting for production

## 🔒 Security Considerations

- Store API keys securely (use environment variables)
- Implement authentication for production deployment
- Sanitize user inputs to prevent injection attacks
- Use HTTPS for production deployments
- Monitor and log all API requests

## 📝 Development

### Adding New Features

1. Backend changes go in `backend/services/`
2. API endpoints in `backend/main.py`
3. Frontend updates in `frontend/app.py`
4. Update tests in `backend/test_*.py`

### Testing

```bash
cd backend
python -m pytest test_*.py -v
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check system status at `/system/status`
4. Review logs for error details

## 🎯 Roadmap

### Planned Features

- [ ] Authentication and user management
- [ ] Conversation history persistence
- [ ] Advanced analytics and metrics
- [ ] Multi-language support
- [ ] Batch content upload
- [ ] Custom embedding models
- [ ] Integration with external data sources

---

**Built with ❤️ using FastAPI, Streamlit, Pinecone, and Gemini AI**
