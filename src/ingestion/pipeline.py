from src.ingestion.loader import load_folder, load_file
from src.ingestion.chunker import chunk_documents
from src.rag.store import upsert_chunks, delete_chunks_by_source

def run_full_ingestion(loader, folder_id: str, pinecone_index, embedder) -> int:
    documents = load_folder(loader, folder_id)
    chunks = chunk_documents(documents)
    upsert_chunks(pinecone_index, embedder, chunks)
    return len(chunks)

def run_file_ingestion(loader, file_id: str, pinecone_index, embedder) -> int:
    delete_chunks_by_source(pinecone_index, file_id)
    documents = load_file(loader, file_id)
    chunks = chunk_documents(documents)
    upsert_chunks(pinecone_index, embedder, chunks)
    return len(chunks)
