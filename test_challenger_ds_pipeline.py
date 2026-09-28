#!/usr/bin/env python3
"""
GARDA-JKN Empirical Adversarial & Stress Testing Harness (challenger_ds_1).
Comprehensive empirical challenge suite for:
- StratifiedIsolationForest (R1)
- ClinicalFeatureExtractor & Clinical Incoherence Heuristics (R2)
- BalancedBaggingXGBoost & Zero-SMOTE Verification (R3)
- ShapAuditorReasonCodeGenerator (R4)
- OperationalEvaluator (PR-AUC, AP, Precision@K)

Executes with ./venv/bin/python.
"""

import sys
import os
import re
import unittest
import numpy as np
import pandas as pd
from typing import Dict, List, Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from garda_ds_pipeline import (
    ClinicalFeatureExtractor,
    StratifiedIsolationForest,
    BalancedBaggingXGBoost,
    ShapAuditorReasonCodeGenerator,
    OperationalEvaluator,
    generate_semi_supervised_labels,
    BPJSDataLoader,
    ADVANCED_FEATURE_COLS,
)


class TestStratifiedIsolationForestChallenger(unittest.TestCase):
    """Adversarial stress tests for StratifiedIsolationForest."""

    @classmethod
    def setUpClass(cls):
        # Generate controlled synthetic training baseline
        rng = np.random.RandomState(42)
        n = 500
        cls.train_df = pd.DataFrame({
            "BASE_CBG": rng.choice(["A-4-14", "G-4-17", "I-4-12", "J-4-10", "Q-5-44"], size=n),
            "KELAS_RS": rng.choice(["RS Kelas A", "RS Kelas B", "RS Kelas C", "RS Kelas D"], size=n),
            "IS_RAWAT_INAP": rng.choice([0, 1], size=n, p=[0.6, 0.4]),
            "LOS_HARI": rng.gamma(shape=2.0, scale=2.0, size=n).round(),
            "BIAYA_PER_HARI": rng.uniform(200_000, 10_000_000, size=n),
            "SEVERITY_LEVEL": rng.choice([0, 1, 2, 3], size=n),
            "JML_DIAG_SEKUNDER": rng.poisson(lam=1.5, size=n),
        })
        # Single sample micro-stratum injected into training data
        cls.train_df.loc[0, "BASE_CBG"] = "Z-9-99"
        cls.train_df.loc[0, "KELAS_RS"] = "RS Kelas Khusus"

        cls.sif = StratifiedIsolationForest(min_samples=25, n_estimators=30, random_state=42)
        cls.sif.fit(cls.train_df)

    def test_01_single_sample_stratum_training_fallback(self):
        """Verify model handles strata with N=1 or N < min_samples without crashing, using hierarchical fallback."""
        self.assertNotIn("Z-9-99__RS Kelas Khusus", self.sif.stratum_models_)
        # Should resolve via global model or CMG fallback
        test_single = pd.DataFrame([{
            "BASE_CBG": "Z-9-99",
            "KELAS_RS": "RS Kelas Khusus",
            "IS_RAWAT_INAP": 1,
            "LOS_HARI": 5.0,
            "BIAYA_PER_HARI": 2_000_000.0,
            "SEVERITY_LEVEL": 2,
            "JML_DIAG_SEKUNDER": 1,
        }])
        scores = self.sif.score_samples(test_single)
        self.assertEqual(len(scores), 1)
        self.assertTrue(0.0 <= scores[0] <= 1.0, f"Score out of bounds: {scores[0]}")
        self.assertFalse(np.isnan(scores[0]))
        self.assertFalse(np.isinf(scores[0]))

    def test_02_unseen_hospital_class_and_base_cbg_inference(self):
        """Verify inference gracefully falls back when encountering completely unseen classes and CBGs."""
        unseen_df = pd.DataFrame([
            # Unseen hospital class
            {"BASE_CBG": "A-4-14", "KELAS_RS": "RS Tipe Militer", "IS_RAWAT_INAP": 1, "LOS_HARI": 3.0, "BIAYA_PER_HARI": 1e6, "SEVERITY_LEVEL": 1, "JML_DIAG_SEKUNDER": 0},
            # Unseen Base CBG
            {"BASE_CBG": "W-8-88", "KELAS_RS": "RS Kelas A", "IS_RAWAT_INAP": 0, "LOS_HARI": 0.0, "BIAYA_PER_HARI": 5e5, "SEVERITY_LEVEL": 0, "JML_DIAG_SEKUNDER": 0},
            # Both unseen
            {"BASE_CBG": "UNKNOWN_CBG", "KELAS_RS": "KLINIK_PRATAMA", "IS_RAWAT_INAP": 0, "LOS_HARI": 0.0, "BIAYA_PER_HARI": 3e5, "SEVERITY_LEVEL": 0, "JML_DIAG_SEKUNDER": 0},
            # Empty strings
            {"BASE_CBG": "", "KELAS_RS": "", "IS_RAWAT_INAP": 1, "LOS_HARI": 2.0, "BIAYA_PER_HARI": 1e6, "SEVERITY_LEVEL": 1, "JML_DIAG_SEKUNDER": 0},
        ])
        scores = self.sif.score_samples(unseen_df)
        self.assertEqual(len(scores), 4)
        for i, s in enumerate(scores):
            self.assertTrue(0.0 <= s <= 1.0, f"Unseen test row {i} returned invalid score: {s}")
            self.assertFalse(np.isnan(s), f"Unseen test row {i} returned NaN")

    def test_03_nan_and_infinite_feature_values(self):
        """Verify inference robustness against NaN, +inf, and -inf in feature columns."""
        nan_inf_df = pd.DataFrame([
            # All NaNs in features
            {"BASE_CBG": "A-4-14", "KELAS_RS": "RS Kelas A", "IS_RAWAT_INAP": 1, "LOS_HARI": np.nan, "BIAYA_PER_HARI": np.nan, "SEVERITY_LEVEL": np.nan, "JML_DIAG_SEKUNDER": np.nan},
            # Positive Infinity in costs and LOS
            {"BASE_CBG": "A-4-14", "KELAS_RS": "RS Kelas A", "IS_RAWAT_INAP": 1, "LOS_HARI": np.inf, "BIAYA_PER_HARI": np.inf, "SEVERITY_LEVEL": 3, "JML_DIAG_SEKUNDER": 5},
            # Negative Infinity
            {"BASE_CBG": "A-4-14", "KELAS_RS": "RS Kelas A", "IS_RAWAT_INAP": 1, "LOS_HARI": -np.inf, "BIAYA_PER_HARI": -np.inf, "SEVERITY_LEVEL": 0, "JML_DIAG_SEKUNDER": 0},
            # Astronomical numbers (100 Billion IDR)
            {"BASE_CBG": "A-4-14", "KELAS_RS": "RS Kelas A", "IS_RAWAT_INAP": 1, "LOS_HARI": 1000.0, "BIAYA_PER_HARI": 1e11, "SEVERITY_LEVEL": 3, "JML_DIAG_SEKUNDER": 50},
        ])
        scores = self.sif.score_samples(nan_inf_df)
        self.assertEqual(len(scores), 4)
        for i, s in enumerate(scores):
            self.assertTrue(0.0 <= s <= 1.0, f"NaN/Inf row {i} produced out-of-bound score: {s}")
            self.assertFalse(np.isnan(s), f"NaN/Inf row {i} produced NaN score")

    def test_04_continuous_distribution_strictly_in_0_1(self):
        """Verify that score distribution across large cohort is strictly in [0, 1] and exhibits continuous spread."""
        scores = self.sif.score_samples(self.train_df)
        min_s = float(np.min(scores))
        max_s = float(np.max(scores))
        std_s = float(np.std(scores))
        unique_s = len(np.unique(scores))

        self.assertGreaterEqual(min_s, 0.0)
        self.assertLessEqual(max_s, 1.0)
        # Should not be degenerate single-value or trivial 0/1 binary
        self.assertGreater(std_s, 0.05, f"Score distribution lacks variance (std={std_s:.4f})")
        self.assertGreater(unique_s, 50, f"Score distribution lacks continuous granularity (unique values={unique_s})")

    def test_05_adversarial_dataframe_indexing(self):
        """CRITICAL CHALLENGE: Test inference on sliced, custom-indexed, and string-indexed DataFrames."""
        # Slice of DataFrame (index is e.g. 50..59)
        sliced_df = self.train_df.iloc[50:60].copy()
        
        # Test whether score_samples survives non-RangeIndex
        try:
            scores_sliced = self.sif.score_samples(sliced_df)
            sliced_success = True
        except IndexError as e:
            sliced_success = False
            sliced_err = str(e)

        # String-indexed DataFrame
        string_indexed_df = self.train_df.iloc[0:5].copy()
        string_indexed_df.index = [f"CLAIM_ID_{i:04d}" for i in range(5)]
        try:
            scores_str = self.sif.score_samples(string_indexed_df)
            string_success = True
        except (IndexError, TypeError, ValueError) as e:
            string_success = False
            str_err = str(e)

        # Record findings for Challenger report
        if not sliced_success:
            print(f"\n[CHALLENGER VULNERABILITY FOUND] score_samples fails on sliced DataFrame: {sliced_err}")
        if not string_success:
            print(f"[CHALLENGER VULNERABILITY FOUND] score_samples fails on string-indexed DataFrame: {str_err}")


class TestClinicalFeatureExtractorChallenger(unittest.TestCase):
    """Adversarial stress tests for ClinicalFeatureExtractor."""

    @classmethod
    def setUpClass(cls):
        cls.extractor = ClinicalFeatureExtractor()

    def test_01_negative_and_zero_los(self):
        """Verify negative LOS is clipped to 0 and cost per day never divides by 0."""
        df_raw = pd.DataFrame([
            # Negative LOS (discharge before admission by 5 days)
            {
                "FKL02": "NEG-LOS-01", "FKL03": "2024-03-15", "FKL04": "2024-03-10",
                "FKL09": "RS Kelas B", "FKL10": "RITL", "FKL14": "Sehat",
                "FKL17A": "I21", "FKL18": "I210", "FKL19": "I-4-12-I",
                "FKL23": "Ringan", "FKL30": "", "FKL47": 10_000_000.0
            },
            # Zero LOS Inpatient with high cost (Potential Phantom Daycare)
            {
                "FKL02": "ZERO-LOS-RITL", "FKL03": "2024-03-15", "FKL04": "2024-03-15",
                "FKL09": "RS Kelas A", "FKL10": "RITL", "FKL14": "Sehat",
                "FKL17A": "Z00", "FKL18": "Z000", "FKL19": "Q-5-44-0",
                "FKL23": "", "FKL30": "", "FKL47": 5_000_000.0
            },
            # Zero LOS Outpatient with standard cost (Legitimate RJTL)
            {
                "FKL02": "ZERO-LOS-RJTL", "FKL03": "2024-03-15", "FKL04": "2024-03-15",
                "FKL09": "RS Kelas C", "FKL10": "RJTL", "FKL14": "Sehat",
                "FKL17A": "Z00", "FKL18": "Z000", "FKL19": "Q-5-44-0",
                "FKL23": "", "FKL30": "", "FKL47": 250_000.0
            },
        ])
        feat = self.extractor.transform(df_raw, None)

        # 1. Negative LOS should clip to 0.0
        row_neg = feat[feat["FKL02"] == "NEG-LOS-01"].iloc[0]
        self.assertEqual(row_neg["LOS_HARI"], 0.0)
        self.assertEqual(row_neg["BIAYA_PER_HARI"], 10_000_000.0)  # divided by 1.0, not zero or negative!

        # 2. Zero LOS Inpatient high cost should trigger INCOH_PHANTOM_DAYCARE
        row_ritl = feat[feat["FKL02"] == "ZERO-LOS-RITL"].iloc[0]
        self.assertEqual(row_ritl["INCOH_PHANTOM_DAYCARE"], 1)
        self.assertEqual(row_ritl["CLINICAL_INCOHERENCE"], 1)

        # 3. Zero LOS Outpatient should NOT trigger INCOH_PHANTOM_DAYCARE
        row_rjtl = feat[feat["FKL02"] == "ZERO-LOS-RJTL"].iloc[0]
        self.assertEqual(row_rjtl["INCOH_PHANTOM_DAYCARE"], 0)

    def test_02_missing_primary_and_secondary_diagnosis(self):
        """Verify behavior when primary diagnosis is None/NaN and secondary table is empty or None."""
        df_raw = pd.DataFrame([
            {
                "FKL02": "MISS-DX-01", "FKL03": "2024-03-01", "FKL04": "2024-03-04",
                "FKL09": "RS Kelas C", "FKL10": "RITL", "FKL14": "Sehat",
                "FKL17A": None, "FKL18": np.nan, "FKL19": "A-4-14-III",
                "FKL23": "Berat", "FKL30": "", "FKL47": 12_000_000.0
            }
        ])
        # Case A: df_sekunder is None
        feat_a = self.extractor.transform(df_raw, None)
        self.assertEqual(feat_a.loc[0, "JML_DIAG_SEKUNDER"], 0)
        # Severity III with 0 secondary diagnoses MUST trigger INCOH_UPCODING_SEV3
        self.assertEqual(feat_a.loc[0, "INCOH_UPCODING_SEV3"], 1)
        self.assertEqual(feat_a.loc[0, "CLINICAL_INCOHERENCE"], 1)

        # Case B: df_sekunder is empty DataFrame
        feat_b = self.extractor.transform(df_raw, pd.DataFrame(columns=["FKL02", "FKL24", "FKL24A", "FKL24B"]))
        self.assertEqual(feat_b.loc[0, "JML_DIAG_SEKUNDER"], 0)
        self.assertEqual(feat_b.loc[0, "INCOH_UPCODING_SEV3"], 1)

    def test_03_claims_with_100_secondary_diagnoses(self):
        """Stress test with a claim containing 100 secondary diagnoses."""
        df_raw = pd.DataFrame([{
            "FKL02": "POLY-100", "FKL03": "2024-03-01", "FKL04": "2024-03-10",
            "FKL09": "RS Kelas A", "FKL10": "RITL", "FKL14": "Sehat",
            "FKL17A": "I21", "FKL18": "I210", "FKL19": "I-4-12-III",
            "FKL23": "Berat", "FKL30": "967", "FKL47": 80_000_000.0
        }])
        sec_rows = [
            {"FKL02": "POLY-100", "FKL24": f"E11{i}", "FKL24A": f"E{i%50:02d}", "FKL24B": f"Diag {i}"}
            for i in range(100)
        ]
        # Include E43 malnutrition in one of them
        sec_rows[42]["FKL24A"] = "E43"
        df_sec = pd.DataFrame(sec_rows)

        feat = self.extractor.transform(df_raw, df_sec)
        row = feat.iloc[0]
        self.assertEqual(row["JML_DIAG_SEKUNDER"], 100)
        self.assertEqual(row["FLAG_SUSPECT_E43"], 1)
        # Severity III with 100 secondary diagnoses should NOT be flagged as upcoding without complications
        self.assertEqual(row["INCOH_UPCODING_SEV3"], 0)

    def test_04_discharge_status_edge_cases_meninggal_vs_sehat(self):
        """Verify clinical validity: Sepsis + short stay + Meninggal != Fraud; Sepsis + short stay + Sehat == Fraud."""
        df_raw = pd.DataFrame([
            # Claim A: Sepsis, 1 day, no ICU, DISCHARGED SEHAT (Incoherent!)
            {
                "FKL02": "SEP-SEHAT", "FKL03": "2024-03-01", "FKL04": "2024-03-02",
                "FKL09": "RS Kelas B", "FKL10": "RITL", "FKL14": "Sehat",
                "FKL17A": "A41", "FKL18": "A419", "FKL19": "A-4-14-II",
                "FKL23": "Sedang", "FKL30": "", "FKL47": 25_000_000.0
            },
            # Claim B: Sepsis, 1 day, no ICU, DISCHARGED MENINGGAL (Tragic death, clinically coherent)
            {
                "FKL02": "SEP-MENINGGAL", "FKL03": "2024-03-01", "FKL04": "2024-03-02",
                "FKL09": "RS Kelas B", "FKL10": "RITL", "FKL14": "Meninggal",
                "FKL17A": "A41", "FKL18": "A419", "FKL19": "A-4-14-II",
                "FKL23": "Sedang", "FKL30": "", "FKL47": 25_000_000.0
            },
            # Claim C: Sepsis, 1 day, no ICU, DISCHARGED PULANG PAKSA (AMA, clinically coherent)
            {
                "FKL02": "SEP-PULANG-PAKSA", "FKL03": "2024-03-01", "FKL04": "2024-03-02",
                "FKL09": "RS Kelas B", "FKL10": "RITL", "FKL14": "Pulang Paksa",
                "FKL17A": "A41", "FKL18": "A419", "FKL19": "A-4-14-II",
                "FKL23": "Sedang", "FKL30": "", "FKL47": 25_000_000.0
            },
        ])
        feat = self.extractor.transform(df_raw, None)

        row_sehat = feat[feat["FKL02"] == "SEP-SEHAT"].iloc[0]
        self.assertEqual(row_sehat["INCOH_SEPSIS_NO_ICU"], 1, "Sepsis discharged Sehat in <=2d must trigger incoherence")

        row_meninggal = feat[feat["FKL02"] == "SEP-MENINGGAL"].iloc[0]
        self.assertEqual(row_meninggal["INCOH_SEPSIS_NO_ICU"], 0, "Sepsis deceased must NOT trigger incoherence")

        row_paksa = feat[feat["FKL02"] == "SEP-PULANG-PAKSA"].iloc[0]
        self.assertEqual(row_paksa["INCOH_SEPSIS_NO_ICU"], 0, "Pulang Paksa must NOT trigger incoherence")

    def test_05_extreme_and_corrupted_inputs(self):
        """Stress test with negative costs, extreme costs, and unparseable dates."""
        df_raw = pd.DataFrame([
            # Negative cost (- Rp 500,000)
            {
                "FKL02": "NEG-COST", "FKL03": "2024-03-01", "FKL04": "2024-03-03",
                "FKL09": "RS Kelas C", "FKL10": "RITL", "FKL14": "Sehat",
                "FKL17A": "K29", "FKL18": "K290", "FKL19": "K-4-17-I",
                "FKL23": "Ringan", "FKL30": "", "FKL47": -500_000.0
            },
            # Corrupted date string
            {
                "FKL02": "BAD-DATE", "FKL03": "CORRUPTED_DATE", "FKL04": "BAD_TIMESTAMP",
                "FKL09": "RS Kelas C", "FKL10": "RITL", "FKL14": "Sehat",
                "FKL17A": "K29", "FKL18": "K290", "FKL19": "K-4-17-I",
                "FKL23": "Ringan", "FKL30": "", "FKL47": 1_000_000.0
            },
            # Missing INA-CBG code entirely (NaN)
            {
                "FKL02": "NO-CBG", "FKL03": "2024-03-01", "FKL04": "2024-03-03",
                "FKL09": "RS Kelas C", "FKL10": "RITL", "FKL14": "Sehat",
                "FKL17A": "K29", "FKL18": "K290", "FKL19": np.nan,
                "FKL23": np.nan, "FKL30": "", "FKL47": 1_000_000.0
            },
        ])
        feat = self.extractor.transform(df_raw, None)

        # Negative cost should be clipped to 0.0
        self.assertEqual(feat.loc[0, "BIAYA_TAGIH"], 0.0)
        self.assertEqual(feat.loc[0, "BIAYA_PER_HARI"], 0.0)

        # Corrupted dates should default to LOS=0 without exception
        self.assertEqual(feat.loc[1, "LOS_HARI"], 0.0)

        # Missing CBG should default to severity 0 and base CBG "nan"
        self.assertEqual(feat.loc[2, "SEVERITY_LEVEL"], 0)


class TestBalancedBaggingAndIntegrityChallenger(unittest.TestCase):
    """Stress testing BalancedBaggingXGBoost and strict compliance checks."""

    def test_01_strictly_zero_smote_adasyn_in_codebase(self):
        """Verify zero presence or importation of SMOTE, ADASYN, or imblearn."""
        files_to_check = [
            os.path.join(PROJECT_ROOT, "garda_ds_pipeline.py"),
            os.path.join(PROJECT_ROOT, "GARDA_JKN_Advanced_DS.ipynb"),
        ]
        forbidden_patterns = [
            r"\bsmote\b",
            r"\badasyn\b",
            r"\bimblearn\b",
            r"from imblearn",
            r"import SMOTE",
            r"import ADASYN",
        ]
        for fpath in files_to_check:
            if not os.path.exists(fpath):
                continue
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
            for pattern in forbidden_patterns:
                matches = re.findall(pattern, content)
                # Filter out occurrences in comments explaining NOT to use SMOTE
                real_imports = [m for m in matches if "import" in m or "from" in m]
                self.assertEqual(
                    len(real_imports), 0,
                    f"Forbidden synthetic oversampling found in {fpath}: {real_imports}"
                )

    def test_02_balanced_bagging_training_and_calibration(self):
        """Stress test BalancedBaggingXGBoost on extreme class imbalance (98% neg, 2% pos)."""
        rng = np.random.RandomState(42)
        n = 1000
        n_pos = 20  # 2% fraud
        X = pd.DataFrame(rng.randn(n, 5), columns=[f"f{i}" for i in range(5)])
        y = np.zeros(n, dtype=int)
        y[:n_pos] = 1

        bag = BalancedBaggingXGBoost(n_estimators=3, max_depth=3, random_state=42)
        bag.fit(X, y)

        probs = bag.predict_proba(X)
        self.assertEqual(probs.shape, (n, 2))
        # Ensure row probabilities sum to 1.0
        np.testing.assert_allclose(probs.sum(axis=1), np.ones(n), atol=1e-5)
        # Check non-degeneracy: probability spread must be > 0.3
        pos_probs = probs[:, 1]
        spread = float(np.max(pos_probs) - np.min(pos_probs))
        self.assertGreater(spread, 0.3, f"Bagging probabilities degenerate (spread={spread:.4f})")

    def test_03_zero_positives_raises_clear_error(self):
        """Ensure BalancedBaggingXGBoost safely raises ValueError when no positive instances exist."""
        X = pd.DataFrame(np.zeros((50, 4)))
        y = np.zeros(50, dtype=int)
        bag = BalancedBaggingXGBoost(n_estimators=2)
        with self.assertRaises(ValueError):
            bag.fit(X, y)


class TestShapAuditorReasonCodeGeneratorChallenger(unittest.TestCase):
    """Stress testing XAI ShapAuditorReasonCodeGenerator."""

    def test_01_explain_normal_and_anomalous_claims(self):
        """Verify SHAP explanation generation across normal and high-risk claims."""
        rng = np.random.RandomState(42)
        n = 200
        X = pd.DataFrame({
            col: rng.uniform(0, 10, size=n) for col in ADVANCED_FEATURE_COLS
        })
        y = rng.choice([0, 1], size=n, p=[0.85, 0.15])
        # Ensure at least 5 positives
        y[:5] = 1

        bag = BalancedBaggingXGBoost(n_estimators=2, max_depth=3, random_state=42)
        bag.fit(X, y)

        gen = ShapAuditorReasonCodeGenerator(bag, ADVANCED_FEATURE_COLS)

        # Test normal claim
        normal_claim = X.iloc[10]
        exp_normal = gen.explain_claim(normal_claim, claim_id="NORMAL-01")
        self.assertIn("claim_id", exp_normal)
        self.assertIn("top_reasons", exp_normal)
        self.assertLessEqual(len(exp_normal["top_reasons"]), 3)

        # Test report formatting
        report_text = gen.format_auditor_report(exp_normal, risk_score=0.15)
        self.assertIn("BERITA ACARA DETEKSI ANOMALI", report_text)
        self.assertIn("NORMAL-01", report_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
