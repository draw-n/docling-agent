# Docling Assistant MVP

This project is a local-first website application for asking questions about Docling through a retrieval-backed assistant.

## Environment variables

Copy [`.env.example`](.env.example) into your local environment configuration and adjust values as needed.

### Backend retrieval settings

- `USE_QDRANT=true` enables the local-path Qdrant-backed retrieval index
- `QDRANT_PATH=qdrant_data` stores the embedded Qdrant database on disk without Docker
- `QDRANT_COLLECTION=docling_docs` sets the collection name used for indexed documents
- `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2` selects the local embedding model

### Backend generation settings

- `OLLAMA_URL=http://localhost:11434` points the backend to your local Ollama server
- `OLLAMA_MODEL=gemma4` selects the Ollama model used for answer generation

### Frontend API setting

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api` points the frontend to the FastAPI backend

## Local Qdrant setup without Docker

The backend uses [`QdrantClient(path=...)`](backend/app/services/index.py) so Qdrant runs in embedded local mode and persists vectors to disk.

## Ollama installation and usage

### 1. Install Ollama on macOS

Download and install Ollama from [`https://ollama.com/download`](https://ollama.com/download).

### 2. Start Ollama

After installation, start the Ollama app or run:

```bash
ollama serve
```

Ollama should then be available at `http://localhost:11434`.

### 3. Pull a model

Recommended first model:

```bash
ollama pull gemma4
```

### 4. Test Ollama directly

Run:

```bash
ollama run gemma4
```

Then ask a simple question to confirm the model is working.

## Install backend dependencies

Run from [`backend/`](backend/):

```bash
python3 -m pip install -r requirements.txt
```

## Start the backend

Run from [`backend/`](backend/):

```bash
uvicorn main:app --reload --port 8000
```

When [`USE_QDRANT`](.env.example) is enabled, the backend will:

1. load seed documents from [`backend/app/services/ingest.py`](backend/app/services/ingest.py:18)
2. embed them with [`SentenceTransformerEmbedder`](backend/app/services/index.py:54)
3. store them in the local Qdrant path configured by [`QDRANT_PATH`](.env.example)
4. search them through [`QdrantRetrievalIndex`](backend/app/services/index.py:88)

When Ollama is running, the backend will also:

1. retrieve relevant chunks in [`backend/app/services/rag.py`](backend/app/services/rag.py:29)
2. build a prompt in [`generate_answer()`](backend/app/services/generate.py:40)
3. call Ollama through [`/api/generate`](backend/app/services/generate.py:43)
4. return a generated grounded answer with citations

## Current retrieval and generation flow

- [`backend/routes/chat.py`](backend/routes/chat.py:9) receives the user query
- [`backend/app/services/rag.py`](backend/app/services/rag.py:37) retrieves relevant chunks
- [`backend/app/services/generate.py`](backend/app/services/generate.py:40) sends the grounded prompt to Ollama
- [`backend/app/services/index.py`](backend/app/services/index.py:88) performs Qdrant-backed search when enabled
- if Qdrant setup fails, [`get_retrieval_index()`](backend/app/services/index.py:151) falls back to [`InMemoryRetrievalIndex`](backend/app/services/index.py:66)

## Recommended validation steps

1. Install backend dependencies
2. Install and start Ollama
3. Pull [`gemma4`](README.md)
4. Start the backend
5. Send a request to [`POST /api/chat`](backend/routes/chat.py:9)
6. Confirm the answer is generated rather than just concatenated retrieval text