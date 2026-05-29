from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse, RefreshResponse
from app.services.index import get_retrieval_index
from app.services.rag import build_grounded_response

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    normalized_query = request.query.strip()
    return build_grounded_response(normalized_query)


@router.post("/refresh", response_model=RefreshResponse)
def refresh_docs():
    index = get_retrieval_index()
    refresh_result = index.refresh()
    return RefreshResponse(**refresh_result)

# Made with Bob
