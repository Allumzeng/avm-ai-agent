import os
import pytest

# Set dummy env vars before any test module imports src.config (which reads them at module level).
# Uses setdefault so real values in the environment are not overridden.
for _key, _val in {
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "PINECONE_API_KEY": "test-pinecone-key",
    "GOOGLE_DRIVE_FOLDER_ID": "test-folder-id",
    "GOOGLE_SERVICE_ACCOUNT_JSON": "{}",
    "VOYAGE_API_KEY": "test-voyage-key",
}.items():
    os.environ.setdefault(_key, _val)

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
