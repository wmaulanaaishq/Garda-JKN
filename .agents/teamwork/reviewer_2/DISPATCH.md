# Dispatch: Reviewer 2 — Clinical Logic, Robustness & Edge Case Review

## Task
Review clinical adjudication logic, robustness against edge cases, LLM output parsing, and state flow in GARDA-JKN.

## Instructions
1. Inspect:
   - `app/agents/nodes.py` (specifically Validator clinical rules for Stroke KDIGO, STEMI PCI, Epilepsy EEG; and Executor LLM prompt / regex JSON parser)
   - `app/core/vector_db.py` (collection handling, metadata preservation, fallback embeddings)
   - `app/core/ml_engine.py` (feature mapping resilience, SHAP calculation)
2. Run tests independently:
   - `./venv/bin/python test_rag.py`
   - `./venv/bin/python test_langgraph.py`
3. Verify:
   - No infinite loops, timeouts, or unhandled exceptions.
   - Robust JSON extraction handles thinking tags, markdown blocks, and raw JSON.
   - Clinical terminology conforms to standard Indonesian BPJS/PNPK phrasing.
4. Render verdict: `APPROVE` or `REQUEST_CHANGES` in `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/reviewer_2/handoff.md`.

## 2026-09-27T08:29:31Z
You are reviewer_2, the Clinical & Robustness Reviewer for GARDA-JKN.

Working directory: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/reviewer_2/
Project root: /home/wmaulanaaishq/projects/bpjs_2025

Read:
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/orchestrator_2/PROJECT.md
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m2/handoff.md
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/reviewer_2/DISPATCH.md

Review:
- Clinical decision rules in app/agents/nodes.py (Validator clinical checks: Stroke KDIGO AKI, STEMI PCI, Epilepsy EEG).
- Indonesian medical phrasing in executor node and adjudication letters.
- Robust JSON parsing resilience against markdown fences and reasoning tags.
- Run tests: ./venv/bin/python test_langgraph.py and ./venv/bin/python test_rag.py.
Render verdict: APPROVE or REQUEST_CHANGES in /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/reviewer_2/handoff.md.
Send message to orchestrator upon completion.
