# Dispatch: Worker M1 v3 — Qdrant Vector Database & RAG Enhancement (Tahap 3)

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
- Virtual environment at `/home/wmaulanaaishq/projects/bpjs_2025/venv/`

## Efficiency and Technical Guidance
1. **Fast Dependency Installation**:
   DO NOT install heavy packages like `torch` or `sentence-transformers` which take multi-gigabyte downloads.
   Install the necessary packages quickly using:
   `./venv/bin/pip install qdrant-client langchain langchain-community langchain-openai pypdf xgboost shap pydantic python-dotenv`
   Verify with `./venv/bin/python -c "import qdrant_client, langchain, pypdf, xgboost"`.
2. **Embedding Architecture**:
   In `app/core/vector_db.py`, use AIML API embeddings (`openai/text-embedding-3-small` using `AIML_API_KEY` from `.env` via `OpenAIEmbeddings(api_key=..., base_url="https://api.aimlapi.com/v1", model="openai/text-embedding-3-small")`), with a fast fallback (e.g. FastEmbed or hash/dense if offline).
3. **Qdrant Storage**:
   Use local Qdrant embedded mode (`path="knowledge_base/qdrant_db"` or `:memory:` if locked). Automatically create the collection if it doesn't exist.
4. **Metadata Preservation**:
   Extract structured chunks with metadata (`source`, `disease`, `icd10`, `page`, `rule_type`).
5. **Testing**:
   Implement `test_rag.py` at project root. It must:
   - Ingest a sample guideline or PDF chunk
   - Search for clinical terms (e.g., Stroke, STEMI, Epilepsi, Diabetes)
   - Assert non-empty relevant results returned
   - Exit with code 0: `./venv/bin/python test_rag.py`

## 2026-09-27T08:05:50Z
You are worker_m1_v3, the Qdrant RAG Specialist Worker for GARDA-JKN.

Your working directory is: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_v3/
Project root: /home/wmaulanaaishq/projects/bpjs_2025

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

First, read the authoritative user request at:
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/ORIGINAL_REQUEST.md
Also read:
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/explorer_survey_1/handoff.md
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/orchestrator_2/PROJECT.md
/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_v3/DISPATCH.md

Your Scope & Exclusive File Ownership:
- /home/wmaulanaaishq/projects/bpjs_2025/app/core/vector_db.py
- /home/wmaulanaaishq/projects/bpjs_2025/ingest_pnpk.py
- /home/wmaulanaaishq/projects/bpjs_2025/test_rag.py
- Virtual environment at /home/wmaulanaaishq/projects/bpjs_2025/venv/

Tasks:
1. Run pip install for the lightweight requirements. Verify with `./venv/bin/python -c "import qdrant_client, langchain, pypdf, xgboost; print('Imports OK')"`.
2. Enhance `app/core/vector_db.py`:
   - `MedicalKnowledgeBase` class.
   - Embeddings: `OpenAIEmbeddings(model="openai/text-embedding-3-small", api_key=..., base_url="https://api.aimlapi.com/v1")` using `AIML_API_KEY`, or local fast fallback.
   - Embedded Qdrant at `knowledge_base/qdrant_db`.
   - Methods: `ingest_document(text_content, metadata)`, `search_rules(query, top_k=3) -> List[Dict[str, Any]]` or string format, and collection initialization.
3. Update `ingest_pnpk.py` to ingest PDF rules or clinical guidelines into Qdrant.
4. Implement `test_rag.py` at project root:
   - Ingests test medical rule/PDF.
   - Performs similarity queries for clinical conditions.
   - Asserts valid non-empty responses returned with metadata.
   - Must execute cleanly: `./venv/bin/python test_rag.py` (exit code 0).
5. Document all commands and results in `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_v3/handoff.md`.
6. Send completion message back to parent.
