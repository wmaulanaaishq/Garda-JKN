"""Audit proxy-label leakage and split sensitivity for tabular claim models.

This is a diagnostic tool. It does not turn proxy labels into clinical truth.
Raw BPJS files remain local and are supplied explicitly with --data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


SUSPECT_TOKENS = (
    "INCOHERENCE",
    "ANOMALY",
    "SUSPECT",
    "UPCOD",
    "PHANTOM",
    "FRAUD",
)


def load_frame(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".dta":
        return pd.read_stata(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def numeric_frame(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    values = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
    return values.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def auc_report(X: pd.DataFrame, y: pd.Series, seed: int) -> dict[str, float | None]:
    if y.nunique() < 2 or len(y) < 10:
        return {"mean_auc": None, "std_auc": None}
    folds = min(5, int(y.value_counts().min()))
    if folds < 2:
        return {"mean_auc": None, "std_auc": None}
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=seed))
    scores = cross_val_score(model, X, y, cv=StratifiedKFold(folds, shuffle=True, random_state=seed), scoring="roc_auc")
    return {"mean_auc": round(float(scores.mean()), 4), "std_auc": round(float(scores.std()), 4)}


def run_audit(frame: pd.DataFrame, label_col: str, seed: int) -> dict:
    if label_col not in frame.columns:
        raise ValueError(f"Label column tidak ditemukan: {label_col}")

    y = pd.to_numeric(frame[label_col], errors="coerce").fillna(0).astype(int)
    feature_cols = [column for column in frame.columns if column != label_col]
    feature_cols = [column for column in feature_cols if pd.api.types.is_numeric_dtype(frame[column])]
    suspect_cols = [column for column in feature_cols if any(token in column.upper() for token in SUSPECT_TOKENS)]
    X = numeric_frame(frame, feature_cols)

    correlations = {}
    for column in feature_cols:
        correlations[column] = round(float(X[column].corr(y) or 0.0), 4)

    shuffled = y.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    permuted_report = auc_report(X.reset_index(drop=True), shuffled, seed)
    ablated_cols = [column for column in feature_cols if column not in suspect_cols]
    ablated_report = auc_report(numeric_frame(frame, ablated_cols), y, seed)

    return {
        "rows": int(len(frame)),
        "label_column": label_col,
        "positive_rate": round(float(y.mean()), 4),
        "features": feature_cols,
        "suspect_proxy_features": suspect_cols,
        "feature_label_correlation": dict(sorted(correlations.items(), key=lambda item: abs(item[1]), reverse=True)),
        "all_features_cv_auc": auc_report(X, y, seed),
        "without_suspect_features_cv_auc": ablated_report,
        "permuted_label_cv_auc": permuted_report,
        "interpretation": [
            "Correlation is diagnostic only and is not evidence of fraud.",
            "A large drop after removing suspect features indicates proxy-label dependence.",
            "Permuted-label AUC near 0.5 is the minimum sanity check for split leakage.",
            "Independent reviewer labels are still required for clinical validity.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path, help="CSV, Parquet, or Stata feature table")
    parser.add_argument("--label-col", default="FRAUD_RISK")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    report = run_audit(load_frame(args.data), args.label_col, args.seed)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
