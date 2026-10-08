# GARDA-JKN Evaluation

`golden_cases.json` contains synthetic cases only. It is safe to commit and is
not a substitute for independently reviewed BPJS claims.

The evaluation should be run in two layers:

1. DeepEval: answer relevancy, faithfulness, answer correctness, and citation correctness.
2. Ragas: context precision, context recall, context relevancy, faithfulness, and answer correctness.

The final report must also include exact decision/severity accuracy against the
golden labels. LLM-judge scores must never replace clinical review labels.

Install evaluation-only dependencies separately from production:

```bash
pip install -r requirements-evaluation.txt
```

Required credentials are read from the environment and never stored in this
directory. Run against local backend and local Qdrant for the reproducible demo.

## Model Integrity Audit

Run the proxy-label audit against a local feature table only:

```bash
python evaluation/audit_model_integrity.py \
  --data /path/to/local/features.dta \
  --label-col FRAUD_RISK \
  --output evaluation/model_integrity_report.json
```

The report compares all-feature AUC, AUC after removing rule-like features, and
permuted-label AUC. A strong all-feature score that collapses after ablation is
proxy dependence, not proof of fraud detection.

For the local Stata sample, run the wrapper below. It writes aggregate metrics
only and explicitly records that `FRAUD_RISK` is a proxy label:

```bash
python evaluation/audit_local_bpjs.py --samples 10000
```
