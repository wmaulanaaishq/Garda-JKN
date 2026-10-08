# BRIEFING — 2026-10-07T15:48:30Z

## Mission
Supervise execution of Advanced PDF Parsing upgrade for PNPK RAG ingestion pipeline (table parsing, complex layouts, OCR/markdown extraction via external API like LlamaParse or Unstructured), monitoring progress and liveness via crons, and verifying completion via independent victory auditor.

## 🔒 My Identity
- Archetype: sentinel
- Working directory: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/sentinel
- Orchestrator: f598af4d-e0c7-40f6-9f84-814d12b17500
- Victory Auditor: [to be spawned on victory claim]
- Orchestrator (Active): 11c744ff-60b8-4c08-8fd1-a00f87f8adb9 (orchestrator_3)
- Orchestrator (Active - E2E Testing): 6076e050-cb3e-43a9-b14a-360212480217 (orchestrator_4)
- Victory Auditor (Active - E2E Testing): e2582244-1f1f-45ab-bad9-19d833c05049 (auditor_victory_1)
- SWE Orchestrator: 6e79280e-51f4-4b76-8c30-670555420ff5 (swe_1)

## 🔒 Key Constraints
- No technical decisions — relay only
- Victory Audit is MANDATORY before reporting completion
- Must not write code or make technical decisions; keep context ultra-light
- Route selected: General path (teamwork_preview_orchestrator)
- Monitor progress and liveness via crons
- Clean up all crons and subagents upon completion
- Route selected: SWE Light path (teamwork_preview_swe)

## User Context
- **Last user request**: Upgrade RAG document ingestion pipeline in ingest_pnpk.py to parse nested tables, complex layouts, and OCR text/flowcharts from medical PDF (PNPK) via external API (e.g. LlamaParse/Unstructured). Small focused team requested for single self-contained fix.
- **Pending clarifications**: none
- **Delivered results**: Previous E2E testing completed. New task launched under SWE Light.

## Project Status
- **Phase**: in progress
- **Route**: SWE Light (teamwork_preview_swe)
- **Active Subagent Directory**: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/swe_1
- **Cron 1 (Progress)**: task-28 (*/8 * * * *)
- **Cron 2 (Liveness)**: task-30 (*/10 * * * *)

## Victory Audit Status
- **Triggered**: no
- **Verdict**: pending
- **Retry count**: 0

## Artifact Index
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/ORIGINAL_REQUEST.md — Authoritative record of user requests
- /home/wmaulanaaishq/projects/bpjs_2025/ingest_pnpk.py — Target ingestion script
- /home/wmaulanaaishq/projects/bpjs_2025/test_advanced_parsing.py — Test script to create and verify
- /home/wmaulanaaishq/projects/bpjs_2025/app/core/vector_db.py — Qdrant Document schema
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/swe_1 — SWE Light working directory
