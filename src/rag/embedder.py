from llama_index.embeddings.voyageai import VoyageEmbedding

def create_embedder(api_key: str) -> VoyageEmbedding:
    return VoyageEmbedding(
        model_name="voyage-multilingual-2",
        voyage_api_key=api_key,
    )
