# Dispatch: Worker M2 — LangGraph Multi-Agent Orchestration & E2E Verification (Tahap 4)

## Task Description
Implement Milestone M2 (LangGraph Multi-Agent Orchestration with Validator and Executor) and Milestone M3 (Automated E2E Verification & Explainable AI Evaluation).

## Mandatory Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Input Files
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/ORIGINAL_REQUEST.md` (Authoritative Requirements)
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/spec_miner_survey_1/handoff.md` (Full Specification for State, Nodes, and Prompts)
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/explorer_survey_1/handoff.md` (Defect Analysis & Codebase Structure)
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/orchestrator_2/PROJECT.md` (Architecture & Interface Contracts)
- `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m1_v3/handoff.md` (Qdrant RAG Contracts & KB Usage)

## Exclusive File Ownership
- `/home/wmaulanaaishq/projects/bpjs_2025/app/agents/state.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/app/agents/nodes.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/app/agents/workflow.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/app/agents/__init__.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/app/core/llm.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/app/core/ml_engine.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/app/core/__init__.py`
- `/home/wmaulanaaishq/projects/bpjs_2025/test_langgraph.py`

## Completion Criteria
1. `app/agents/state.py` implements full `ClaimState` TypedDict with `final_status`, `adjudication_reason`, `audit_trail`, `confidence_score`, and backward-compatible aliases.
2. `app/core/ml_engine.py` exports `ml_engine = MLEngine(...)` singleton, implements feature mapper and risk/anomaly prediction without errors.
3. `app/core/llm.py` initializes ChatOpenAI via AIML API (`deepseek/deepseek-chat` default with `AIML_API_KEY`).
4. `app/agents/nodes.py` implements all 5 nodes cleanly:
   - `intake_node`: PII masking under Zero-Knowledge principles.
   - `ml_scoring_node`: Feature mapping, ML risk score, anomaly detection, feature explanation.
   - `rag_retrieval_node`: Querying `MedicalKnowledgeBase` for diagnosis & procedure guidelines.
   - `validator_node` ("Pengecek"): Deterministic & clinical cross-checking against PNPK criteria.
   - `executor_node` ("Pengeksekusi"): Prompting DeepSeek LLM, robust JSON parsing (stripping think tags/code fences), outputting formal Indonesian medical adjudication log and final status (`APPROVED`, `DOWNGRADED`, `ESCALATED`).
5. `app/agents/workflow.py` compiles `StateGraph(ClaimState)` and exports `garda_app`.
6. `test_langgraph.py` created at project root, implementing:
   - 3 benchmark scenarios (DOWNGRADED, APPROVED, ESCALATED).
   - Batch simulation of sample claims from `artifacts/sample_vclaim_simulation.json`.
   - Formal assertion verification on `final_status`, `adjudication_reason`, `audit_trail`.
   - Formatted Explainable AI metrics report printed to stdout.
   - Passes with exit code 0 (`./venv/bin/python test_langgraph.py`).
7. Write complete handoff report to `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/worker_m2/handoff.md`.
