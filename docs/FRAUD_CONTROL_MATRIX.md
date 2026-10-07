# GARDA-JKN Fraud Control Matrix

This matrix separates a legally supported fraud signal from a model heuristic. A
high-risk score is never, by itself, a fraud finding. The final label requires
evidence and, for ambiguous cases, human verification.

## Evidence Status

- `AUTHORITATIVE`: copied from an applicable regulation or official clinical/tariff guideline.
- `OPERATIONAL`: an implementation rule derived from an authoritative source.
- `HEURISTIC`: a risk-prioritization signal that must not be presented as proof.
- `PENDING_SOURCE`: parameter still needs the exact official document, article, or page.

## Matrix

| Control | Fraud pattern | Required evidence | Candidate data signals | Status | Automated action |
| --- | --- | --- | --- | --- | --- |
| FC-01 | Upcoding | Submitted diagnosis/severity versus clinical record and applicable INA-CBG rule | Severity gap, unsupported secondary diagnosis, missing clinical evidence | PENDING_SOURCE | Review or escalate |
| FC-02 | Phantom billing | Procedure/service record, timestamp, result, and DPJP documentation | Claimed procedure without matching evidence | OPERATIONAL | Escalate; never auto-reject from one signal |
| FC-03 | Unbundling or fragmentation | Episode definition and tariff packaging rule | Same episode split across claims or separately billed bundled components | PENDING_SOURCE | Escalate |
| FC-04 | Duplicate billing | Claim, episode, patient, date, provider, and procedure identifiers | Exact and near-duplicate claims | OPERATIONAL | Hold duplicate for review |
| FC-05 | Inflated billing | Applicable tariff, quantity, unit, and supporting record | Cost/quantity deviation after peer and tariff adjustment | HEURISTIC | Risk ranking |
| FC-06 | Medical necessity | PNPK/clinical guideline and patient evidence | Diagnosis-procedure mismatch, missing indication | PENDING_SOURCE | Escalate |
| FC-07 | Clinical documentation inconsistency | Medical record, lab, radiology, procedure, and discharge evidence | Diagnosis, procedure, laboratory, and outcome mismatch | HEURISTIC | Risk ranking or escalate |
| FC-08 | Episode/readmission manipulation | Episode and readmission policy | Short-interval readmission, repeated episode, unusual LOS | PENDING_SOURCE | Escalate |
| FC-09 | Administrative/identity anomaly | Eligibility and service identity records | Duplicate identity, claim identity mismatch, abnormal reuse | PENDING_SOURCE | Hold for verification |
| FC-10 | Provider/referral conflict | Referral and provider relationship policy | Self-referral or abnormal provider concentration | PENDING_SOURCE | Risk ranking |

## Source Register

The exact PDF and status must be checked before a row is promoted to
`AUTHORITATIVE` or encoded as an automatic rule.

- Permenkes No. 16 Tahun 2019: prevention, handling, and administrative sanctions for fraud in JKN.
- Permenkes No. 36 Tahun 2015: earlier JKN fraud regulation; verify whether a provision is superseded.
- Permenkes No. 3 Tahun 2023: JKN service tariffs and INA-CBG context.
- Permenkes No. 24 Tahun 2022: medical record governance and evidence integrity.
- Disease-specific PNPK and applicable KMK documents.
- BPJS Kesehatan claim-verification and INA-CBG technical guidance.

Primary repositories:

- https://jdih.kemkes.go.id/
- https://peraturan.bpk.go.id/
- https://peraturan.go.id/

## Label Policy

Training and evaluation must distinguish these outcomes:

- `VALID`: evidence supports the submitted claim.
- `SUBSTANTIATED_FRAUD`: independent audit confirms intentional or materially fraudulent conduct.
- `CODING_ERROR`: claim is wrong or unsupported, but intent is not established.
- `AMBIGUOUS`: evidence is incomplete or reviewers disagree.
- `UNLABELED`: no independent review is available.

Proxy labels generated from rules are suitable for risk-prioritization experiments
only. They must not be called confirmed fraud labels or used as the sole basis for
an automatic sanction.
