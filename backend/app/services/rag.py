from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import ChatResponse, Citation
from app.services.generate import generate_answer
from app.services.index import IndexedDocument, RetrievalIndex, get_retrieval_index


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    title: str
    url: str
    snippet: str
    content: str
    source_type: str
    section: str
    priority: int


def _indexed_document_to_chunk(document: IndexedDocument) -> RetrievedChunk:
    return RetrievedChunk(
        id=document.id,
        title=document.title,
        url=document.url,
        snippet=document.snippet,
        content=document.content,
        source_type=document.source_type,
        section=document.section,
        priority=document.priority,
    )


def retrieve_chunks(
    query: str,
    limit: int = 3,
    index: RetrievalIndex | None = None,
) -> list[RetrievedChunk]:
    active_index = index or get_retrieval_index()
    indexed_documents = active_index.search(query=query, limit=limit)
    return [_indexed_document_to_chunk(document) for document in indexed_documents]


def build_grounded_response(
    query: str,
    index: RetrievalIndex | None = None,
) -> ChatResponse:
    retrieved_chunks = retrieve_chunks(query, index=index)

    if not retrieved_chunks:
        return ChatResponse(
            answer=(
                "I could not find enough indexed Docling context to answer that confidently yet. "
                "Try asking about parsing PDFs, pipelines, or table extraction."
            ),
            citations=[],
            grounded=False,
        )

    generated_answer = generate_answer(query, retrieved_chunks)

    citations = [
        Citation(
            title=f"{chunk.title} · {chunk.section}",
            url=chunk.url,
            snippet=chunk.snippet,
        )
        for chunk in retrieved_chunks
    ]

    return ChatResponse(
        answer=generated_answer,
        citations=citations,
        grounded=True,
    )

# Made with Bob
