# Project: GARDA-JKN Healthkathon BPJS 2026

## Architecture
GARDA-JKN is a multi-tier AI verification and adjudication platform for BPJS Kesehatan claims:
- **Lapis 1 (ML Risk Engine)**: XGBoost classifier (`artifacts/garda_xgb_model.json`) estimating fraud and upcoding probability with feature importance.
- **Lapis 2 (Knowledge Base & RAG)**: Qdrant Vector DB (local disk embedded or in-memory) storing clinical guidelines (PNPK Kemenkes) and INA-CBG severity rules with semantic search.
- **Lapis 3 (Multi-Agent StateGraph)**: LangGraph state machine orchestrating 5 modular agents:
  1. `intake`: PII masking under Zero-Knowledge principles (UU PDP No. 27/2022).
  2. `ml_scoring`: Tabular feature mapping and statistical anomaly scoring.
  3. `rag_retrieval`: Diagnosis/procedure guideline retrieval from Qdrant.
  4. `validator`: The "Pengecek" performing deterministic and clinical rule cross-checking.
  5. `executor`: The "Pengeksekusi" calling DeepSeek LLM (via AIML API) to synthesize an explainable JSON adjudication letter in formal Indonesian medical terminology.
- **Lapis 4 (E2E Verification & XAI Evaluation)**: Automated testing suite (`test_rag.py`, `test_langgraph.py`) outputting Explainable AI metrics.

## Code Layout
```
/home/wmaulanaaishq/projects/bpjs_2025/
├── app/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py           # ClaimState TypedDict (consolidated, robust)
│   │   ├── nodes.py           # intake, ml_scoring, rag_retrieval, validator, executor
│   │   └── workflow.py        # LangGraph StateGraph builder (garda_app)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── llm.py             # ChatOpenAI client via AIML API (DeepSeek)
│   │   ├── ml_engine.py       # MLEngine wrapper & singleton export
│   │   └── vector_db.py       # MedicalKnowledgeBase wrapping Qdrant & embeddings
├── artifacts/
│   ├── garda_features_meta.json
│   ├── garda_xgb_model.json
│   └── sample_vclaim_simulation.json
├── Data RAG/                  # 5 PNPK PDFs & INA-CBG guidelines
├── knowledge_base/            # Qdrant local storage
├── ingest_pnpk.py             # Script to ingest PNPK PDFs into Qdrant
├── test_rag.py                # R1 Verification Script
├── test_langgraph.py          # R2 & R3 Verification & XAI Script
└── requirements.txt
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Python Environment & Dependencies | Restore missing packages (qdrant-client, langchain, etc.) | M1 | explorer_survey_1 |
| 2 | Qdrant Vector DB & RAG | Semantic search over PNPK PDFs & INA-CBG rules | M1 | ORIGINAL_REQUEST R1 |
| 3 | PDF Chunking & Metadata | Structured chunking preserving page, disease, and rule types | M1 | ORIGINAL_REQUEST R1 |
| 4 | RAG Verification Script | `test_rag.py` verifying ingestion & retrieval | M1 | ORIGINAL_REQUEST Acceptance Criteria |
| 5 | Clean Modular Architecture | Enkapsulasi di `app/agents/` dan `app/core/` | M2 | ORIGINAL_REQUEST R2 & Integration |
| 6 | Consolidated State Schema | `ClaimState` TypedDict matching nodes and UI | M2 | spec_miner_survey_1 |
| 7 | Validator Agent ("Pengecek") | Clinical & ML cross-checker node | M2 | ORIGINAL_REQUEST R2 |
| 8 | Executor Agent ("Pengeksekusi") | DeepSeek LLM structured JSON adjudication draf | M2 | ORIGINAL_REQUEST R2 |
| 9 | Formal Indonesian Medical Phrasing | Bahasa medis baku BPJS untuk APPROVED, DOWNGRADED, ESCALATED | M2 | ORIGINAL_REQUEST R2 |
| 10 | E2E LangGraph Verification | `test_langgraph.py` running pipeline without timeout/loop | M3 | ORIGINAL_REQUEST R3 & Acceptance Criteria |
| 11 | Explainable AI Metrics | XAI reasoning logs and audit trail | M3 | ORIGINAL_REQUEST R3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Qdrant Vector DB & RAG | Environment setup, `app/core/vector_db.py`, `ingest_pnpk.py`, `test_rag.py` | None | DONE |
| 2 | M2: LangGraph Multi-Agent | `app/agents/state.py`, `app/core/ml_engine.py`, `app/core/llm.py`, `app/agents/nodes.py`, `app/agents/workflow.py` | M1 | DONE |
| 3 | M3: E2E Verification & XAI | `test_langgraph.py`, assertion verification, Explainable AI reporting | M2 | DONE |
| 4 | M4: Integration Gate & Forensics | Reviewer, Challenger, and Forensic Auditor verification | M1, M2, M3 | IN_PROGRESS |

## Interface Contracts
### `app/core/vector_db.py` ↔ `app/agents/nodes.py`
- `MedicalKnowledgeBase(collection_name="bpjs_pnpk", path="knowledge_base/qdrant_db")`
- `kb.search_rules(query: str, top_k: int = 3) -> List[Dict[str, Any]]`
- Format: `[{"text": str, "source": str, "score": float, "metadata": dict}]`

### `app/core/ml_engine.py` ↔ `app/agents/nodes.py`
- `ml_engine = MLEngine(model_path="artifacts/garda_xgb_model.json", meta_path="artifacts/garda_features_meta.json")`
- `ml_engine.predict_risk(claim_data: dict) -> dict`
- Format: `{"risk_score": float, "is_anomaly": bool, "analyzed_features": list, "explanation": str}`

### `app/agents/workflow.py` Entry/Exit Contract
- Input: `{"claim_data": dict}` or full `ClaimState`
- Output: `ClaimState` containing `final_status` (`"APPROVED"` | `"DOWNGRADED"` | `"ESCALATED"`), `adjudication_reason`, `audit_trail`, `confidence_score`
