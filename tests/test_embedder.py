from unittest.mock import MagicMock, patch
from src.rag.embedder import create_embedder

def test_embedder_creates_with_correct_model():
    with patch("src.rag.embedder.VoyageEmbedding") as MockVoyage:
        create_embedder("test-api-key")
        MockVoyage.assert_called_once_with(
            model_name="voyage-multilingual-2",
            voyage_api_key="test-api-key",
        )

def test_embedder_returns_embedder_instance():
    with patch("src.rag.embedder.VoyageEmbedding") as MockVoyage:
        mock_instance = MagicMock()
        MockVoyage.return_value = mock_instance
        result = create_embedder("test-api-key")
        assert result is mock_instance
