import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in your API keys."
        )
    return value

ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
PINECONE_API_KEY = _require("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "avm-knowledge-base")
GOOGLE_DRIVE_FOLDER_ID = _require("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = _require("GOOGLE_SERVICE_ACCOUNT_JSON")
VOYAGE_API_KEY = _require("VOYAGE_API_KEY")
WEBHOOK_VERIFICATION_TOKEN = os.environ.get("WEBHOOK_VERIFICATION_TOKEN", "")
