"""Create a blinded local review queue from the BPJS sample.

The queue contains claim evidence needed by a medical reviewer, but excludes
proxy labels, model scores, SHAP values, and the original claim identifier.
Generated files belong under evaluation/reviewer_data/ and are gitignored.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from garda_ds_pipeline import BPJSDataLoader, ClinicalFeatureExtractor


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "evaluation" / "reviewer_data"
LABEL_COLUMNS = [
    "review_item_id",
    "label",
    "fraud_mechanism",
    "evidence_references",
    "severity_supported",
    "evidence_sufficient",
    "reviewer_notes",
    "reviewer_id",
    "reviewed_at",
]


def pseudonymize(value: object, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:20]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=300)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    salt = os.getenv("REVIEW_QUEUE_SALT", "")
    if not salt:
        raise SystemExit("Set REVIEW_QUEUE_SALT before generating a blinded review queue.")

    fkrtl_path = ROOT / "data sampel bpjs" / "202403_fkrtl.dta"
    secondary_path = ROOT / "data sampel bpjs" / "202405_diagnosissekunder.dta"
    fkrtl, secondary = BPJSDataLoader.load_data(
        n_samples=None,
        fkrtl_path=str(fkrtl_path),
        sekunder_path=str(secondary_path),
    )
    features = ClinicalFeatureExtractor().transform(fkrtl, secondary)
    if len(features) > args.samples:
        rng = np.random.RandomState(42)
        selected = rng.choice(features.index.to_numpy(), size=args.samples, replace=False)
        features = features.loc[selected].copy()

    rows = []
    for _, row in features.iterrows():
        claim_id = row.get("FKL02", "")
        rows.append({
            "review_item_id": pseudonymize(claim_id, salt),
            "primary_diagnosis_code": str(row.get("FKL17A", "")),
            "cbg_code": str(row.get("FKL19", "")),
            "facility_class": str(row.get("FKL09", "")),
            "care_setting": str(row.get("FKL10", "")),
            "admission_date": str(row.get("FKL03", "")),
            "discharge_date": str(row.get("FKL04", "")),
            "los_days": float(row.get("LOS_HARI", 0)),
            "billed_amount": float(row.get("BIAYA_TAGIH", 0)),
            "severity_level_claimed": int(row.get("SEVERITY_LEVEL", 0)),
            "procedure_code": str(row.get("FKL30", "")),
            "discharge_status": str(row.get("FKL14", "")),
            "secondary_diagnosis_count": int(row.get("JML_DIAG_SEKUNDER", 0)),
            "supporting_record_reference": "",
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    queue_path = args.output_dir / "review_queue.csv"
    with queue_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    for reviewer in ("reviewer_a", "reviewer_b"):
        label_path = args.output_dir / f"labels_{reviewer}.csv"
        with label_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=LABEL_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow({"review_item_id": row["review_item_id"]})

    metadata = {
        "queue_rows": len(rows),
        "source_files": [fkrtl_path.name, secondary_path.name],
        "contains_original_claim_id": False,
        "contains_model_score": False,
        "contains_proxy_label": False,
        "review_labels": ["VALID", "SUBSTANTIATED_FRAUD", "CODING_ERROR", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE"],
    }
    (args.output_dir / "queue_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(f"Queue: {queue_path}")


if __name__ == "__main__":
    main()
