from llama_index.core.schema import Document
from src.ingestion.chunker import chunk_documents


def test_chunk_produces_list_of_dicts():
    doc = Document(
        text="作業中心模組是 AVM 的第二個模組。" * 10,
        metadata={
            "file_id": "file_001",
            "mime_type": "application/pdf",
        },
    )
    chunks = chunk_documents([doc])
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all("id" in c for c in chunks)
    assert all("text" in c for c in chunks)
    assert all("metadata" in c for c in chunks)


def test_chunk_metadata_contains_source_file():
    doc = Document(
        text="The Activity Center Module is Module 2 of AVM." * 10,
        metadata={"file_id": "drive_abc123", "mime_type": "text/plain"},
    )
    chunks = chunk_documents([doc])
    assert all(c["metadata"]["source_file"] == "drive_abc123" for c in chunks)


def test_chunk_detects_chinese_language():
    doc = Document(
        text="作業價值管理是由吳安妮教授研發的管理制度。" * 10,
        metadata={"file_id": "file_zh", "mime_type": "text/plain"},
    )
    chunks = chunk_documents([doc])
    assert all(c["metadata"]["language"] == "zh-TW" for c in chunks)


def test_chunk_detects_english_language():
    doc = Document(
        text="Activity Value Management is developed by Professor Ann Wu." * 10,
        metadata={"file_id": "file_en", "mime_type": "text/plain"},
    )
    chunks = chunk_documents([doc])
    assert all(c["metadata"]["language"] == "en" for c in chunks)
