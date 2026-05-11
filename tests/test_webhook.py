import importlib
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_webhook_returns_200_on_update():
    import src.webhook.handler as handler_module
    with patch.object(handler_module, "create_vector_store", return_value=MagicMock()), \
         patch.object(handler_module, "create_embedder", return_value=MagicMock()), \
         patch.object(handler_module, "create_loader", return_value=MagicMock()), \
         patch.object(handler_module, "run_file_ingestion"):
        # Reset cached singletons so _get_resources() calls the mocked factories
        handler_module._PINECONE_INDEX = None
        handler_module._EMBEDDER = None
        handler_module._LOADER = None
        app = FastAPI()
        app.include_router(handler_module.router)
        client = TestClient(app)
        response = client.post(
            "/webhook",
            headers={
                "X-Goog-Resource-State": "update",
                "X-Goog-Resource-Id": "file_abc123",
            },
        )
        assert response.status_code == 200


def test_webhook_ignores_sync_state():
    import src.webhook.handler as handler_module
    with patch.object(handler_module, "create_vector_store", return_value=MagicMock()), \
         patch.object(handler_module, "create_embedder", return_value=MagicMock()), \
         patch.object(handler_module, "create_loader", return_value=MagicMock()), \
         patch.object(handler_module, "run_file_ingestion") as mock_ingest:
        handler_module._PINECONE_INDEX = None
        handler_module._EMBEDDER = None
        handler_module._LOADER = None
        app = FastAPI()
        app.include_router(handler_module.router)
        client = TestClient(app)
        response = client.post(
            "/webhook",
            headers={
                "X-Goog-Resource-State": "sync",
                "X-Goog-Resource-Id": "file_abc123",
            },
        )
        assert response.status_code == 200
        mock_ingest.assert_not_called()
