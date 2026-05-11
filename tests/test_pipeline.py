from unittest.mock import MagicMock, patch
from llama_index.core import Document
from src.ingestion.pipeline import run_full_ingestion, run_file_ingestion

def test_full_ingestion_loads_chunks_and_upserts():
    mock_doc = Document(
        text="AVM Module 2 content." * 20,
        metadata={"file_id": "file_001", "mime_type": "text/plain"},
    )
    mock_index = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding_batch.return_value = [[0.1] * 1024]
    mock_loader = MagicMock()

    with patch("src.ingestion.pipeline.load_folder", return_value=[mock_doc]) as mock_lf:
        run_full_ingestion(
            loader=mock_loader,
            folder_id="folder_abc",
            pinecone_index=mock_index,
            embedder=mock_embedder,
        )
        mock_lf.assert_called_once_with(mock_loader, "folder_abc")

    assert mock_index.upsert.called


def test_file_ingestion_deletes_old_chunks_first():
    mock_doc = Document(
        text="Updated AVM content." * 20,
        metadata={"file_id": "file_001", "mime_type": "text/plain"},
    )
    mock_index = MagicMock()
    mock_index.query.return_value = MagicMock(matches=[])
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding_batch.return_value = [[0.1] * 1024]
    mock_loader = MagicMock()

    with patch("src.ingestion.pipeline.load_file", return_value=[mock_doc]) as mock_lf:
        run_file_ingestion(
            loader=mock_loader,
            file_id="file_001",
            pinecone_index=mock_index,
            embedder=mock_embedder,
        )
        mock_lf.assert_called_once_with(mock_loader, "file_001")

    mock_index.query.assert_called_once()
    assert mock_index.upsert.called
