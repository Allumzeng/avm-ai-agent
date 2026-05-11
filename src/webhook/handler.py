from fastapi import APIRouter, Request, BackgroundTasks
from src.config import (
    PINECONE_API_KEY, PINECONE_INDEX_NAME,
    GOOGLE_SERVICE_ACCOUNT_JSON, VOYAGE_API_KEY,
)
from src.rag.embedder import create_embedder
from src.rag.store import create_vector_store
from src.ingestion.loader import create_loader
from src.ingestion.pipeline import run_file_ingestion

router = APIRouter()

_PINECONE_INDEX = None
_EMBEDDER = None
_LOADER = None


def _get_resources():
    global _PINECONE_INDEX, _EMBEDDER, _LOADER
    if _PINECONE_INDEX is None:
        _PINECONE_INDEX = create_vector_store(PINECONE_API_KEY, PINECONE_INDEX_NAME)
    if _EMBEDDER is None:
        _EMBEDDER = create_embedder(VOYAGE_API_KEY)
    if _LOADER is None:
        _LOADER = create_loader(GOOGLE_SERVICE_ACCOUNT_JSON)
    return _PINECONE_INDEX, _EMBEDDER, _LOADER


@router.post("/webhook")
async def google_drive_webhook(request: Request, background_tasks: BackgroundTasks):
    state = request.headers.get("X-Goog-Resource-State", "")
    file_id = request.headers.get("X-Goog-Resource-Id", "")

    if state in ("sync", "") or not file_id:
        return {"status": "ignored"}

    pinecone_index, embedder, loader = _get_resources()

    background_tasks.add_task(
        run_file_ingestion,
        loader=loader,
        file_id=file_id,
        pinecone_index=pinecone_index,
        embedder=embedder,
    )
    return {"status": "queued", "file_id": file_id}
