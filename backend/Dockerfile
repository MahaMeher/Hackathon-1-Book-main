# =============================================================================
# Backend — FastAPI RAG Chatbot Server
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system deps (only what lxml needs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first for layer caching
COPY pyproject.toml ./

# Install Python deps (editable install so the package is resolved)
RUN pip install --no-cache-dir -e .

# Copy the rest of the backend source
COPY . .

# Expose the API port
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
