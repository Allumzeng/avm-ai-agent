from unittest.mock import MagicMock, patch
from src.rag.store import create_vector_store, upsert_chunks, delete_chunks_by_source

def test_create_vector_store_connects_to_index():
    with patch("src.rag.store.Pinecone") as MockPC:
        mock_pc = MagicMock()
        MockPC.return_value = mock_pc
        mock_pc.list_indexes.return_value = [MagicMock(name="avm-knowledge-base")]
        create_vector_store("test-key", "avm-knowledge-base")
        MockPC.assert_called_once_with(api_key="test-key")
        mock_pc.Index.assert_called_once_with("avm-knowledge-base")

def test_upsert_chunks_calls_index_upsert(sample_chunks):
    mock_index = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024
    upsert_chunks(mock_index, mock_embedder, sample_chunks)
    assert mock_index.upsert.called

def test_delete_chunks_by_source_queries_and_deletes():
    mock_index = MagicMock()
    mock_index.query.return_value = MagicMock(
        matches=[MagicMock(id="chunk_001"), MagicMock(id="chunk_002")]
    )
    delete_chunks_by_source(mock_index, "file_001")
    mock_index.delete.assert_called_once_with(ids=["chunk_001", "chunk_002"])

def test_delete_chunks_by_source_no_op_when_empty():
    mock_index = MagicMock()
    mock_index.query.return_value = MagicMock(matches=[])
    delete_chunks_by_source(mock_index, "file_nobody")
    mock_index.delete.assert_not_called()
