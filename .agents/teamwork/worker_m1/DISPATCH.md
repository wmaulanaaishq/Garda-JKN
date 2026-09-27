# Dispatch: Worker M1 — Qdrant Vector Database & RAG Enhancement (Tahap 3)

## Task Description
Implement Milestone M1: Qdrant Vector Database RAG Enhancement for INA-CBG and PNPK clinical guidelines.

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
- Environment management (`./venv`)

## Completion Criteria
1. Dependencies installed into `./venv` so `qdrant_client`, `langchain`, `pypdf`, `sentence_transformers` (or `fastembed`), `xgboost`, `shap`, etc. import cleanly.
2. `app/core/vector_db.py` updated with robust local Qdrant embedded mode, chunking with metadata, and similarity search.
3. `ingest_pnpk.py` runnable, ingesting PNPK documents from `Data RAG/`.
4. `test_rag.py` created and executing cleanly (exit code 0), demonstrating indexing and semantic query returning relevant clinical snippets.
5. 

## 2026-09-27T07:41:27Z
You are worker_m1, the Qdrant RAG Specialist Worker for GARDA-JKN.
Your working directory is: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1/
Project root: /home/wmaulanaaishq/projects/bpjs_2025

Scope & Exclusive File Ownership:
- app/core/vector_db.py
- ingest_pnpk.py
- test_rag.py
- Virtual environment at venv/

Tasks:
1. Restore/install all missing dependencies into `./venv`.
2. Implement/enhance `app/core/vector_db.py`.
3. Update `ingest_pnpk.py`.
4. Create `test_rag.py` and verify it passes.
5. Write complete handoff report.
6. Send message to orchestrator.
