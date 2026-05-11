from unittest.mock import MagicMock, patch
from src.agent.client import AVMAgentClient

def _make_client():
    mock_index = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024
    mock_index.query.return_value = MagicMock(matches=[])
    return AVMAgentClient(
        api_key="test-key",
        pinecone_index=mock_index,
        embedder=mock_embedder,
    )

def test_client_initializes():
    client = _make_client()
    assert client is not None

def test_get_response_returns_string():
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = "AVM 的四大模組分別是資源、作業中心、作業與價值標的模組。"
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [mock_text_block]

    with patch("src.agent.client.anthropic.Anthropic") as MockAnthropic:
        mock_api = MagicMock()
        MockAnthropic.return_value = mock_api
        mock_api.messages.create.return_value = mock_response

        client = _make_client()
        result = client.get_response(
            history=[{"role": "user", "content": "AVM 有哪四大模組？"}],
            role="analyst",
        )

    assert isinstance(result, str)
    assert len(result) > 0

def test_get_response_handles_tool_use_then_end_turn():
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "tool_123"
    tool_block.name = "search_avm_knowledge"
    tool_block.input = {"query": "idle capacity cost"}

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Idle capacity cost is the cost of unused productive time."

    first_response = MagicMock()
    first_response.stop_reason = "tool_use"
    first_response.content = [tool_block]

    second_response = MagicMock()
    second_response.stop_reason = "end_turn"
    second_response.content = [text_block]

    with patch("src.agent.client.anthropic.Anthropic") as MockAnthropic:
        mock_api = MagicMock()
        MockAnthropic.return_value = mock_api
        mock_api.messages.create.side_effect = [first_response, second_response]

        client = _make_client()
        result = client.get_response(
            history=[{"role": "user", "content": "What is idle capacity cost?"}],
            role="analyst",
        )

    assert isinstance(result, str)
    assert mock_api.messages.create.call_count == 2
