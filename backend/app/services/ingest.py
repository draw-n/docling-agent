from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

from app.utils.logger import log_error, setup_logger

logger = setup_logger(__name__)


@dataclass(frozen=True)
class SourceDocument:
    id: str
    title: str
    url: str
    snippet: str
    content: str
    source_type: str
    section: str
    priority: int


DOCS_BASE_URL = "https://docling-project.github.io/docling/"
DEFAULT_DOC_PATHS = (
    "",
    "concepts/",
    "examples/",
    "faq/",
)


class DoclingHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        cleaned = data.strip()
        if not cleaned:
            return

        if self._in_title:
            self._title_parts.append(cleaned)

        self._text_parts.append(cleaned)

    @property
    def title(self) -> str:
        return " ".join(self._title_parts).strip()

    @property
    def text(self) -> str:
        return " ".join(self._text_parts).strip()


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    normalized_text = _normalize_whitespace(text)
    if not normalized_text:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(normalized_text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = normalized_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(end - overlap, start + 1)

    return chunks


def _build_document_id(url: str, chunk_index: int) -> str:
    digest = hashlib.md5(f"{url}::{chunk_index}".encode("utf-8")).hexdigest()
    return f"docling-web-{digest}"


def _fetch_page(url: str, timeout: int = 30) -> tuple[str, str]:
    """Fetch and parse a web page with error handling."""
    try:
        logger.info(f"Fetching page: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        parser = DoclingHtmlParser()
        parser.feed(response.text)

        title = parser.title or url
        text = parser.text
        
        logger.info(f"Successfully fetched page: {url} ({len(text)} chars)")
        return title, text
        
    except (ConnectionError, Timeout) as e:
        log_error(logger, e, {"url": url})
        raise RuntimeError(f"Failed to fetch {url}: Network error") from e
        
    except HTTPError as e:
        log_error(logger, e, {"url": url, "status_code": e.response.status_code if e.response else None})
        raise RuntimeError(f"Failed to fetch {url}: HTTP {e.response.status_code if e.response else 'error'}") from e
        
    except Exception as e:
        log_error(logger, e, {"url": url})
        raise RuntimeError(f"Failed to parse {url}") from e


def fetch_docling_documents(paths: tuple[str, ...] = DEFAULT_DOC_PATHS) -> list[SourceDocument]:
    documents: list[SourceDocument] = []

    for path in paths:
        page_url = urljoin(DOCS_BASE_URL, path)
        title, text = _fetch_page(page_url)
        chunks = _chunk_text(text)

        for chunk_index, chunk in enumerate(chunks):
            snippet = chunk[:220].strip()
            documents.append(
                SourceDocument(
                    id=_build_document_id(page_url, chunk_index),
                    title=title,
                    url=page_url,
                    snippet=snippet,
                    content=chunk,
                    source_type="official_docs",
                    section=path or "home",
                    priority=3,
                )
            )

    return documents


def load_seed_documents() -> list[SourceDocument]:
    """Load seed documents with fallback to hardcoded defaults."""
    try:
        logger.info("Attempting to fetch live Docling documentation")
        fetched_documents = fetch_docling_documents()
        if fetched_documents:
            logger.info(f"Successfully loaded {len(fetched_documents)} documents from web")
            return fetched_documents
    except Exception as e:
        log_error(logger, e, {"source": "fetch_docling_documents"})
        logger.warning("Falling back to hardcoded seed documents")

    return [
        SourceDocument(
            id="official-docs-overview",
            title="Docling Documentation",
            url="https://docling-project.github.io/docling/",
            snippet="Primary documentation source for Docling usage and concepts.",
            content=(
                "Docling is a document processing toolkit that can convert documents such as PDFs "
                "into structured representations for downstream workflows."
            ),
            source_type="official_docs",
            section="Overview",
            priority=3,
        ),
        SourceDocument(
            id="official-docs-concepts",
            title="Docling Concepts",
            url="https://docling-project.github.io/docling/concepts/",
            snippet="Overview of pipelines, conversion flow, and structured outputs.",
            content=(
                "Docling pipelines focus on converting source documents into structured outputs such "
                "as markdown, JSON, and extracted elements like tables."
            ),
            source_type="official_docs",
            section="Concepts",
            priority=3,
        ),
        SourceDocument(
            id="official-docs-pdf-processing",
            title="Docling PDF Processing",
            url="https://docling-project.github.io/docling/examples/",
            snippet="Examples for parsing PDFs and converting them into structured content.",
            content=(
                "Docling can be used to parse PDFs and transform them into structured markdown or "
                "JSON outputs for downstream processing."
            ),
            source_type="official_docs",
            section="Examples",
            priority=2,
        ),
        SourceDocument(
            id="github-readme",
            title="Docling GitHub Repository",
            url="https://github.com/docling-project/docling",
            snippet="Secondary source for examples, README guidance, and implementation details.",
            content=(
                "The Docling GitHub repository contains examples, README guidance, and implementation "
                "details that complement the official documentation."
            ),
            source_type="github",
            section="README",
            priority=1,
        ),
    ]

# Made with Bob
