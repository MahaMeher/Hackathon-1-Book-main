---
title: Humanoid Robotics Academy — RAG Chatbot
emoji: 🤖
colorFrom: indigo
colorTo: violet
sdk: gradio
sdk_version: 5.0.0
app_file: gradio_app.py
pinned: false
license: mit
---

# 🤖 Humanoid Robotics Academy — RAG Chatbot

Ask questions about the Humanoid Robotics book and get answers grounded in the actual content using Retrieval-Augmented Generation.

## How it works

1. Your question is converted into a **semantic embedding** (Cohere `embed-english-v3.0`)
2. The embedding is used to **search the Qdrant vector database** for the most relevant book chunks
3. Retrieved chunks are fed as context to **Cohere Command R** to generate a grounded answer
4. Every answer includes **source citations** so you can verify the information

## Run locally

```bash
pip install -r requirements-hf.txt
python gradio_app.py
```

## Environment variables (required)

Set these as **Secrets** in your Hugging Face Space settings:

| Variable | Description |
|---|---|
| `COHERE_API_KEY` | Cohere API key for embeddings and generation |
| `QDRANT_URL` | Qdrant cluster URL |
| `QDRANT_API_KEY` | Qdrant API key |
| `COLLECTION_NAME` | *(optional)* Qdrant collection name (default: `book_vectors`) |
