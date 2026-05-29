from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from sentence_transformers import SentenceTransformer

from app.services.ingest import SourceDocument, load_seed_documents
from app.utils.config import settings
from app.utils.logger import log_error, setup_logger

logger = setup_logger(__name__)


@dataclass(frozen=True)
class IndexedDocument:
    id: str
    title: str
    url: str
    snippet: str
    content: str
    source_type: str
    section: str
    priority: int


class RetrievalIndex(Protocol):
    def search(self, query: str, limit: int = 3) -> list[IndexedDocument]:
        ...

    def refresh(self) -> dict[str, str | int]:
        ...


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


def _to_indexed_document(document: SourceDocument) -> IndexedDocument:
    return IndexedDocument(
        id=document.id,
        title=document.title,
        url=document.url,
        snippet=document.snippet,
        content=document.content,
        source_type=document.source_type,
        section=document.section,
        priority=document.priority,
    )


def _document_text(document: IndexedDocument) -> str:
    return f"{document.title} {document.section} {document.snippet} {document.content}"


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str | None = None) -> None:
        resolved_model_name = model_name or settings.embedding_model
        logger.info(f"Loading embedding model: {resolved_model_name}")
        self._model = SentenceTransformer(resolved_model_name)

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()


class InMemoryRetrievalIndex:
    def __init__(self, documents: list[SourceDocument] | None = None) -> None:
        self._documents = [_to_indexed_document(document) for document in (documents or load_seed_documents())]

    def search(self, query: str, limit: int = 3) -> list[IndexedDocument]:
        normalized_terms = {term for term in query.lower().split() if term}

        scored_documents: list[tuple[int, IndexedDocument]] = []
        for document in self._documents:
            haystack = _document_text(document).lower()
            score = sum(1 for term in normalized_terms if term in haystack)
            score += document.priority

            if document.source_type == "official_docs":
                score += 2

            scored_documents.append((score, document))

        ranked_documents = sorted(scored_documents, key=lambda item: item[0], reverse=True)
        return [document for score, document in ranked_documents if score > 0][:limit]

    def refresh(self) -> dict[str, str | int]:
        refreshed_documents = load_seed_documents()
        self._documents = [_to_indexed_document(document) for document in refreshed_documents]
        return {
            "status": "ok",
            "documents_indexed": len(self._documents),
            "collection_name": "in_memory",
            "backend": "in_memory",
        }


class QdrantRetrievalIndex:
    def __init__(
        self,
        documents: list[SourceDocument] | None = None,
        embedder: Embedder | None = None,
        collection_name: str | None = None,
        storage_path: str | None = None,
    ) -> None:
        try:
            self._documents = [_to_indexed_document(document) for document in (documents or load_seed_documents())]
            self._embedder = embedder or SentenceTransformerEmbedder()
            self._collection_name = collection_name or settings.qdrant_collection
            self._storage_path = storage_path or settings.qdrant_path
            
            logger.info(f"Initializing Qdrant at {self._storage_path}")
            Path(self._storage_path).mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=self._storage_path)
            self._vector_size = len(self._embedder.embed("docling"))
            
            self._ensure_collection()
            self.index_documents()
            logger.info(f"Qdrant index initialized with {len(self._documents)} documents")
        except Exception as e:
            log_error(logger, e, {"collection": self._collection_name})
            raise

    def _ensure_collection(self) -> None:
        collections = self._client.get_collections().collections
        collection_names = {collection.name for collection in collections}

        if self._collection_name in collection_names:
            return

        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=self._vector_size,
                distance=qdrant_models.Distance.COSINE,
            ),
        )

    def index_documents(self) -> None:
        points = [
            qdrant_models.PointStruct(
                id=document.id,
                vector=self._embedder.embed(_document_text(document)),
                payload={
                    "id": document.id,
                    "title": document.title,
                    "url": document.url,
                    "snippet": document.snippet,
                    "content": document.content,
                    "source_type": document.source_type,
                    "section": document.section,
                    "priority": document.priority,
                },
            )
            for document in self._documents
        ]

        self._client.upsert(
            collection_name=self._collection_name,
            points=points,
            wait=True,
        )

    def refresh(self) -> dict[str, str | int]:
        refreshed_documents = load_seed_documents()
        self._documents = [_to_indexed_document(document) for document in refreshed_documents]
        self._client.delete(
            collection_name=self._collection_name,
            points_selector=qdrant_models.FilterSelector(
                filter=qdrant_models.Filter(),
            ),
            wait=True,
        )
        self.index_documents()
        return {
            "status": "ok",
            "documents_indexed": len(self._documents),
            "collection_name": self._collection_name,
            "backend": "qdrant",
        }

    def search(self, query: str, limit: int = 3) -> list[IndexedDocument]:
        query_vector = self._embedder.embed(query)
        results = self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )

        documents: list[IndexedDocument] = []
        for result in results:
            payload = result.payload or {}
            documents.append(
                IndexedDocument(
                    id=str(payload.get("id", result.id)),
                    title=str(payload.get("title", "")),
                    url=str(payload.get("url", "")),
                    snippet=str(payload.get("snippet", "")),
                    content=str(payload.get("content", "")),
                    source_type=str(payload.get("source_type", "")),
                    section=str(payload.get("section", "")),
                    priority=int(payload.get("priority", 0)),
                )
            )

        return documents


_RETRIEVAL_INDEX: RetrievalIndex | None = None


def get_retrieval_index() -> RetrievalIndex:
    """Get or create the global retrieval index with proper error handling."""
    global _RETRIEVAL_INDEX

    if _RETRIEVAL_INDEX is not None:
        return _RETRIEVAL_INDEX

    if settings.use_qdrant:
        try:
            logger.info("Attempting to initialize Qdrant index")
            _RETRIEVAL_INDEX = QdrantRetrievalIndex()
            return _RETRIEVAL_INDEX
        except Exception as e:
            log_error(logger, e, {"backend": "qdrant"})
            logger.warning("Falling back to in-memory index")
            _RETRIEVAL_INDEX = InMemoryRetrievalIndex()
            return _RETRIEVAL_INDEX

    logger.info("Using in-memory index")
    _RETRIEVAL_INDEX = InMemoryRetrievalIndex()
    return _RETRIEVAL_INDEX

# Made with Bob
