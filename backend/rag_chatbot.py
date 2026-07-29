"""
RAG Chatbot for the Humanoid Robotics Academy Book

This module implements a Retrieval-Augmented Generation (RAG) chatbot
that answers questions about the book content using:
- Qdrant vector database for semantic search
- Cohere for embeddings and text generation
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import cohere
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RetrievedContext:
    """A chunk of book content retrieved for answering a question."""
    content: str
    source_url: str
    section: str
    similarity_score: float


@dataclass
class ChatResponse:
    """The chatbot's response with supporting evidence."""
    answer: str
    sources: List[RetrievedContext]
    model_used: str
    execution_time_ms: int


class RAGChatbot:
    """Retrieval-Augmented Generation chatbot for the Humanoid Robotics book."""

    def __init__(self):
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = os.getenv("COLLECTION_NAME", "book_vectors")
        self.embedding_model = "embed-english-v3.0"
        self.generation_model = "command-r-08-2024"  # Cohere chat model
        self.top_k = 5
        self.max_context_chars = 12000  # Max characters for context window

        if not self.cohere_api_key:
            raise ValueError("COHERE_API_KEY not set")
        if not self.qdrant_url:
            raise ValueError("QDRANT_URL not set")
        if not self.qdrant_api_key:
            raise ValueError("QDRANT_API_KEY not set")

        self.cohere_client = cohere.Client(self.cohere_api_key)
        self.qdrant_client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
        )
        logger.info("RAG Chatbot initialized")

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for a text query."""
        response = self.cohere_client.embed(
            texts=[text],
            model=self.embedding_model,
            input_type="search_query"
        )
        return response.embeddings[0]

    def _search_qdrant(self, embedding: List[float]) -> List[RetrievedContext]:
        """Search Qdrant for relevant chunks given an embedding."""
        results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=self.top_k,
            with_payload=True,
            with_vectors=False,
        )

        contexts = []
        for hit in results.points:
            payload = hit.payload or {}
            content = payload.get("content", "")
            if content and content.strip():
                contexts.append(RetrievedContext(
                    content=content,
                    source_url=payload.get("source_url", ""),
                    section=payload.get("section", ""),
                    similarity_score=hit.score,
                ))
        return contexts

    def _build_prompt(self, question: str, contexts: List[RetrievedContext],
                       selected_context: Optional[str] = None) -> str:
        """Build a prompt with retrieved context for the LLM.

        Args:
            question: The user's question
            contexts: Retrieved chunks from Qdrant
            selected_context: Optional text selected by the user from the book page

        Returns:
            A prompt string for the LLM
        """
        context_text = ""
        total_chars = 0

        # If the user selected text from the book, include it as primary context
        if selected_context:
            selected_trimmed = selected_context.strip()[:self.max_context_chars]
            context_text += f"[Selected Passage]\n{selected_trimmed}\n\n"
            total_chars += len(context_text)

        for i, ctx in enumerate(contexts, 1):
            chunk = f"[{i}] From \"{ctx.section}\" ({ctx.source_url}):\n{ctx.content}\n\n"
            if total_chars + len(chunk) > self.max_context_chars:
                break
            context_text += chunk
            total_chars += len(chunk)

        prompt = f"""You are a helpful teaching assistant for the Humanoid Robotics Academy book.
Answer the student's question based ONLY on the provided book content below.
If the book content doesn't contain enough information to answer, say so clearly.
Always cite the section and source URL from which you got the information.

Book Content:
{context_text}

Student Question: {question}

Answer:"""
        return prompt

    def ask(self, question: str, print_sources: bool = True,
            selected_context: Optional[str] = None) -> ChatResponse:
        """
        Ask a question and get an answer grounded in the book content.

        Args:
            question: The user's question about the book
            print_sources: Whether to print the retrieved sources
            selected_context: Optional text selected by the user from the book page

        Returns:
            ChatResponse with answer and sources
        """
        import time
        start = time.time()

        # Step 1: Generate query embedding
        logger.info(f"Processing question: {question[:80]}...")
        embedding = self._generate_embedding(question)

        # Step 2: Retrieve relevant contexts
        contexts = self._search_qdrant(embedding)
        logger.info(f"Retrieved {len(contexts)} relevant chunks")

        if not contexts:
            elapsed = int((time.time() - start) * 1000)
            return ChatResponse(
                answer="I couldn't find any relevant information in the book to answer your question.",
                sources=[],
                model_used=self.generation_model,
                execution_time_ms=elapsed,
            )

        # Step 3: Generate answer using Cohere Chat API
        prompt = self._build_prompt(question, contexts, selected_context=selected_context)

        response = self.cohere_client.chat(
            model=self.generation_model,
            message=prompt,
            max_tokens=500,
            temperature=0.3,
        )

        answer = response.text.strip()

        elapsed = int((time.time() - start) * 1000)

        if print_sources:
            self._print_sources(question, answer, contexts, elapsed)

        return ChatResponse(
            answer=answer,
            sources=contexts,
            model_used=self.generation_model,
            execution_time_ms=elapsed,
        )

    def _print_sources(self, question: str, answer: str,
                       contexts: List[RetrievedContext], elapsed_ms: int):
        """Pretty-print the answer with sources."""
        print("\n" + "=" * 70)
        print(f"Q: {question}")
        print("=" * 70)
        print(f"\nA: {answer}")
        print(f"\n  (answered in {elapsed_ms}ms)")
        print("\n" + "-" * 70)
        print("SOURCES:")
        for i, ctx in enumerate(contexts, 1):
            print(f"  [{i}] Score: {ctx.similarity_score:.4f}")
            print(f"      Section: {ctx.section}")
            print(f"      URL: {ctx.source_url}")
        print("=" * 70)


def chat_cli():
    """Interactive CLI for the RAG chatbot."""
    print("=" * 70)
    print("  Humanoid Robotics Academy - RAG Chatbot")
    print("  Ask questions about the book content!")
    print("  Type 'exit' to quit, '/sources' to toggle source display")
    print("=" * 70)

    try:
        bot = RAGChatbot()
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
        return 1

    show_sources = True

    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break
        if question.lower() == "/sources":
            show_sources = not show_sources
            print(f"Source display: {'ON' if show_sources else 'OFF'}")
            continue

        try:
            bot.ask(question, print_sources=show_sources)
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            print(f"Sorry, I encountered an error: {e}")

    return 0


def main():
    """Entry point for the RAG chatbot."""
    import argparse
    parser = argparse.ArgumentParser(description="RAG Chatbot for Humanoid Robotics Book")
    parser.add_argument("--query", "-q", type=str, help="Single question to answer")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Start interactive chat session")
    args = parser.parse_args()

    if args.query:
        bot = RAGChatbot()
        bot.ask(args.query)
    elif args.interactive:
        return chat_cli()
    else:
        # Default: single question mode
        print("Usage: python rag_chatbot.py --query \"Your question\"")
        print("   or: python rag_chatbot.py --interactive")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
