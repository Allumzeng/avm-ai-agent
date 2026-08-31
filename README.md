# AVM AI Agent

A bilingual (Traditional Chinese / English) AI agent built for **DPD Taiwan** and collaborating **National Chengchi University (NCCU)** students, based on Professor Ann Wu's **Activity Value Management (AVM)** framework. It answers AVM questions with retrieval-augmented generation over a curated knowledge base, walks users through guided setup/diagnosis wizards, and generates structured management reports from uploaded Excel/CSV data.

Access is restricted to DPD Taiwan staff and NCCU students working with DPD Taiwan.

## Features

- **Conversational Q&A** — Ask free-form questions about AVM's four modules, activity attribute classification (quality, capacity, value-added, customer service, ESG), idle capacity, long-term customer/product profitability, and C-PVM carbon management. Answers are grounded in a Pinecone knowledge base via RAG, with responses depth-calibrated to the user's role (executive / manager / analyst) and to query complexity.
- **Guided Wizards** — Step-by-step AVM setup (sequential 4-module implementation) and symptom-driven diagnosis (e.g. "we're losing money" → drills into the relevant module) with pausable, resumable session state.
- **Analysis & Reporting** — Upload an Excel/CSV file to generate one of four report types: profitability, capacity analysis, activity attribute dashboard, and value object (long-term vs. short-term value) reports, then drill down on results via chat.
- **Auto-syncing knowledge base** — A Google Drive folder of AVM source material is ingested, chunked, and embedded into Pinecone; a webhook keeps the index in sync as files are added or changed in Drive.
- **Role-based auth** — Username/password login (plus optional "Sign in with Google" OAuth) mapped to roles (`executive`, `manager`, `analyst`) and groups (`dpd_taiwan`, `nccu_students`) that gate default response depth.

## Architecture

| Layer | Technology |
|---|---|
| Intelligence | Claude (Anthropic SDK) — Sonnet for Q&A/wizard flows, Opus for report analysis |
| RAG / Knowledge | LlamaIndex + Pinecone |
| Embeddings | Voyage AI `voyage-multilingual-2` (bilingual zh-TW + EN) |
| Ingestion | LlamaIndex `GoogleDriveReader` + FastAPI webhook (auto re-sync) |
| Chat UI | [Chainlit](https://github.com/Chainlit/chainlit) |
| Backend | FastAPI (webhook receiver) |
| Proxy | nginx + Let's Encrypt |

See [docs/superpowers/specs/2026-05-11-avm-agent-design.md](docs/superpowers/specs/2026-05-11-avm-agent-design.md) for the full design spec and [docs/superpowers/plans/](docs/superpowers/plans/) for the sprint-by-sprint implementation plans.

### Project layout

```
app.py                  # Chainlit entrypoint: auth, message routing, session state
webhook_server.py       # FastAPI app exposing the Drive-sync webhook
ingest.py               # One-shot full Google Drive -> Pinecone ingestion
manage_users.py         # CLI for adding/removing/listing local users
src/
  agent/                # Core Q&A agent (system prompt, tools, Claude client)
  auth/                 # Local username/password auth + Google OAuth resolution
  ingestion/             # Drive loader, chunker, ingestion pipeline
  rag/                   # Embedder, Pinecone vector store, retriever
  reporting/             # Report intent detection, upload parsing, report engine
  wizard/                 # Wizard intent detection, state machine, prompts
deploy/                 # systemd unit files, nginx config, VPS setup script
docs/                   # Design spec, sprint plans, known issues
tests/                  # pytest suite (one file per module, mirrors src/)
```

## Prerequisites

- Python 3.11+
- Anthropic API key
- Pinecone account + index
- Voyage AI API key
- A Google Cloud service account with read access to the AVM Drive folder (for knowledge ingestion)

## Setup

1. **Clone and install dependencies**

   ```bash
   git clone https://github.com/Allumzeng/avm-ai-agent.git
   cd avm-ai-agent
   python -m venv venv
   source venv/bin/activate   # venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Fill in `.env`:

   | Variable | Purpose |
   |---|---|
   | `ANTHROPIC_API_KEY` | Claude API access |
   | `CHAINLIT_AUTH_SECRET` | Session signing secret — generate with `chainlit create-secret` |
   | `PINECONE_API_KEY` / `PINECONE_INDEX_NAME` | Vector store |
   | `GOOGLE_DRIVE_FOLDER_ID` / `GOOGLE_SERVICE_ACCOUNT_JSON` | Knowledge base source (path to a service-account JSON under `secrets/`) |
   | `VOYAGE_API_KEY` | Embeddings |
   | `WEBHOOK_VERIFICATION_TOKEN` | Verifies incoming Drive webhook pushes |
   | `OAUTH_GOOGLE_CLIENT_ID` / `OAUTH_GOOGLE_CLIENT_SECRET` | Optional — enables "Sign in with Google" |
   | `CHAINLIT_URL` | Public base URL (needed for OAuth callback) |

3. **Set up local users**

   ```bash
   cp users.json.example users.json
   python manage_users.py add <username> <password> <role> <group>
   # role:  executive | manager | analyst
   # group: dpd_taiwan | nccu_students
   ```

4. **Ingest the knowledge base**

   ```bash
   python ingest.py
   ```

   This pulls documents from the configured Google Drive folder, chunks and embeds them, and upserts them into Pinecone.

## Running locally

```bash
chainlit run app.py -w
```

To also run the Drive-sync webhook receiver (needed for auto re-ingestion when Drive files change):

```bash
python webhook_server.py
```

## Testing

```bash
pytest
```

## Deployment

`deploy/` contains everything needed to stand the app up on a fresh Ubuntu VPS behind nginx + Let's Encrypt:

```bash
bash deploy/setup.sh https://github.com/Allumzeng/avm-ai-agent.git
```

This provisions system packages, clones the repo, sets up a Python venv, installs systemd services (`avm-chainlit`, `avm-webhook`) from `deploy/avm-chainlit.service` / `deploy/avm-webhook.service`, configures nginx (`deploy/nginx.conf`), and obtains a TLS certificate. Secrets (`.env`, `secrets/`, logo) are copied over manually afterward — see the script's final output for the exact steps.

## Known issues

See [docs/known-issues.md](docs/known-issues.md) — currently tracks a module-metadata parsing bug in the ingestion pipeline (fixed for future ingests, not retroactively backfilled) and a handful of Drive files skipped during the last full ingest due to permissions.

## License

Internal project — not licensed for external use. Solely developed by Allum Zeng (Strategic PM, DPD Taiwan Digital Transformation Center), based on Professor Ann Wu's AVM framework.
