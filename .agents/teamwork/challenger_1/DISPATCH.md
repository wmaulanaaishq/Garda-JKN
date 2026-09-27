# Dispatch: Challenger 1 — Stress Testing & Malformed Payload Verification

## Task
Adversarially challenge GARDA-JKN pipeline with stress tests, malformed claim payloads, missing fields, extreme costs, and invalid diagnosis codes.

## Instructions
1. Test how the pipeline handles:
   - Claims with completely empty clinical data or missing billing keys.
   - Extremely high billing costs (e.g. Rp 500,000,000) or negative LOS.
   - Unknown diagnosis codes not in PNPK.
   - Verify that the workflow never hangs or crashes and always produces `final_status` in `["APPROVED", "DOWNGRADED", "ESCALATED"]`.
2. Write a verification script or execute adversarial invocations against `garda_app.invoke()`.
3. Render verdict: `APPROVE` or `REJECT` in `/home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/challenger_1/handoff.md`.

## 2026-09-27T08:29:31Z
You are challenger_1, the Stress & Malformed Payload Challenger for GARDA-JKN.

Working directory: /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/challenger_1/
Project root: /home/wmaulanaaishq/projects/bpjs_2025

Read:
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/ORIGINAL_REQUEST.md
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/orchestrator_2/PROJECT.md
- /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/challenger_1/DISPATCH.md

Adversarially challenge the multi-agent pipeline:
- Construct adversarial/malformed claim payloads (empty dictionaries, missing billing data, extreme outlier costs like Rp 500M, negative LOS, unknown ICD-10 codes).
- Pass them into garda_app.invoke().
- Assert that the pipeline NEVER crashes or hangs and always produces a valid final_status in ['APPROVED', 'DOWNGRADED', 'ESCALATED'] and adjudication_reason.
Write your findings and render verdict: APPROVE or REJECT in /home/wmaulanaaishq/projects/bpjs_2025/.agents/teamwork/challenger_1/handoff.md.
Send message to orchestrator upon completion.
