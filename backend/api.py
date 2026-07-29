"""
FastAPI server for the Humanoid Robotics Academy RAG Chatbot.

Provides a REST API for the Docusaurus frontend chatbot to query
the book content using the RAGChatbot pipeline.
"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Humanoid Robotics Academy - RAG Chatbot API",
    version="0.1.0",
    description="REST API for querying the Humanoid Robotics book content via RAG",
)

# ---------------------------------------------------------------------------
# CORS Middleware
# Allow the Docusaurus dev server (localhost:3000) to access the API
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request payload for the chat endpoint."""
    query: str = Field(..., min_length=1, max_length=5000, description="User's question")
    selected_context: Optional[str] = Field(None, max_length=12000, description="Optional selected text from the book page")


class SourceItem(BaseModel):
    """A single source citation from the book content."""
    content: str
    section: str
    source_url: str
    similarity_score: float


class ChatResponse(BaseModel):
    """Response payload from the chat endpoint."""
    answer: str
    sources: List[SourceItem] = []
    model_used: str = ""
    execution_time_ms: int = 0
    status: str = "success"


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health_check():
    """Return server status for health monitoring."""
    return {"status": "ok", "service": "rag-chatbot-api"}


# ---------------------------------------------------------------------------
# Chat Endpoint
# ---------------------------------------------------------------------------


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a question to the RAG chatbot and receive a grounded answer.

    The answer is generated from the book's vectorized content using
    Cohere embeddings + Qdrant search + Cohere generation.
    """
    try:
        from rag_chatbot import RAGChatbot

        bot = RAGChatbot()
        result = bot.ask(
            request.query,
            print_sources=False,
            selected_context=request.selected_context,
        )

        return ChatResponse(
            answer=result.answer,
            sources=[
                SourceItem(
                    content=ctx.content,
                    section=ctx.section,
                    source_url=ctx.source_url,
                    similarity_score=ctx.similarity_score,
                )
                for ctx in result.sources
            ],
            model_used=result.model_used,
            execution_time_ms=result.execution_time_ms,
            status="success",
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Sorry, I encountered an error while processing your question. Please try again.",
        )
