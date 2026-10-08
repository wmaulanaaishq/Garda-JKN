"""Reconcile two independent reviewer label files without touching raw claims."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from sklearn.metrics import cohen_kappa_score


VALID_LABELS = {"VALID", "SUBSTANTIATED_FRAUD", "CODING_ERROR", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE"}


def read_labels(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = {}
    for row in rows:
        item_id = row.get("review_item_id", "").strip()
        label = row.get("label", "").strip().upper()
        if not item_id or label not in VALID_LABELS:
            continue
        result[item_id] = row
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer-a", required=True, type=Path)
    parser.add_argument("--reviewer-b", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    reviewer_a = read_labels(args.reviewer_a)
    reviewer_b = read_labels(args.reviewer_b)
    common_ids = sorted(set(reviewer_a) & set(reviewer_b))
    if not common_ids:
        raise SystemExit("Tidak ada item dengan label valid dari kedua reviewer.")

    labels_a = [reviewer_a[item]["label"] for item in common_ids]
    labels_b = [reviewer_b[item]["label"] for item in common_ids]
    consensus_rows = []
    disagreements = 0
    for item_id, label_a, label_b in zip(common_ids, labels_a, labels_b):
        agreed = label_a == label_b
        if not agreed:
            disagreements += 1
        consensus_rows.append({
            "review_item_id": item_id,
            "reviewer_a_label": label_a,
            "reviewer_b_label": label_b,
            "consensus_label": label_a if agreed else "ADJUDICATION_REQUIRED",
            "agreement": agreed,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(consensus_rows[0].keys()))
        writer.writeheader()
        writer.writerows(consensus_rows)

    report = {
        "items_reviewed_by_both": len(common_ids),
        "agreements": len(common_ids) - disagreements,
        "disagreements": disagreements,
        "agreement_rate": (len(common_ids) - disagreements) / len(common_ids),
        "cohen_kappa": cohen_kappa_score(labels_a, labels_b),
        "consensus_rule": "Only exact agreement is consensus; disagreements require a third medical adjudicator.",
        "output": str(args.output),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
