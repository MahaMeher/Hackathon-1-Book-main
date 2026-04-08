/sp.constitution

Project: AI-Spec-Driven Book with Embedded RAG Chatbot

Principles:
- Spec-first, reproducible development
- Content accuracy and grounding
- No hallucination beyond book content
- Modular and transparent system design

Book Standards:
- Written using Claude Code + Spec-Kit Plus
- Built with Docusaurus, deployed on GitHub Pages
- Markdown/MDX, clear chapter structure
- Target audience: software developers

RAG Chatbot Standards:
- FastAPI backend
- OpenAI Agents / ChatKit SDKs
- Qdrant Cloud (vector search)
- Neon Serverless Postgres
- Answers based on:
  1. Full book content
  2. User-selected text only (when provided)

Constraints:

- Free-tier services only
- API keys via environment variables
- Chatbot embedded in book UI

Success Criteria:
- Book publicly accessible
- Accurate, grounded chatbot responses
- Selected-text scope strictly enforced
- Project fully reproducible from specs

