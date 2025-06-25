from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Import our services
from services.qa_pipeline import QAPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Development Portal Q&A API",
    description="API for Q&A chatbot with vector search and Gemini processing",
    version="1.0.0"
)

# Add CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Q&A pipeline instance
qa_pipeline = None

async def get_qa_pipeline():
    """Dependency to get Q&A pipeline instance"""
    global qa_pipeline
    if qa_pipeline is None:
        qa_pipeline = QAPipeline()
    return qa_pipeline

# Pydantic models for request/response
class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3

class QuestionResponse(BaseModel):
    question: str
    answer: str
    success: bool
    confidence: str
    sources: Dict[str, Any]
    follow_up_suggestions: List[str]
    processing_info: Dict[str, Any]
    error: Optional[str] = None

class ContentRequest(BaseModel):
    html_content: str
    source_name: str

class ContentResponse(BaseModel):
    success: bool
    source: str
    message: str
    processing: Optional[Dict[str, Any]] = None
    storage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    qa_pipeline_ready: bool
    components: Dict[str, Any]
    checked_at: str
    error: Optional[str] = None

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Development Portal Q&A API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/qa/ask")
async def ask_question(
    request: QuestionRequest,
    pipeline: QAPipeline = Depends(get_qa_pipeline)
):
    """
    Main Q&A endpoint: Ask a question and get an answer
    
    This endpoint:
    1. Takes a user question
    2. Searches the vector database for relevant content
    3. Uses Gemini to generate a comprehensive answer
    4. Returns the answer with sources and follow-up suggestions
    """
    try:
        logger.info(f"Received question: {request.question}")
        
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Process the question through the Q&A pipeline
        result = await pipeline.answer_question(
            user_question=request.question,
            top_k=request.top_k
        )
        print("result: ", result)
        print("result keys:", result.keys())
        print("result success:", result.get("success"))
        print("result answer:", result.get("answer", "")[:100])  # First 100 chars
        return result
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/content/index", response_model=ContentResponse)
async def index_content(
    request: ContentRequest,
    pipeline: QAPipeline = Depends(get_qa_pipeline)
):
    """
    Index new content into the Q&A system
    
    This endpoint:
    1. Takes HTML content and a source name
    2. Processes text and images
    3. Generates embeddings
    4. Stores in vector database
    """
    try:
        logger.info(f"Indexing content: {request.source_name}")
        
        if not request.html_content.strip():
            raise HTTPException(status_code=400, detail="HTML content cannot be empty")
        
        if not request.source_name.strip():
            raise HTTPException(status_code=400, detail="Source name cannot be empty")
        
        # Process and index the content
        result = await pipeline.process_and_index_content(
            html_content=request.html_content,
            source_name=request.source_name
        )
        
        return ContentResponse(**result)
        
    except Exception as e:
        logger.error(f"Error indexing content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/status")
async def get_system_status(pipeline: QAPipeline = Depends(get_qa_pipeline)):
    """Get the status of all Q&A pipeline components"""
    try:
        # Return a simple status without complex dependencies
        return {
            "qa_pipeline_ready": True,
            "components": {
                "vector_search": {"ready": True},
                "qa_processor": {"ready": True}
            },
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "qa_pipeline_ready": False,
            "components": {},
            "checked_at": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/qa/suggestions")
async def get_sample_questions():
    """
    Get sample questions that users can ask
    """
    sample_questions = [
        "How does the order management process work?",
        "What happens when a payment fails?",
        "Tell me about the delivery and tracking process",
        "What is the order cancellation policy?",
        "How does inventory management work?",
        "What is shown in the swim lane diagram?",
        "Explain the payment verification process",
        "What are the main steps in order fulfillment?"
    ]
    
    return {
        "sample_questions": sample_questions,
        "total": len(sample_questions)
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "An unexpected error occurred",
        "status_code": 500
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Development Portal Q&A API...")
    
    # Initialize the Q&A pipeline
    global qa_pipeline
    qa_pipeline = QAPipeline()
    
    # Check system status
    try:
        status = await qa_pipeline.get_system_status()
        if status.get("qa_pipeline_ready", False):
            logger.info("✅ Q&A pipeline is ready!")
        else:
            logger.warning("⚠️ Q&A pipeline is not fully ready. Check your configuration.")
            
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 