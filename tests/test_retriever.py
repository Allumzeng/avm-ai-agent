from src.rag.retriever import retrieve_chunks


def test_retrieve_returns_list_of_strings():
    mock_index = __import__('unittest.mock', fromlist=['MagicMock']).MagicMock()
    mock_match = __import__('unittest.mock', fromlist=['MagicMock']).MagicMock()
    mock_match.metadata = {"text": "作業中心模組的標準成本計算方式。"}
    mock_index.query.return_value = __import__('unittest.mock', fromlist=['MagicMock']).MagicMock(matches=[mock_match])
    mock_embedder = __import__('unittest.mock', fromlist=['MagicMock']).MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    results = retrieve_chunks(mock_index, mock_embedder, "標準成本")

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0] == "作業中心模組的標準成本計算方式。"


def test_retrieve_with_module_filter_passes_filter():
    from unittest.mock import MagicMock
    mock_index = MagicMock()
    mock_index.query.return_value = MagicMock(matches=[])
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    retrieve_chunks(mock_index, mock_embedder, "capacity", module_filter=2)

    call_kwargs = mock_index.query.call_args.kwargs
    assert call_kwargs["filter"] == {"module": {"$eq": 2}}


def test_retrieve_without_module_filter_has_no_filter():
    from unittest.mock import MagicMock
    mock_index = MagicMock()
    mock_index.query.return_value = MagicMock(matches=[])
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    retrieve_chunks(mock_index, mock_embedder, "AVM overview")

    call_kwargs = mock_index.query.call_args.kwargs
    assert "filter" not in call_kwargs or call_kwargs.get("filter") is None


def test_retrieve_skips_chunks_without_text_metadata():
    from unittest.mock import MagicMock
    mock_index = MagicMock()
    good_match = MagicMock()
    good_match.metadata = {"text": "Valid AVM content."}
    bad_match = MagicMock()
    bad_match.metadata = {}  # no "text" key
    mock_index.query.return_value = MagicMock(matches=[good_match, bad_match])
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    results = retrieve_chunks(mock_index, mock_embedder, "AVM")

    assert len(results) == 1
    assert results[0] == "Valid AVM content."
