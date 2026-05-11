import pytest

@pytest.fixture
def sample_chunks():
    return [
        {
            "id": "chunk_001",
            "text": "作業中心模組定義作業執行者並計算標準成本。",
            "metadata": {"module": 2, "language": "zh-TW", "source_file": "file_001"},
        },
        {
            "id": "chunk_002",
            "text": "The Activity Center Module defines activity executors and calculates unit standard cost.",
            "metadata": {"module": 2, "language": "en", "source_file": "file_001"},
        },
    ]
