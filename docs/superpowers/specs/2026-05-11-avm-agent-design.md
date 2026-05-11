# AVM AI Agent — Design Spec
**Date:** 2026-05-11
**Project:** AVM Wizard & GPT
**Stakeholders:** DPD Taiwan staff + NCCU grad students collaborating with DPD Taiwan

---

## Context

Activity Value Management (AVM), developed by Professor Ann Wu, is a comprehensive management system linking operational activities (causes) to financial outcomes (results). DPD Taiwan and NCCU graduate students need an AI agent that can answer AVM-related questions, guide users through AVM implementation, and generate management reports — replacing the current interim workflow of manually querying NotebookLM and Google Drive resources.

The agent must serve users at multiple levels (executives, managers, analysts, students) and adapt response depth both by user role and by query complexity.

---

## Architecture Overview

### Stack

| Layer | Technology | Purpose |
|---|---|---|
| Intelligence | Claude Sonnet 4.6 + Opus 4.7 (Anthropic SDK) | Q&A, wizard orchestration, report generation |
| RAG / Knowledge | LlamaIndex + Pinecone | Document retrieval over AVM knowledge base |
| Embeddings | Voyage AI `voyage-multilingual-2` | Bilingual (zh-TW + EN) vector embeddings |
| Ingestion | LlamaIndex GoogleDriveReader + FastAPI webhook | Auto-sync from Google Drive |
| UI | Chainlit | Chat interface with streaming, file upload, sessions |
| Backend | FastAPI | Webhook receiver, report generation API |
| Proxy | nginx + Let's Encrypt | HTTPS termination |
| Hosting | Cloud VM (GCP e2-medium or AWS t3.small) | ~$15–25/month |

### Model Usage

| Mode | Model | Reason |
|---|---|---|
| Conversational Q&A | Claude Sonnet 4.6 | Fast, cost-efficient for standard queries |
| Guided Wizard | Claude Sonnet 4.6 | Structured conversation flows |
| Analysis & Reporting | Claude Opus 4.7 | Extended thinking for complex multi-step analysis |

### Three Interaction Modes (unified Chainlit interface)

1. **Conversational Q&A** — free-form natural language questions about AVM
2. **Guided Wizard** — step-by-step AVM setup or diagnosis flows
3. **Analysis & Reporting** — upload data, generate structured reports, drill down via chat

---

## Section 1: Depth & Role Calibration

Response depth is governed by two combined signals:

- **Static signal**: User role assigned at account creation
  - Executive (總經理): concise strategic summaries by default
  - Manager (中階主管): department-level analysis by default
  - Analyst / Student: detailed module-level breakdowns by default
- **Dynamic signal**: Query complexity at runtime — a detailed, multi-part query unlocks deeper responses regardless of role.

Role sets the **default depth**, not a ceiling. An executive who sends a highly detailed query gets a deep answer.

System prompt instruction: *"Calibrate response depth and verbosity to match the specificity and complexity of the user's query, using their role only as a baseline default."*

---

## Section 2: Knowledge Ingestion Pipeline

### Flow

```
Google Drive Folder (AVM resources)
    ↓  LlamaIndex GoogleDriveReader (PDFs, DOCX, slides)
    ↓  Semantic chunking (~512 tokens, 50-token overlap)
    ↓  Voyage AI voyage-multilingual-2 → embeddings
    ↓  Pinecone upsert with metadata:
       { module: 1|2|3|4, language: "zh-TW"|"en", doc_type, source_file }
    ↓  Index: "avm-knowledge-base"
```

### Auto Re-ingestion (Google Drive Webhooks)

- Register Google Drive Push Notification webhook → FastAPI `/webhook` endpoint
- Triggered on: file **created** or **modified** in the AVM Drive folder
- On trigger: delete old Pinecone chunks for that file → re-fetch → re-chunk → re-embed → upsert
- Webhook registrations expire every 7 days — auto-renewal on server startup
- Source: Google Drive folder `1ApsN_DE5qmEgxSF6KQLx-fkG8iNDMOMq`

---

## Section 3: Core RAG Agent

### Tool Set

| Tool | Purpose |
|---|---|
| `search_avm_knowledge(query, module_filter?)` | Semantic search in Pinecone, optional module filter (1–4) |
| `get_user_context()` | Returns user role |
| `generate_report(report_type, parameters)` | Triggers structured report (Sprint 3) |
| `start_wizard(type)` | Initiates wizard flow (Sprint 2) |

### Prompt Caching Strategy

- **Tier 1 (cached)**: AVM core definitions, 4 modules, 5 activity attribute types, key formulas
- **Tier 2 (dynamic)**: Retrieved Pinecone chunks per query

### Language

Auto-detect per message. Claude responds in the same language as the query. Mixed-language queries default to Traditional Chinese.

---

## Section 4: Wizard Engine *(Sprint 2)*

### Wizard A: AVM Setup Wizard

Guides a company through full 4-module AVM implementation sequentially. Each step: Claude asks structured questions → validates input → saves to session state → advances. Users can pause and resume.

### Wizard B: Diagnosis Wizard

Symptom-driven root-cause analysis:

| Symptom | AVM Investigation Path |
|---|---|
| "We're losing money" | Module 4 value objects → which customers/products? |
| "Margins are shrinking" | Module 3 → non-value-added activity costs |
| "Capacity feels wasted" | Module 2 vs 3 delta → idle capacity cost |
| "Need ESG reporting" | Module 3 ESG-tagged activities → C-PVM logic |

---

## Section 5: Analysis & Reporting Engine *(Sprint 3)*

### Four Report Types

| Report | Key Metrics | Primary Users |
|---|---|---|
| Profitability Report | Revenue, full-cost (incl. hidden costs), net profit by product/customer/BU | Executive, Manager |
| Capacity Analysis Report | Normal vs. actual capacity, idle cost, over-utilization cost | Manager, Analyst |
| Activity Attribute Dashboard | Breakdown by quality / value-added / ESG / customer service | Manager, Analyst |
| Value Object Report | Long-term vs. short-term value; flags "large client, actually unprofitable" | Executive, Manager |

Data input: users upload Excel/CSV via Chainlit file upload. No live ERP connection in Sprint 3.

---

## Section 6: Deployment & Authentication

### Hosting

Single cloud VM (GCP e2-medium or AWS t3.small, ~$15–25/month):
- Chainlit (port 8000) + FastAPI (port 8001) behind nginx + Let's Encrypt HTTPS

### Branding

- DPD Taiwan logo in Chainlit sidebar via `config.toml` → `[UI] logo = "public/dpd_logo.png"`
- Logo PNG to be provided by DPD Taiwan, placed in `public/`

### Authentication

Chainlit built-in username/password. Two groups:

| Group | Default Role |
|---|---|
| `dpd_taiwan` | Manager or Executive (per individual) |
| `nccu_students` | Analyst / Student |

### Environment Variables

```
ANTHROPIC_API_KEY
PINECONE_API_KEY
PINECONE_INDEX_NAME
GOOGLE_DRIVE_FOLDER_ID
GOOGLE_SERVICE_ACCOUNT_JSON
VOYAGE_API_KEY
WEBHOOK_VERIFICATION_TOKEN
```

---

## Sub-Project Phasing

| Phase | Sub-Projects | Deliverable |
|---|---|---|
| **Sprint 1** | Knowledge Pipeline + Core RAG Agent | Working bilingual Q&A chatbot |
| **Sprint 2** | Setup Wizard + Diagnosis Wizard | Guided AVM implementation flows |
| **Sprint 3** | Reporting Engine | Full analysis and report generation |

---

## Cost Estimate (~20 users, moderate usage)

| Service | Cost |
|---|---|
| Anthropic Claude API | ~$20–40/month (prompt caching reduces cost) |
| Pinecone | Free tier initially |
| Voyage AI | Free tier initially (200M tokens) |
| Google Drive API | Free |
| Cloud VM | ~$15–25/month |
| **Total** | **~$35–65/month** |
