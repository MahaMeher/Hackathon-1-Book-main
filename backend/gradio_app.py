"""
Gradio Chat App — Humanoid Robotics Academy RAG Chatbot
=======================================================
Designed for Hugging Face Spaces deployment.

Usage:
    gradio app.py          # Dev mode with live reload
    python app.py          # Direct launch
"""

import os
import sys
import time
import logging

import gradio as gr

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(__file__))

from rag_chatbot import RAGChatbot, ChatResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Theme colours — match the book's indigo / purple palette
# ---------------------------------------------------------------------------
THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="violet",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
    text_size=gr.themes.Size(
        text_sm="0.9rem",
        text_md="1rem",
        text_lg="1.15rem",
    ),
)

CUSTOM_CSS = """
footer { display: none !important; }
.gradio-container { max-width: 900px !important; margin: 0 auto; }
h1 { background: linear-gradient(135deg, #6366F1, #A78BFA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.source-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; margin: 6px 0; font-size: 0.85rem; }
.source-card strong { color: #4F46E5; }
.dark .source-card { background: #1e1b4b; border-color: #3730a3; }
.status-ok { color: #10B981; }
"""

# ---------------------------------------------------------------------------
# Example questions
# ---------------------------------------------------------------------------
EXAMPLES = [
    "What is ROS 2 and why is it important for humanoid robots?",
    "How do I set up a Gazebo simulation?",
    "What is NVIDIA Isaac and how does it work with ROS 2?",
    "Explain Vision-Language-Action (VLA) models",
    "What sensors are commonly used in humanoid robots?",
]

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

_chatbot: RAGChatbot | None = None


def get_bot() -> RAGChatbot:
    global _chatbot
    if _chatbot is None:
        try:
            _chatbot = RAGChatbot()
            logger.info("RAGChatbot initialised")
        except ValueError as exc:
            logger.error(f"Failed to initialise RAGChatbot: {exc}")
            raise
    return _chatbot


def chat_fn(message: str, history: list) -> str:
    """Gradio chat function — returns markdown with answer + sources."""
    try:
        bot = get_bot()
        result: ChatResponse = bot.ask(
            message,
            print_sources=False,
        )

        # Build answer
        parts = [result.answer]

        # Sources section
        if result.sources:
            parts.append("\n\n---\n**📚 Sources**\n")
            for i, src in enumerate(result.sources, 1):
                parts.append(
                    f'<div class="source-card">'
                    f'<strong>[{i}] {src.section}</strong> — '
                    f'<em>score {src.similarity_score:.3f}</em><br>'
                    f'{src.content[:200]}{"…" if len(src.content) > 200 else ""}<br>'
                    f'<a href="{src.source_url}" target="_blank">{src.source_url}</a>'
                    f'</div>'
                )

        # Footer
        parts.append(
            f'\n\n<small style="color: #94a3b8;">'
            f'Model: {result.model_used} · {result.execution_time_ms}ms'
            f'</small>'
        )

        return "".join(parts)

    except ValueError as exc:
        return (
            "⚠️ **Configuration Error**\n\n"
            f"`{exc}`\n\n"
            "Please make sure `COHERE_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY` "
            "are set as **Secrets** in your Hugging Face Space settings."
        )
    except Exception as exc:
        logger.exception("Chat error")
        return f"⚠️ **Something went wrong**\n\n```\n{exc}\n```"


# ---------------------------------------------------------------------------
# Build UI
# ---------------------------------------------------------------------------

def build_ui():
    with gr.Blocks(theme=THEME, css=CUSTOM_CSS, title="Humanoid Robotics Academy — Chat") as demo:
        gr.Markdown(
            "# 🤖 Humanoid Robotics Academy\n"
            "Ask questions about the book content — answers are grounded in the actual "
            "material using **Retrieval-Augmented Generation**."
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.ChatInterface(
                    fn=chat_fn,
                    title=None,
                    description=None,
                    examples=EXAMPLES,
                    clear_btn="Clear",
                    submit_btn="Ask",
                    placeholder="Ask a question about ROS 2, NVIDIA Isaac, VLA models…",
                )

            with gr.Column(scale=1, min_width=260):
                gr.Markdown("### ⚙️ Status")
                status_val = gr.HTML(
                    value='<span class="status-ok">● Connected</span>'
                    if _chatbot is not None
                    else "<span>● Starting…</span>"
                )

                gr.Markdown(
                    "### 💡 Tips\n"
                    "- Ask specific questions for best results\n"
                    "- Answers are based **only** on the book content\n"
                    "- Source sections are cited for every answer\n"
                )

                gr.Markdown(
                    "### 🔗 Links\n"
                    "- [GitHub Repo](https://github.com/MahaMeher/Hackathon-1-Book)\n"
                )

        # Try initialising early so the status shows correctly on page load
        try:
            get_bot()
            status_val.value = '<span class="status-ok">● Connected</span>'
        except Exception:
            status_val.value = '<span style="color:#EF4444;">● Disconnected — check Secrets</span>'

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

demo = build_ui()

if __name__ == "__main__":
    port = int(os.getenv("GRADIO_PORT", "7860"))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True,
    )
