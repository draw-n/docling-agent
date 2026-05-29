from __future__ import annotations

import time
from typing import Iterable, Sequence

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

from app.utils.config import settings
from app.utils.logger import log_error, setup_logger

logger = setup_logger(__name__)


def _build_context(chunks: Iterable[object]) -> str:
    context_parts: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        title = str(getattr(chunk, "title", ""))
        section = str(getattr(chunk, "section", ""))
        url = str(getattr(chunk, "url", ""))
        snippet = str(getattr(chunk, "snippet", ""))
        content = str(getattr(chunk, "content", ""))

        context_parts.append(
            "\n".join(
                [
                    f"Source {index}:",
                    f"Title: {title}",
                    f"Section: {section}",
                    f"URL: {url}",
                    f"Snippet: {snippet}",
                    f"Content: {content}",
                ]
            )
        )

    return "\n\n".join(context_parts)


def _build_prompt(query: str, chunks: Iterable[object]) -> str:
    context = _build_context(chunks)

    return "\n\n".join(
        [
            "You are a Docling assistant helping users understand how to use Docling.",
            "Answer the user's question using only the provided context.",
            "When the context contains relevant steps, commands, code, or outputs, give a direct practical answer instead of saying the context is insufficient.",
            "Prefer official documentation over GitHub examples when both are present.",
            "Summarize the answer in clear steps when possible.",
            "If markdown conversion is mentioned, explicitly mention the Docling conversion flow and output format when supported by the context.",
            "Only say the context is insufficient if none of the sources contain relevant information for the user's question.",
            f"User question: {query}",
            f"Context:\n{context}",
        ]
    )


def generate_answer(query: str, chunks: Sequence[object]) -> str:
    """Generate an answer using Ollama with retry logic and error handling."""
    prompt = _build_prompt(query, chunks)
    
    last_error: Exception | None = None
    
    for attempt in range(settings.ollama_max_retries):
        try:
            logger.info(f"Generating answer (attempt {attempt + 1}/{settings.ollama_max_retries})")
            
            response = requests.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=settings.ollama_timeout,
            )
            response.raise_for_status()
            
            payload = response.json()
            answer = str(payload.get("response", "")).strip()
            
            if not answer:
                logger.warning("Ollama returned empty response")
                raise ValueError("Empty response from Ollama")
            
            logger.info("Successfully generated answer")
            return answer
            
        except (ConnectionError, Timeout) as e:
            last_error = e
            log_error(logger, e, {"attempt": attempt + 1, "query_length": len(query)})
            
            if attempt < settings.ollama_max_retries - 1:
                delay = settings.ollama_retry_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            
        except HTTPError as e:
            last_error = e
            log_error(logger, e, {"status_code": e.response.status_code if e.response else None})
            
            # Don't retry on 4xx errors (client errors)
            if e.response and 400 <= e.response.status_code < 500:
                logger.error("Client error, not retrying")
                break
            
            if attempt < settings.ollama_max_retries - 1:
                delay = settings.ollama_retry_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                
        except Exception as e:
            last_error = e
            log_error(logger, e, {"attempt": attempt + 1})
            break
    
    # All retries failed
    error_msg = f"Failed to generate answer after {settings.ollama_max_retries} attempts"
    if last_error:
        error_msg += f": {str(last_error)}"
    logger.error(error_msg)
    
    return "I'm having trouble connecting to the language model. Please try again in a moment."

# Made with Bob
