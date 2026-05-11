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
