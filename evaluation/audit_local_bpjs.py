"""Build and audit a local BPJS feature table without exporting raw claims."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from garda_ds_pipeline import (
    ADVANCED_FEATURE_COLS,
    BPJSDataLoader,
    ClinicalFeatureExtractor,
    StratifiedIsolationForest,
    generate_semi_supervised_labels,
)
from evaluation.audit_model_integrity import run_audit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FKRTL = ROOT / "data sampel bpjs" / "202403_fkrtl.dta"
DEFAULT_SEKUNDER = ROOT / "data sampel bpjs" / "202405_diagnosissekunder.dta"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation" / "results" / "bpjs_feature_integrity_latest.json")
    args = parser.parse_args()

    fkrtl, sekunder = BPJSDataLoader.load_data(
        n_samples=args.samples,
        fkrtl_path=str(DEFAULT_FKRTL),
        sekunder_path=str(DEFAULT_SEKUNDER),
    )
    features = ClinicalFeatureExtractor().transform(fkrtl, sekunder)
    isolation = StratifiedIsolationForest(n_estimators=60, random_state=42)
    isolation.fit(features)
    features["ISO_ANOMALY_SCORE"] = isolation.score_samples(features)
    features["FRAUD_RISK"] = generate_semi_supervised_labels(
        features,
        features["ISO_ANOMALY_SCORE"].to_numpy(),
        contamination_threshold=0.70,
    )

    report = run_audit(features[ADVANCED_FEATURE_COLS + ["FRAUD_RISK"]], "FRAUD_RISK", 42)
    report["source"] = {
        "fkrtl_file": DEFAULT_FKRTL.name,
        "secondary_file": DEFAULT_SEKUNDER.name,
        "fkrtl_rows_loaded": len(fkrtl),
        "secondary_rows_loaded": len(sekunder),
        "raw_claim_contents_exported": False,
        "label_type": "semi-supervised proxy label, not reviewer-confirmed fraud",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
