from typing import Optional


def retrieve_chunks(
    index,
    embedder,
    query: str,
    top_k: int = 5,
    module_filter: Optional[int] = None,
) -> list[str]:
    query_vector = embedder.get_text_embedding(query)
    kwargs = {
        "vector": query_vector,
        "top_k": top_k,
        "include_metadata": True,
    }
    if module_filter is not None:
        kwargs["filter"] = {"module": {"$eq": module_filter}}

    results = index.query(**kwargs)
    return [
        match.metadata["text"]
        for match in results.matches
        if "text" in match.metadata
    ]
