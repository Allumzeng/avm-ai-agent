# AVM AI Agent — Sprint 1: Knowledge Pipeline + Core RAG Agent

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bilingual (zh-TW / EN) AVM Q&A chatbot backed by a Pinecone RAG pipeline auto-synced from Google Drive, served via a Chainlit UI with DPD Taiwan branding and role-calibrated responses.

**Architecture:** Google Drive documents are ingested via LlamaIndex GoogleDriveReader, embedded with Voyage AI `voyage-multilingual-2`, and stored in Pinecone with module metadata. At query time, Claude Sonnet 4.6 uses tool use to retrieve relevant chunks and responds with role-calibrated depth. A FastAPI webhook receiver handles auto re-ingestion when Drive files change. Chainlit provides the chat UI with streaming and password auth.

**Tech Stack:** Python 3.11+, anthropic SDK, llama-index, llama-index-vector-stores-pinecone, llama-index-embeddings-voyageai, llama-index-readers-google, pinecone-client, chainlit, fastapi, uvicorn, google-api-python-client, pytest, pytest-asyncio, httpx

---

## File Structure

```
project root/
├── .env                          # Real secrets (gitignored)
├── .env.example                  # Template — commit this
├── .gitignore
├── requirements.txt
├── pytest.ini
├── config.toml                   # Chainlit config (branding, auth settings)
├── chainlit.md                   # Chainlit welcome screen content
├── app.py                        # Chainlit entry point
├── ingest.py                     # CLI: run full Drive → Pinecone ingestion
├── webhook_server.py             # FastAPI entry point for Drive webhook
├── public/
│   └── dpd_logo.png              # DPD Taiwan logo (provided separately)
├── src/
│   ├── __init__.py
│   ├── config.py                 # Load env vars, single source of truth
│   ├── auth/
│   │   ├── __init__.py
│   │   └── users.py              # User list, password check, role lookup
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embedder.py           # Voyage AI embedding wrapper
│   │   ├── store.py              # Pinecone index connection + upsert/delete
│   │   └── retriever.py          # Query Pinecone → return top-k text chunks
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py             # Google Drive → LlamaIndex Documents
│   │   ├── chunker.py            # SentenceSplitter + metadata tagging
│   │   └── pipeline.py           # Orchestrate: load → chunk → embed → upsert
│   ├── webhook/
│   │   ├── __init__.py
│   │   └── handler.py            # FastAPI router: /webhook endpoint
│   └── agent/
│       ├── __init__.py
│       ├── prompt.py             # AVM system prompt with cache_control
│       ├── tools.py              # Tool definitions + dispatch function
│       └── client.py             # Claude tool-use loop → final text response
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-05-11-avm-agent-design.md
│       └── plans/
│           └── 2026-05-11-avm-agent-sprint1.md
└── tests/
    ├── conftest.py               # Shared fixtures
    ├── test_config.py
    ├── test_users.py
    ├── test_embedder.py
    ├── test_store.py
    ├── test_retriever.py
    ├── test_chunker.py
    ├── test_pipeline.py
    ├── test_webhook.py
    ├── test_prompt.py
    ├── test_tools.py
    └── test_client.py
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create requirements.txt**

```
anthropic>=0.40.0
llama-index>=0.11.0
llama-index-vector-stores-pinecone>=0.2.0
llama-index-embeddings-voyageai>=0.3.0
llama-index-readers-google>=0.3.0
llama-index-core>=0.11.0
pinecone-client>=3.0.0
chainlit>=1.3.0
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
google-api-python-client>=2.120.0
google-auth>=2.29.0
google-auth-httplib2>=0.2.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

- [ ] **Step 2: Create .env.example**

```
ANTHROPIC_API_KEY=your_anthropic_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=avm-knowledge-base
PINECONE_ENVIRONMENT=us-east-1
GOOGLE_DRIVE_FOLDER_ID=1ApsN_DE5qmEgxSF6KQLx-fkG8iNDMOMq
GOOGLE_SERVICE_ACCOUNT_JSON=secrets/service_account.json
VOYAGE_API_KEY=your_voyage_api_key
WEBHOOK_VERIFICATION_TOKEN=generate_a_random_secret_here
```

- [ ] **Step 3: Create .gitignore**

```
.env
secrets/
*.pyc
__pycache__/
.pytest_cache/
.DS_Store
```

- [ ] **Step 4: Create pytest.ini**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 5: Create src/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "avm-knowledge-base")
GOOGLE_DRIVE_FOLDER_ID = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
WEBHOOK_VERIFICATION_TOKEN = os.environ.get("WEBHOOK_VERIFICATION_TOKEN", "")
```

- [ ] **Step 6: Create tests/conftest.py**

```python
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
```

- [ ] **Step 7: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 8: Create .env from template**

Copy `.env.example` to `.env` and fill in your real API keys.

- [ ] **Step 9: Commit**

```bash
git init
git add requirements.txt .env.example .gitignore pytest.ini src/ tests/conftest.py
git commit -m "feat: project scaffold with dependencies and config"
```

---

## Task 2: User Auth

**Files:**
- Create: `src/auth/__init__.py`
- Create: `src/auth/users.py`
- Test: `tests/test_users.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_users.py
from src.auth.users import authenticate, get_role

def test_valid_dpd_user_authenticates():
    user = authenticate("alice", "password123")
    assert user is not None
    assert user["username"] == "alice"

def test_invalid_password_returns_none():
    user = authenticate("alice", "wrongpassword")
    assert user is None

def test_unknown_user_returns_none():
    user = authenticate("nobody", "password")
    assert user is None

def test_dpd_user_has_manager_role():
    assert get_role("alice") == "manager"

def test_nccu_user_has_analyst_role():
    assert get_role("student_chen") == "analyst"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_users.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/auth/users.py**

```python
import hashlib
from typing import Optional

# In production, load this from a database or encrypted file.
# Passwords stored as sha256 hashes.
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

USERS: dict[str, dict] = {
    "alice": {
        "password_hash": _hash("password123"),
        "role": "manager",
        "group": "dpd_taiwan",
    },
    "student_chen": {
        "password_hash": _hash("nccu2026"),
        "role": "analyst",
        "group": "nccu_students",
    },
}

def authenticate(username: str, password: str) -> Optional[dict]:
    user = USERS.get(username)
    if user and user["password_hash"] == _hash(password):
        return {"username": username, "role": user["role"], "group": user["group"]}
    return None

def get_role(username: str) -> Optional[str]:
    user = USERS.get(username)
    return user["role"] if user else None
```

- [ ] **Step 4: Create src/auth/__init__.py** (empty file)

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_users.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add src/auth/ tests/test_users.py
git commit -m "feat: user auth with role lookup"
```

---

## Task 3: Voyage AI Embedder

**Files:**
- Create: `src/rag/__init__.py`
- Create: `src/rag/embedder.py`
- Test: `tests/test_embedder.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_embedder.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_embedder.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/rag/embedder.py**

```python
from llama_index.embeddings.voyageai import VoyageEmbedding

def create_embedder(api_key: str) -> VoyageEmbedding:
    return VoyageEmbedding(
        model_name="voyage-multilingual-2",
        voyage_api_key=api_key,
    )
```

- [ ] **Step 4: Create src/rag/__init__.py** (empty file)

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_embedder.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/rag/ tests/test_embedder.py
git commit -m "feat: voyage ai embedder wrapper"
```

---

## Task 4: Pinecone Store

**Files:**
- Create: `src/rag/store.py`
- Test: `tests/test_store.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_store.py
from unittest.mock import MagicMock, patch, call
from src.rag.store import create_vector_store, upsert_chunks, delete_chunks_by_source

def test_create_vector_store_connects_to_index():
    with patch("src.rag.store.Pinecone") as MockPC:
        mock_pc = MagicMock()
        MockPC.return_value = mock_pc
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_store.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/rag/store.py**

```python
from pinecone import Pinecone, ServerlessSpec
from llama_index.embeddings.voyageai import VoyageEmbedding

def create_vector_store(api_key: str, index_name: str):
    pc = Pinecone(api_key=api_key)
    # Create index if it doesn't exist
    if index_name not in [i.name for i in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=1024,  # voyage-multilingual-2 dimension
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(index_name)

def upsert_chunks(index, embedder: VoyageEmbedding, chunks: list[dict]) -> None:
    vectors = []
    for chunk in chunks:
        embedding = embedder.get_text_embedding(chunk["text"])
        vectors.append({
            "id": chunk["id"],
            "values": embedding,
            "metadata": {**chunk["metadata"], "text": chunk["text"]},
        })
    if vectors:
        index.upsert(vectors=vectors)

def delete_chunks_by_source(index, source_file: str) -> None:
    results = index.query(
        vector=[0.0] * 1024,
        top_k=10000,
        filter={"source_file": {"$eq": source_file}},
        include_metadata=False,
    )
    ids = [match.id for match in results.matches]
    if ids:
        index.delete(ids=ids)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_store.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/rag/store.py tests/test_store.py
git commit -m "feat: pinecone vector store with upsert and delta delete"
```

---

## Task 5: Document Chunker

**Files:**
- Create: `src/ingestion/__init__.py`
- Create: `src/ingestion/chunker.py`
- Test: `tests/test_chunker.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_chunker.py
from unittest.mock import MagicMock
from src.ingestion.chunker import chunk_documents

def test_chunk_produces_list_of_dicts():
    mock_doc = MagicMock()
    mock_doc.text = "作業中心模組是 AVM 的第二個模組。" * 10
    mock_doc.metadata = {
        "file_id": "file_001",
        "mime_type": "application/pdf",
    }
    chunks = chunk_documents([mock_doc])
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all("id" in c for c in chunks)
    assert all("text" in c for c in chunks)
    assert all("metadata" in c for c in chunks)

def test_chunk_metadata_contains_source_file():
    mock_doc = MagicMock()
    mock_doc.text = "The Activity Center Module is Module 2 of AVM." * 10
    mock_doc.metadata = {"file_id": "drive_abc123", "mime_type": "text/plain"}
    chunks = chunk_documents([mock_doc])
    assert all(c["metadata"]["source_file"] == "drive_abc123" for c in chunks)

def test_chunk_detects_chinese_language():
    mock_doc = MagicMock()
    mock_doc.text = "作業價值管理是由吳安妮教授研發的管理制度。" * 10
    mock_doc.metadata = {"file_id": "file_zh", "mime_type": "text/plain"}
    chunks = chunk_documents([mock_doc])
    assert all(c["metadata"]["language"] == "zh-TW" for c in chunks)

def test_chunk_detects_english_language():
    mock_doc = MagicMock()
    mock_doc.text = "Activity Value Management is developed by Professor Ann Wu." * 10
    mock_doc.metadata = {"file_id": "file_en", "mime_type": "text/plain"}
    chunks = chunk_documents([mock_doc])
    assert all(c["metadata"]["language"] == "en" for c in chunks)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_chunker.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/ingestion/chunker.py**

```python
import re
import uuid
from llama_index.core.node_parser import SentenceSplitter

_SPLITTER = SentenceSplitter(chunk_size=512, chunk_overlap=50)

_CJK_PATTERN = re.compile(r'[一-鿿㐀-䶿]')

def _detect_language(text: str) -> str:
    cjk_chars = len(_CJK_PATTERN.findall(text))
    return "zh-TW" if cjk_chars / max(len(text), 1) > 0.1 else "en"

def chunk_documents(documents: list) -> list[dict]:
    nodes = _SPLITTER.get_nodes_from_documents(documents)
    chunks = []
    for node in nodes:
        source_file = node.metadata.get("file_id", "unknown")
        text = node.get_content()
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": text,
            "metadata": {
                "source_file": source_file,
                "language": _detect_language(text),
                "doc_type": node.metadata.get("mime_type", "unknown"),
                "module": node.metadata.get("avm_module", 0),
            },
        })
    return chunks
```

- [ ] **Step 4: Create src/ingestion/__init__.py** (empty file)

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_chunker.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add src/ingestion/ tests/test_chunker.py
git commit -m "feat: document chunker with bilingual language detection"
```

---

## Task 6: Google Drive Loader

**Files:**
- Create: `src/ingestion/loader.py`
- Test: `tests/test_pipeline.py` (loader tested as part of pipeline)

- [ ] **Step 1: Implement src/ingestion/loader.py**

```python
from llama_index.readers.google import GoogleDriveReader

def create_loader(service_account_json_path: str) -> GoogleDriveReader:
    return GoogleDriveReader(service_account_key_path=service_account_json_path)

def load_folder(loader: GoogleDriveReader, folder_id: str) -> list:
    return loader.load_data(folder_id=folder_id)

def load_file(loader: GoogleDriveReader, file_id: str) -> list:
    return loader.load_data(file_ids=[file_id])
```

- [ ] **Step 2: Commit**

```bash
git add src/ingestion/loader.py
git commit -m "feat: google drive loader wrapper"
```

---

## Task 7: Ingestion Pipeline

**Files:**
- Create: `src/ingestion/pipeline.py`
- Create: `ingest.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py
from unittest.mock import MagicMock, patch
from src.ingestion.pipeline import run_full_ingestion, run_file_ingestion

def test_full_ingestion_loads_chunks_and_upserts():
    mock_loader = MagicMock()
    mock_doc = MagicMock()
    mock_doc.text = "AVM Module 2 content." * 20
    mock_doc.metadata = {"file_id": "file_001", "mime_type": "text/plain"}
    mock_loader.load_data.return_value = [mock_doc]
    mock_index = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    run_full_ingestion(
        loader=mock_loader,
        folder_id="folder_abc",
        pinecone_index=mock_index,
        embedder=mock_embedder,
    )

    mock_loader.load_data.assert_called_once_with(folder_id="folder_abc")
    assert mock_index.upsert.called

def test_file_ingestion_deletes_old_chunks_first():
    mock_loader = MagicMock()
    mock_doc = MagicMock()
    mock_doc.text = "Updated AVM content." * 20
    mock_doc.metadata = {"file_id": "file_001", "mime_type": "text/plain"}
    mock_loader.load_data.return_value = [mock_doc]
    mock_index = MagicMock()
    mock_index.query.return_value = MagicMock(matches=[])
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    run_file_ingestion(
        loader=mock_loader,
        file_id="file_001",
        pinecone_index=mock_index,
        embedder=mock_embedder,
    )

    # delete called before upsert
    mock_index.query.assert_called_once()
    assert mock_index.upsert.called
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/ingestion/pipeline.py**

```python
from src.ingestion.loader import load_folder, load_file
from src.ingestion.chunker import chunk_documents
from src.rag.store import upsert_chunks, delete_chunks_by_source

def run_full_ingestion(loader, folder_id: str, pinecone_index, embedder) -> int:
    documents = load_folder(loader, folder_id)
    chunks = chunk_documents(documents)
    upsert_chunks(pinecone_index, embedder, chunks)
    return len(chunks)

def run_file_ingestion(loader, file_id: str, pinecone_index, embedder) -> int:
    delete_chunks_by_source(pinecone_index, file_id)
    documents = load_file(loader, file_id)
    chunks = chunk_documents(documents)
    upsert_chunks(pinecone_index, embedder, chunks)
    return len(chunks)
```

- [ ] **Step 4: Create ingest.py (CLI)**

```python
#!/usr/bin/env python3
"""Run full Google Drive → Pinecone ingestion."""
from src.config import (
    PINECONE_API_KEY, PINECONE_INDEX_NAME,
    GOOGLE_DRIVE_FOLDER_ID, GOOGLE_SERVICE_ACCOUNT_JSON,
    VOYAGE_API_KEY,
)
from src.rag.embedder import create_embedder
from src.rag.store import create_vector_store
from src.ingestion.loader import create_loader
from src.ingestion.pipeline import run_full_ingestion

if __name__ == "__main__":
    print("Connecting to Pinecone...")
    index = create_vector_store(PINECONE_API_KEY, PINECONE_INDEX_NAME)
    embedder = create_embedder(VOYAGE_API_KEY)
    loader = create_loader(GOOGLE_SERVICE_ACCOUNT_JSON)

    print(f"Ingesting from Google Drive folder: {GOOGLE_DRIVE_FOLDER_ID}")
    count = run_full_ingestion(loader, GOOGLE_DRIVE_FOLDER_ID, index, embedder)
    print(f"Done. {count} chunks upserted to Pinecone.")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_pipeline.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Smoke test ingestion against real services**

```bash
python ingest.py
```

Expected output:
```
Connecting to Pinecone...
Ingesting from Google Drive folder: 1ApsN_DE5qmEgxSF6KQLx-fkG8iNDMOMq
Done. N chunks upserted to Pinecone.
```

Verify in Pinecone console: index `avm-knowledge-base` has vectors with metadata fields `source_file`, `language`, `module`.

- [ ] **Step 7: Commit**

```bash
git add src/ingestion/pipeline.py ingest.py tests/test_pipeline.py
git commit -m "feat: ingestion pipeline with cli runner"
```

---

## Task 8: AVM Retriever

**Files:**
- Create: `src/rag/retriever.py`
- Test: `tests/test_retriever.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_retriever.py
from unittest.mock import MagicMock
from src.rag.retriever import retrieve_chunks

def test_retrieve_returns_list_of_strings():
    mock_index = MagicMock()
    mock_match = MagicMock()
    mock_match.metadata = {"text": "作業中心模組的標準成本計算方式。"}
    mock_index.query.return_value = MagicMock(matches=[mock_match])
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    results = retrieve_chunks(mock_index, mock_embedder, "標準成本")

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0] == "作業中心模組的標準成本計算方式。"

def test_retrieve_with_module_filter_passes_filter():
    mock_index = MagicMock()
    mock_index.query.return_value = MagicMock(matches=[])
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    retrieve_chunks(mock_index, mock_embedder, "capacity", module_filter=2)

    call_kwargs = mock_index.query.call_args.kwargs
    assert call_kwargs["filter"] == {"module": {"$eq": 2}}

def test_retrieve_without_module_filter_has_no_filter():
    mock_index = MagicMock()
    mock_index.query.return_value = MagicMock(matches=[])
    mock_embedder = MagicMock()
    mock_embedder.get_text_embedding.return_value = [0.1] * 1024

    retrieve_chunks(mock_index, mock_embedder, "AVM overview")

    call_kwargs = mock_index.query.call_args.kwargs
    assert "filter" not in call_kwargs or call_kwargs.get("filter") is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_retriever.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/rag/retriever.py**

```python
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
    return [match.metadata["text"] for match in results.matches if "text" in match.metadata]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_retriever.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/rag/retriever.py tests/test_retriever.py
git commit -m "feat: pinecone retriever with optional module filter"
```

---

## Task 9: AVM System Prompt

**Files:**
- Create: `src/agent/__init__.py`
- Create: `src/agent/prompt.py`
- Test: `tests/test_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompt.py
from src.agent.prompt import build_system_prompt

def test_system_prompt_returns_list_of_blocks():
    prompt = build_system_prompt("manager")
    assert isinstance(prompt, list)
    assert len(prompt) >= 1

def test_first_block_has_cache_control():
    prompt = build_system_prompt("analyst")
    assert prompt[0]["type"] == "text"
    assert prompt[0].get("cache_control") == {"type": "ephemeral"}

def test_role_block_mentions_role():
    prompt = build_system_prompt("executive")
    role_block = prompt[-1]
    assert "executive" in role_block["text"].lower()

def test_prompt_contains_avm_core_content():
    prompt = build_system_prompt("analyst")
    full_text = " ".join(b["text"] for b in prompt)
    assert "Activity Value Management" in full_text or "AVM" in full_text
    assert "Module" in full_text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_prompt.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/agent/prompt.py**

```python
_AVM_CORE_KNOWLEDGE = """
You are an expert AI assistant specializing in Activity Value Management (AVM), developed by Professor Ann Wu over 40 years of research and 36 years of Taiwan implementation experience.

## AVM Core Framework

AVM treats "activities" as the management cell linking cause information (process, time, quality, value) to result information (cost, profit, carbon emissions). It helps organizations "earn management profits" (賺管理財) by understanding both causes and results of business operations.

### The Four AVM Modules

**Module 1 — Resource Module (投入面)**
- Reclassifies financial accounting "expenses" into management "resources"
- Key distinction: controllable resources (部門可自行管理) vs. uncontrollable resources (總部或支援單位的分攤)

**Module 2 — Activity Center Module (營運面 — 事先規劃)**
- Defines activity executors (人員 or 機器) and their normal capacity (正常產能 / 標準時間)
- Calculates unit standard cost (單位標準成本) — e.g., cost per minute — as the pricing competitiveness baseline

**Module 3 — Activity Module (營運面 — 實際執行)**
- Collects actual capacity (實際產能 / 實際時間) per activity
- Tags each activity with five attribute types (see below)
- Compares normal vs. actual capacity → surfaces idle (閒置) or over-utilized (超用) capacity and their hidden costs

**Module 4 — Value Object Module (結果面)**
- Assigns costs to final value objects: products, customers, employees, ESG recipients
- Analyzes long-term value vs. short-term profit
- Identifies whether large customers are truly profitable after full cost allocation

### Five Activity Attribute Types (Module 3)

1. **Quality attributes**: preventive, appraisal, internal failure, external failure activities
2. **Capacity attributes**: productive, non-productive, indirect productive, idle activities
3. **Value-added attributes**: value-added, non-value-added, necessary activities
4. **Customer service attributes**: customer development, service delivery, after-sales, customer retention
5. **ESG attributes**: environmental (E), social (S), governance (G) activities

### Seven AVM Theoretical Innovations

1. Strategy-guided design (BSC/mission/vision drives AVM design)
2. Controllable vs. uncontrollable resource distinction (ensures fair performance evaluation)
3. Capacity variance analysis (quantifies idle and over-utilized capacity costs)
4. Five activity attribute types (professional labels for precision management)
5. Whole value chain cost (R&D, design, manufacturing, marketing, administration)
6. Hidden cost consideration (capital cost, risk cost, inventory holding cost)
7. Cause-and-effect integration (produces truly decision-relevant management information)

### C-PVM (Carbon Process Value Management)
Extends AVM logic to calculate product carbon footprints at the activity level, linking carbon emissions to financial data to address greenwashing concerns.

## Language Behavior
- Detect the language of the user's message and respond in the same language
- If the message mixes Traditional Chinese and English, default to Traditional Chinese
- Key AVM terms may be shown in both languages: e.g., 作業中心模組 (Activity Center Module)

## Response Calibration
Calibrate response depth and verbosity to match the specificity and complexity of the user's query. Use the user's role only as a baseline default:
- Executive (總經理): strategic summaries by default — highlight decisions and financial impact
- Manager (中階主管): department-level analysis by default — include activity-level details
- Analyst / Student: full module-level detail by default — include formulas and methodology
A simple one-line question gets a focused answer. A multi-part question with context and constraints gets a thorough breakdown, regardless of role.
""".strip()

def build_system_prompt(role: str) -> list[dict]:
    return [
        {
            "type": "text",
            "text": _AVM_CORE_KNOWLEDGE,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": f"The current user's role is: {role}. Apply the response calibration guidelines above with this role as the baseline default.",
        },
    ]
```

- [ ] **Step 4: Create src/agent/__init__.py** (empty file)

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_prompt.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add src/agent/ tests/test_prompt.py
git commit -m "feat: avm system prompt with anthropic prompt caching"
```

---

## Task 10: Tool Definitions

**Files:**
- Create: `src/agent/tools.py`
- Test: `tests/test_tools.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tools.py
from src.agent.tools import TOOLS, dispatch_tool

def test_tools_list_contains_search_avm_knowledge():
    names = [t["name"] for t in TOOLS]
    assert "search_avm_knowledge" in names

def test_tools_list_contains_get_user_context():
    names = [t["name"] for t in TOOLS]
    assert "get_user_context" in names

def test_search_tool_has_required_query_param():
    tool = next(t for t in TOOLS if t["name"] == "search_avm_knowledge")
    assert "query" in tool["input_schema"]["properties"]
    assert "query" in tool["input_schema"]["required"]

def test_search_tool_module_filter_is_optional():
    tool = next(t for t in TOOLS if t["name"] == "search_avm_knowledge")
    assert "module_filter" in tool["input_schema"]["properties"]
    assert "module_filter" not in tool["input_schema"].get("required", [])

def test_dispatch_search_calls_retriever():
    mock_retriever = lambda q, module_filter=None: [f"result for {q}"]
    result = dispatch_tool(
        "search_avm_knowledge",
        {"query": "idle capacity"},
        retriever=mock_retriever,
        role="analyst",
    )
    assert "result for idle capacity" in result

def test_dispatch_get_user_context_returns_role():
    result = dispatch_tool(
        "get_user_context",
        {},
        retriever=lambda q, **kw: [],
        role="manager",
    )
    assert "manager" in result
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_tools.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/agent/tools.py**

```python
from typing import Callable, Optional

TOOLS = [
    {
        "name": "search_avm_knowledge",
        "description": (
            "Search the AVM knowledge base for relevant information. "
            "Use this for any question about AVM concepts, modules, attributes, formulas, or methodology. "
            "Optionally filter by AVM module number (1=Resource, 2=ActivityCenter, 3=Activity, 4=ValueObject)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query in the user's language.",
                },
                "module_filter": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4,
                    "description": "Optional AVM module number to restrict search scope.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_user_context",
        "description": "Get the current user's role for calibrating response depth.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

def dispatch_tool(
    name: str,
    input_data: dict,
    retriever: Callable,
    role: str,
) -> str:
    if name == "search_avm_knowledge":
        query = input_data["query"]
        module_filter = input_data.get("module_filter")
        chunks = retriever(query, module_filter=module_filter)
        if not chunks:
            return "No relevant AVM knowledge found for this query."
        return "\n\n---\n\n".join(chunks)

    if name == "get_user_context":
        return f"Current user role: {role}"

    return f"Unknown tool: {name}"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_tools.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/agent/tools.py tests/test_tools.py
git commit -m "feat: claude tool definitions and dispatcher"
```

---

## Task 11: Claude Agent Client

**Files:**
- Create: `src/agent/client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_client.py
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
    client = _make_client()
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = "AVM 的四大模組分別是資源、作業中心、作業與價值標的模組。"
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [mock_text_block]

    with patch("src.agent.client.anthropic.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_response

        client = _make_client()
        result = client.get_response(
            history=[{"role": "user", "content": "AVM 有哪四大模組？"}],
            role="analyst",
        )

    assert isinstance(result, str)
    assert len(result) > 0

def test_get_response_handles_tool_use_then_end_turn():
    client = _make_client()

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
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.create.side_effect = [first_response, second_response]

        client = _make_client()
        result = client.get_response(
            history=[{"role": "user", "content": "What is idle capacity cost?"}],
            role="analyst",
        )

    assert isinstance(result, str)
    assert mock_client.messages.create.call_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_client.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/agent/client.py**

```python
import anthropic
from src.agent.prompt import build_system_prompt
from src.agent.tools import TOOLS, dispatch_tool
from src.rag.retriever import retrieve_chunks

class AVMAgentClient:
    def __init__(self, api_key: str, pinecone_index, embedder):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.pinecone_index = pinecone_index
        self.embedder = embedder

    def _retriever(self, query: str, module_filter=None) -> list[str]:
        return retrieve_chunks(
            self.pinecone_index,
            self.embedder,
            query,
            module_filter=module_filter,
        )

    def get_response(self, history: list[dict], role: str) -> str:
        system = build_system_prompt(role)
        messages = list(history)

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                messages=messages,
                tools=TOOLS,
            )

            if response.stop_reason == "end_turn":
                return next(
                    (b.text for b in response.content if b.type == "text"),
                    "",
                )

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_tool(
                            block.name,
                            block.input,
                            retriever=self._retriever,
                            role=role,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_client.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/agent/client.py tests/test_client.py
git commit -m "feat: claude agent client with tool-use loop"
```

---

## Task 12: Google Drive Webhook

**Files:**
- Create: `src/webhook/__init__.py`
- Create: `src/webhook/handler.py`
- Create: `webhook_server.py`
- Test: `tests/test_webhook.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_webhook.py
import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

def test_webhook_returns_200_on_valid_notification():
    with patch("src.webhook.handler.run_file_ingestion") as mock_ingest, \
         patch("src.webhook.handler.PINECONE_INDEX", MagicMock()), \
         patch("src.webhook.handler.EMBEDDER", MagicMock()), \
         patch("src.webhook.handler.LOADER", MagicMock()):
        from src.webhook.handler import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
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
    with patch("src.webhook.handler.run_file_ingestion") as mock_ingest, \
         patch("src.webhook.handler.PINECONE_INDEX", MagicMock()), \
         patch("src.webhook.handler.EMBEDDER", MagicMock()), \
         patch("src.webhook.handler.LOADER", MagicMock()):
        from src.webhook.handler import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_webhook.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/webhook/handler.py**

```python
from fastapi import APIRouter, Request, BackgroundTasks
from src.config import (
    PINECONE_API_KEY, PINECONE_INDEX_NAME,
    GOOGLE_SERVICE_ACCOUNT_JSON, VOYAGE_API_KEY,
)
from src.rag.embedder import create_embedder
from src.rag.store import create_vector_store
from src.ingestion.loader import create_loader
from src.ingestion.pipeline import run_file_ingestion

router = APIRouter()

# Initialized once at module load — reused across requests
PINECONE_INDEX = create_vector_store(PINECONE_API_KEY, PINECONE_INDEX_NAME)
EMBEDDER = create_embedder(VOYAGE_API_KEY)
LOADER = create_loader(GOOGLE_SERVICE_ACCOUNT_JSON)

@router.post("/webhook")
async def google_drive_webhook(request: Request, background_tasks: BackgroundTasks):
    state = request.headers.get("X-Goog-Resource-State", "")
    file_id = request.headers.get("X-Goog-Resource-Id", "")

    # "sync" is the initial confirmation ping — ignore it
    if state in ("sync", "") or not file_id:
        return {"status": "ignored"}

    background_tasks.add_task(
        run_file_ingestion,
        loader=LOADER,
        file_id=file_id,
        pinecone_index=PINECONE_INDEX,
        embedder=EMBEDDER,
    )
    return {"status": "queued", "file_id": file_id}
```

- [ ] **Step 4: Create webhook_server.py**

```python
import uvicorn
from fastapi import FastAPI
from src.webhook.handler import router

app = FastAPI(title="AVM Webhook Server")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

- [ ] **Step 5: Create src/webhook/__init__.py** (empty file)

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_webhook.py -v
```

Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add src/webhook/ webhook_server.py tests/test_webhook.py
git commit -m "feat: google drive webhook for auto re-ingestion"
```

---

## Task 13: Chainlit App + Branding

**Files:**
- Create: `app.py`
- Create: `config.toml`
- Create: `chainlit.md`

- [ ] **Step 1: Create config.toml**

```toml
[project]
enable_telemetry = false

[UI]
name = "AVM AI Agent"
logo = "public/dpd_logo.png"
favicon = "public/dpd_logo.png"
default_collapse_content = true
hide_cot = false

[meta]
generated_by = "1.3.0"

[auth]
require_login = true
```

- [ ] **Step 2: Create chainlit.md (welcome screen)**

```markdown
# 歡迎使用 AVM AI Agent / Welcome to AVM AI Agent

本 Agent 由 DPD Taiwan 與國立政治大學合作開發，基於吳安妮教授的作業價值管理 (AVM) 理論。

This agent is developed in collaboration between DPD Taiwan and NCCU, based on Professor Ann Wu's Activity Value Management (AVM) framework.

## 您可以問我 / You can ask me about:
- AVM 四大模組的概念與計算方式
- 作業屬性分類（品質、產能、附加價值、顧客服務、ESG）
- 如何識別無附加價值作業與閒置產能
- 顧客與產品的長期獲利分析
- C-PVM 碳排放管理

## 指令 / Commands:
- 輸入任何問題以開始 Q&A
- 輸入「開始設置嚮導」啟動 AVM Setup Wizard *(Sprint 2)*
- 輸入「診斷問題」啟動 Diagnosis Wizard *(Sprint 2)*
- 上傳 Excel/CSV 以產生報表 *(Sprint 3)*
```

- [ ] **Step 3: Create app.py**

```python
import chainlit as cl
from src.config import (
    ANTHROPIC_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME,
    GOOGLE_SERVICE_ACCOUNT_JSON, VOYAGE_API_KEY,
)
from src.auth.users import authenticate
from src.rag.embedder import create_embedder
from src.rag.store import create_vector_store
from src.agent.client import AVMAgentClient
from typing import Optional

# Shared resources — initialized once
_pinecone_index = create_vector_store(PINECONE_API_KEY, PINECONE_INDEX_NAME)
_embedder = create_embedder(VOYAGE_API_KEY)

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    user = authenticate(username, password)
    if user:
        return cl.User(
            identifier=username,
            metadata={"role": user["role"], "group": user["group"]},
        )
    return None

@cl.on_chat_start
async def on_chat_start():
    user = cl.user_session.get("user")
    role = user.metadata.get("role", "analyst") if user else "analyst"
    cl.user_session.set("role", role)
    cl.user_session.set("history", [])
    cl.user_session.set(
        "agent",
        AVMAgentClient(
            api_key=ANTHROPIC_API_KEY,
            pinecone_index=_pinecone_index,
            embedder=_embedder,
        ),
    )

@cl.on_message
async def on_message(message: cl.Message):
    role: str = cl.user_session.get("role", "analyst")
    history: list = cl.user_session.get("history", [])
    agent: AVMAgentClient = cl.user_session.get("agent")

    history.append({"role": "user", "content": message.content})

    thinking_msg = cl.Message(content="")
    await thinking_msg.send()

    response_text = agent.get_response(history=history, role=role)

    thinking_msg.content = response_text
    await thinking_msg.update()

    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)
```

- [ ] **Step 4: Place DPD Taiwan logo**

Copy the DPD Taiwan logo PNG file to `public/dpd_logo.png`.

If the logo is not yet available, create a placeholder:
```bash
mkdir -p public
# Place dpd_logo.png in public/ when available from DPD Taiwan
```

- [ ] **Step 5: Run the Chainlit app locally**

```bash
chainlit run app.py --port 8000
```

Expected: Browser opens at `http://localhost:8000`, shows login page with AVM branding.

- [ ] **Step 6: Verify login**

Log in with a user from `src/auth/users.py` (e.g., username: `alice`, password: `password123`).

Expected: Welcome screen shows, chat interface loads.

- [ ] **Step 7: Smoke test full Q&A flow**

Type: `What is idle capacity cost?`

Expected: Claude retrieves relevant Module 2/3 chunks and responds with a clear explanation.

Type: `什麼是無附加價值作業？`

Expected: Claude responds in Traditional Chinese with Module 3 attribute explanation.

- [ ] **Step 8: Commit**

```bash
git add app.py config.toml chainlit.md public/
git commit -m "feat: chainlit app with dpd taiwan branding and role-aware chat"
```

---

## Task 14: Full Test Suite

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass. Minimum passing: `test_users`, `test_embedder`, `test_store`, `test_retriever`, `test_chunker`, `test_pipeline`, `test_webhook`, `test_prompt`, `test_tools`, `test_client`.

- [ ] **Step 2: Verify no import errors across all modules**

```bash
python -c "from src.agent.client import AVMAgentClient; from src.webhook.handler import router; print('All imports OK')"
```

Expected: `All imports OK`

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "chore: sprint 1 complete — bilingual AVM Q&A chatbot with pinecone rag"
```

---

## Verification Checklist

After Sprint 1 is complete, verify the following manually:

- [ ] `python ingest.py` completes without errors; Pinecone console shows vectors with correct metadata
- [ ] Modifying a file in Google Drive folder triggers re-ingestion within 30 seconds (requires webhook server running and public HTTPS URL)
- [ ] Login with `alice` / `password123` → reaches chat interface
- [ ] Login with wrong password → rejected
- [ ] Ask "What is idle capacity cost?" → response references Module 2/3 concepts
- [ ] Ask "什麼是無附加價值作業？" → response in Traditional Chinese
- [ ] Ask a one-line question as Executive → get a concise summary
- [ ] Ask a detailed multi-part question as Executive → get a thorough breakdown
- [ ] DPD Taiwan logo visible in Chainlit sidebar

---

## Sprint 2 Preview

Sprint 2 plan will cover:
- `src/wizard/setup.py` — 4-module AVM setup wizard state machine
- `src/wizard/diagnosis.py` — symptom-driven diagnosis wizard
- Session persistence across browser refreshes
- New Chainlit commands: "開始設置嚮導" / "診斷問題"
