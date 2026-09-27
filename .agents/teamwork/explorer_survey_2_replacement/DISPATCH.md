# Dispatch for Explorer Survey 2 Replacement

## Identity
- Role: Vector Database & RAG Specialist Investigator
- Working Directory: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/explorer_survey_2_replacement/
- Project Root: /home/wmaulanaaishq/projects/bpjs_2025/
- Original Request: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/ORIGINAL_REQUEST.md

## Objective
Investigate how Qdrant and RAG are currently configured and implemented in `/home/wmaulanaaishq/projects/bpjs_2025/`.
Examine:
1. `app/core/vector_db.py`, `ingest_pnpk.py`, and `Data RAG/` PDFs.
2. Qdrant connection parameters (local path `knowledge_base/qdrant_db`, in-memory mode, or server).
3. Embedding model configuration (FastEmbed, SentenceTransformers, or OpenAI/AIML API `openai/text-embedding-3-small`).
4. Chunking strategy (token/character size, overlap, section headers for PNPK and INA-CBG rules).
5. Exact implementation needed for `test_rag.py` to satisfy acceptance criteria (ingesting a PDF, searching similarity, returning relevant text without errors).

## Output
Write a comprehensive report to `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/explorer_survey_2_replacement/handoff.md`.
When finished, send a message back to the orchestrator.
