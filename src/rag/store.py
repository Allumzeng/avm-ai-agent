from pinecone import Pinecone, ServerlessSpec
from llama_index.embeddings.voyageai import VoyageEmbedding

def create_vector_store(api_key: str, index_name: str):
    pc = Pinecone(api_key=api_key)
    if index_name not in [i.name for i in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(index_name)

_EMBED_BATCH = 20   # chunks per Voyage API call
_UPSERT_BATCH = 100 # vectors per Pinecone upsert call

def upsert_chunks(index, embedder, chunks: list[dict]) -> None:
    total = len(chunks)
    print(f"[ingest] embedding {total} chunks (batch={_EMBED_BATCH})...", flush=True)
    vectors = []
    for i in range(0, total, _EMBED_BATCH):
        batch = chunks[i : i + _EMBED_BATCH]
        texts = [c["text"] for c in batch]
        embeddings = embedder.get_text_embedding_batch(texts, show_progress=False)
        for chunk, emb in zip(batch, embeddings):
            vectors.append({
                "id": chunk["id"],
                "values": emb,
                "metadata": {**chunk["metadata"], "text": chunk["text"]},
            })
        done = min(i + _EMBED_BATCH, total)
        if (i // _EMBED_BATCH) % 25 == 0 or done == total:
            print(f"[ingest] embedded {done}/{total}", flush=True)

    print(f"[ingest] uploading {len(vectors)} vectors to Pinecone (batch={_UPSERT_BATCH})...", flush=True)
    for i in range(0, len(vectors), _UPSERT_BATCH):
        index.upsert(vectors=vectors[i : i + _UPSERT_BATCH])
        done = min(i + _UPSERT_BATCH, len(vectors))
        if (i // _UPSERT_BATCH) % 20 == 0 or done == len(vectors):
            print(f"[ingest] uploaded {done}/{len(vectors)}", flush=True)
    print("[ingest] done", flush=True)

def delete_chunks_by_source(index, source_file: str) -> None:
    results = index.query(
        vector=[0.0] * 1024,
        top_k=10000,
        filter={"source_file": {"$eq": source_file}},
        include_metadata=False,
    )
    ids = [match.id for match in results.matches]
    if ids:
        index.delete(ids=ids)
