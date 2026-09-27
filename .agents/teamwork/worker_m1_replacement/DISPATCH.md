# Dispatch: Worker M1 Replacement — Qdrant Vector Database & RAG Enhancement (Tahap 3)

## Task Description
Implement Milestone M1: Qdrant Vector Database RAG Enhancement for INA-CBG and PNPK clinical guidelines. (Replaced worker_m1 due to network timeout at startup).

## Mandatory Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Input Files
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/ORIGINAL_REQUEST.md` (Authoritative Requirements)
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/explorer_survey_1/handoff.md` (Codebase & Environment Survey)
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/explorer_survey_2/progress.md` (RAG & Qdrant Survey)
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/orchestrator_2/PROJECT.md` (Architecture & Contracts)

## Exclusive File Ownership
- `/home/wmaulanaaishq/projects/bpjs_2025/app/core/vector_db.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/ingest_pnpk.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/test_rag.py`
- Virtual environment at `/home/wmaulanaaishq/projects/bpjs_2025/venv/`

## Completion Criteria
1. Dependencies installed into `./venv` so `qdrant_client`, `langchain`, `pypdf`, `sentence_transformers` (or `fastembed`), `xgboost`, `shap`, `pydantic`, `python-dotenv` import cleanly without error.
2. `app/core/vector_db.py` updated with robust local Qdrant embedded mode, chunking with metadata, and similarity search.
3. `ingest_pnpk.py` runnable, ingesting PNPK documents from `Data RAG/`.
4. `test_rag.py` created and executing cleanly (exit code 0), demonstrating indexing and semantic query returning relevant clinical snippets.
5. All test commands and results documented in `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_replacement/handoff.md`.

## 2026-09-27T07:46:33Z
You are worker_m1_replacement, the Qdrant RAG Specialist Worker for GARDA-JKN.

Your working directory is: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_replacement/
Project root: /home/wmaulanaaishq/projects/bpjs_2025

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

First, read the authoritative user request at:
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/ORIGINAL_REQUEST.md
Also read:
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/explorer_survey_1/handoff.md
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/explorer_survey_2/progress.md
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/orchestrator_2/PROJECT.md
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_replacement/DISPATCH.md

Your Scope & Exclusive File Ownership:
- /home/wmaulanaaishq/projects/bpjs_2025/app/core/vector_db.py
- /home/wmaulanaaishq/projects/bpjs_2025/ingest_pnpk.py
- /home/wmaulanaaishq/projects/bpjs_2025/test_rag.py
- Virtual environment at /home/wmaulanaaishq/projects/bpjs_2025/venv/

Your Tasks:
1. Restore/install all missing dependencies into `./venv` so that `qdrant-client`, `langchain`, `langchain-community`, `langchain-openai`, `pypdf`, `sentence-transformers` (or `fastembed`), `xgboost`, `shap`, `pydantic`, `python-dotenv` are installed and can be imported cleanly without error.
2. Implement/enhance `app/core/vector_db.py`:
   - Robust `MedicalKnowledgeBase` class using local Qdrant embedded mode (`path="knowledge_base/qdrant_db"` or in-memory fallback if disk locks occur).
   - Embeddings: Support local FastEmbed / SentenceTransformer or AIML API (`openai/text-embedding-3-small` with `AIML_API_KEY`), with fallback.
   - Text splitter preserving metadata (`source`, `disease`, `icd10`, `page`, `rule_type`).
   - Similarity search `search_rules(query: str, top_k: int = 3) -> List[Dict[str, Any]]` returning structured text, score, source, metadata.
3. Update `ingest_pnpk.py` to ingest the 5 PNPK PDFs in `Data RAG/` into Qdrant (`knowledge_base/qdrant_db`), plus INA-CBG clinical rules.
4. Create `test_rag.py` at project root:
   - Demonstrates initialization, ingestion of dummy or real PDF, and successful similarity query returning relevant medical guideline text without error.
   - Run and verify: `./venv/bin/python test_rag.py` passes with exit code 0.
5. Write your complete handoff report to `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_replacement/handoff.md`.
6. Send a message to orchestrator upon completion.

