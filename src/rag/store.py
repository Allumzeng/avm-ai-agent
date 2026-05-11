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
    vectors = []
    for i in range(0, len(chunks), _EMBED_BATCH):
        batch = chunks[i : i + _EMBED_BATCH]
        texts = [c["text"] for c in batch]
        embeddings = embedder.get_text_embedding_batch(texts, show_progress=False)
        for chunk, emb in zip(batch, embeddings):
            vectors.append({
                "id": chunk["id"],
                "values": emb,
                "metadata": {**chunk["metadata"], "text": chunk["text"]},
            })
    for i in range(0, len(vectors), _UPSERT_BATCH):
        index.upsert(vectors=vectors[i : i + _UPSERT_BATCH])

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
