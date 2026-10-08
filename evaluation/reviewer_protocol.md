# Independent Fraud Review Protocol

The model output is hidden from both reviewers. Reviewers receive only the
blinded queue and the approved clinical/administrative evidence available in the
claim record.

## Labels

- `VALID`: evidence supports the submitted coding and payment claim.
- `SUBSTANTIATED_FRAUD`: objective evidence supports intentional false billing or misrepresentation.
- `CODING_ERROR`: the claim is not supported, but the evidence does not establish intent to defraud.
- `AMBIGUOUS`: conflicting evidence requires a third reviewer.
- `INSUFFICIENT_EVIDENCE`: the available record cannot support a reliable decision.

## Review Rules

- Do not use model score, SHAP reason codes, proxy labels, or prior reviewer decisions.
- Record the exact evidence reference, diagnosis/procedure support, severity support, and whether the record is sufficient.
- A high cost, long LOS, severity III, or an outlier is not fraud by itself.
- Two reviewers label independently. Exact agreement is consensus.
- Any disagreement is adjudicated by a third qualified medical reviewer.
- `SUBSTANTIATED_FRAUD` requires objective evidence and a documented fraud mechanism; unsupported suspicion remains `AMBIGUOUS` or `INSUFFICIENT_EVIDENCE`.

## Required Outputs

- `labels_reviewer_a.csv`
- `labels_reviewer_b.csv`
- `reviewer_consensus.csv`
- `reviewer_agreement.json`

Run reconciliation only after both reviewers complete their files:

```bash
python evaluation/reconcile_reviewer_labels.py \
  --reviewer-a evaluation/reviewer_data/labels_reviewer_a.csv \
  --reviewer-b evaluation/reviewer_data/labels_reviewer_b.csv \
  --output evaluation/reviewer_data/reviewer_consensus.csv
```

Until those files contain real independent labels, the project has no verified
fraud ground truth and model accuracy must be reported as proxy-risk performance.
