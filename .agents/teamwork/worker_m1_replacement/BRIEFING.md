# BRIEFING — 2026-09-27T07:47:00Z

## Mission
Restore venv dependencies, implement robust Qdrant RAG engine in app/core/vector_db.py, ingest PNPK & INA-CBG rules in ingest_pnpk.py, and verify with test_rag.py.

## 🔒 My Identity
- Archetype: implementer
- Roles: implementer, qa, specialist
- Working directory: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_replacement/
- Original parent: f598af4d-e0c7-40f6-9f84-814d12b17500
- Milestone: M1: Qdrant Vector DB & RAG

## 🔒 Key Constraints
- Mandate: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations.
- Exclusive file ownership: app/core/vector_db.py, ingest_pnpk.py, test_rag.py, venv/
- Never place source code, tests, or data files in .agents/teamwork/
- Minimal change principle; genuine state and behavior
- All dependencies must be installed into ./venv and cleanly importable

## Current Parent
- Conversation ID: f598af4d-e0c7-40f6-9f84-814d12b17500
- Updated: not yet

## Task Summary
- **What to build**: Restore ./venv dependencies, implement/enhance app/core/vector_db.py with embedded Qdrant & hybrid/local/AIML embeddings, update ingest_pnpk.py to ingest PNPK PDFs + INA-CBG clinical rules, create and verify test_rag.py.
- **Success criteria**: ./venv/bin/python test_rag.py passes with exit code 0; Qdrant retrieves relevant clinical rules with structured metadata (source, disease, icd10, page, rule_type).
- **Interface contracts**: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/orchestrator_2/PROJECT.md § Interface Contracts
- **Code layout**: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/orchestrator_2/PROJECT.md § Code Layout

## Key Decisions Made
- Use Qdrant embedded mode (`path="knowledge_base/qdrant_db"`) with fallback to `:memory:` on lock.
- Support dual embeddings: AIML API `openai/text-embedding-3-small` (when online/configured) and FastEmbed / HuggingFace local fallback for offline resilience.
- Chunking preserving disease, ICD-10, rule_type, and page number metadata.

## Artifact Index
- app/core/vector_db.py — MedicalKnowledgeBase
- ingest_pnpk.py — Ingestion script for PNPK PDFs & INA-CBG rules
- test_rag.py — RAG verification test suite

## Change Tracker
- **Files modified**: None yet
- **Build status**: Pending
- **Pending issues**: Dependencies missing in ./venv

## Quality Status
- **Build/test result**: Pending
- **Lint status**: Pending
- **Tests added/modified**: test_rag.py (planned)

## Loaded Skills
- None
