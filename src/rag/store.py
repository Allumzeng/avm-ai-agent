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

def upsert_chunks(index, embedder, chunks: list[dict]) -> None:
    vectors = []
    for chunk in chunks:
        embedding = embedder.get_text_embedding(chunk["text"])
        vectors.append({
            "id": chunk["id"],
            "values": embedding,
            "metadata": {**chunk["metadata"], "text": chunk["text"]},
        })
    if vectors:
        index.upsert(vectors=vectors)

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
