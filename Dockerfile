FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# CPU-only torch first, so requirements.txt doesn't pull the multi-GB CUDA build
RUN pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

# Bake the embedding + reranker models into the image (no download on startup)
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY *.py ./
COPY data/processed ./data/processed

# Build the Chroma vector store into the image, so a cold start doesn't re-embed
RUN python -c "import retrival; e, m = retrival.load_chunks(); retrival.build_vector_entries(e, m)"

EXPOSE 5000

# Cloud Run sets $PORT (default 8080); falls back to 5000 locally / in compose.
# One worker: each worker loads its own copy of the models
CMD uvicorn api:api --host 0.0.0.0 --port ${PORT:-5000} --workers 1
