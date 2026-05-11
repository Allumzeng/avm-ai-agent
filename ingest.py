#!/usr/bin/env python3
"""Run full Google Drive -> Pinecone ingestion."""
from src.config import (
    PINECONE_API_KEY, PINECONE_INDEX_NAME,
    GOOGLE_DRIVE_FOLDER_ID, GOOGLE_SERVICE_ACCOUNT_JSON,
    VOYAGE_API_KEY,
)
from src.rag.embedder import create_embedder
from src.rag.store import create_vector_store
from src.ingestion.loader import create_loader
from src.ingestion.pipeline import run_full_ingestion

if __name__ == "__main__":
    print("Connecting to Pinecone...")
    index = create_vector_store(PINECONE_API_KEY, PINECONE_INDEX_NAME)
    embedder = create_embedder(VOYAGE_API_KEY)
    loader = create_loader(GOOGLE_SERVICE_ACCOUNT_JSON)

    print(f"Ingesting from Google Drive folder: {GOOGLE_DRIVE_FOLDER_ID}")
    count = run_full_ingestion(loader, GOOGLE_DRIVE_FOLDER_ID, index, embedder)
    print(f"Done. {count} chunks upserted to Pinecone.")
