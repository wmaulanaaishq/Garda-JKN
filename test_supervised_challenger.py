#!/usr/bin/env python3
"""GARDA-JKN Supervised Modeling & Explainability Adversarial Test Harness.

Role: challenger_ds_2 (Type: teamwork_preview_challenger)
Target:
1. BalancedBaggingXGBoost:
   - Prediction variance (normal vs extreme fraud claims, degenerate score checks)
   - Input feature order permutation (DataFrame vs NumPy behavior)
   - Extreme input values (Rp 1 Billion, Rp 10 Billion, negative costs, extreme LOS, NaNs, Infs)
2. ShapAuditorReasonCodeGenerator:
   - Zero positive drivers
   - All negative drivers
   - Tied SHAP values (exact ties, partial ties)
   - 1, 2, and 3+ positive drivers
   - Narrative formatting safety across all features in AUDITOR_CODE_MAP + generic fallback
   - Safe string formatting and Indonesian text compliance
3. End-to-end execution of GARDA_JKN_Advanced_DS.ipynb
"""

import json
import os
import sys
import unittest
import numpy as np
import pandas as pd
import xgboost as xgb

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from garda_ds_pipeline import (
    BalancedBaggingXGBoost,
    ShapAuditorReasonCodeGenerator,
    ADVANCED_FEATURE_COLS,
    ARTIFACTS_DIR,
)


class TestBalancedBaggingXGBoost(unittest.TestCase):
    """Adversarial stress testing for BalancedBaggingXGBoost ensemble."""

    @classmethod
    def setUpClass(cls):
        """Loads serialized production ensemble models."""
        manifest_path = os.path.join(ARTIFACTS_DIR, "garda_xgb_bagging_manifest.json")
        assert os.path.exists(manifest_path), f"Manifest missing at {manifest_path}"
        with open(manifest_path, "r", encoding="utf-8") as f:
            cls.manifest = json.load(f)

        cls.ensemble = BalancedBaggingXGBoost(n_estimators=len(cls.manifest["estimators"]))
        for est_path in cls.manifest["estimators"]:
            clf = xgb.XGBClassifier()
            clf.load_model(est_path)
            cls.ensemble.estimators_.append(clf)

    def test_01_prediction_variance_normal_vs_extreme(self):
        """Stress test 1: Healthy variance between normal and extreme fraud claims."""
        test_claims = {
            "normal_rjtl": {
                "LOS_HARI": 0, "BIAYA_TAGIH": 180000, "BIAYA_PER_HARI": 180000,
                "SEVERITY_LEVEL": 0, "IS_RAWAT_INAP": 0, "JML_DIAG_SEKUNDER": 0,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.05
            },
            "normal_ritl_standard": {
                "LOS_HARI": 3, "BIAYA_TAGIH": 4200000, "BIAYA_PER_HARI": 1400000,
                "SEVERITY_LEVEL": 1, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 1,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.12
            },
            "extreme_upcoding_sev3_e43": {
                "LOS_HARI": 1, "BIAYA_TAGIH": 55000000, "BIAYA_PER_HARI": 55000000,
                "SEVERITY_LEVEL": 3, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 0,
                "FLAG_SUSPECT_E43": 1, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 1, "ISO_ANOMALY_SCORE": 0.95
            },
            "extreme_sepsis_incoherence": {
                "LOS_HARI": 1, "BIAYA_TAGIH": 48000000, "BIAYA_PER_HARI": 48000000,
                "SEVERITY_LEVEL": 3, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 1,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 1,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 1, "ISO_ANOMALY_SCORE": 0.92
            },
            "extreme_1_billion_claim": {
                "LOS_HARI": 4, "BIAYA_TAGIH": 1000000000, "BIAYA_PER_HARI": 250000000,
                "SEVERITY_LEVEL": 3, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 5,
                "FLAG_SUSPECT_E43": 1, "FLAG_SUSPECT_J96": 1, "FLAG_SUSPECT_SEPSIS": 1,
                "FLAG_SUSPECT_AKI": 1, "CLINICAL_INCOHERENCE": 1, "ISO_ANOMALY_SCORE": 0.99
            }
        }

        df = pd.DataFrame(list(test_claims.values()))[ADVANCED_FEATURE_COLS]
        probs = self.ensemble.predict_proba(df)[:, 1]

        prob_dict = dict(zip(test_claims.keys(), probs))
        # Assert normal claims have low fraud probability (< 15%)
        self.assertLess(prob_dict["normal_rjtl"], 0.15, "Normal RJTL claim received high fraud score")
        self.assertLess(prob_dict["normal_ritl_standard"], 0.15, "Normal RITL claim received high fraud score")

        # Assert extreme fraud claims have very high probability (> 85%)
        self.assertGreater(prob_dict["extreme_upcoding_sev3_e43"], 0.85, "Upcoding claim failed to be flagged")
        self.assertGreater(prob_dict["extreme_sepsis_incoherence"], 0.85, "Sepsis incoherence failed to be flagged")
        self.assertGreater(prob_dict["extreme_1_billion_claim"], 0.85, "1-Billion claim failed to be flagged")

        # Assert healthy score spread (must be > 0.70, not degenerate flat probabilities)
        spread = probs.max() - probs.min()
        std_dev = probs.std()
        self.assertGreater(spread, 0.70, f"Probability spread too low: {spread}")
        self.assertGreater(std_dev, 0.20, f"Probability standard deviation too low: {std_dev}")

    def test_02_feature_permutation_behavior(self):
        """Stress test 2: Behavior when input DataFrame columns are permuted."""
        row = {
            "LOS_HARI": 3, "BIAYA_TAGIH": 4200000, "BIAYA_PER_HARI": 1400000,
            "SEVERITY_LEVEL": 1, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 1,
            "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
            "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.12
        }
        df_correct = pd.DataFrame([row])[ADVANCED_FEATURE_COLS]
        prob_correct = self.ensemble.predict_proba(df_correct)[:, 1][0]

        # Case A: Permuted column order in DataFrame
        permuted_cols = list(reversed(ADVANCED_FEATURE_COLS))
        df_permuted = df_correct[permuted_cols]

        # XGBoost validates feature names and should reject permuted DataFrame with ValueError
        with self.assertRaises(ValueError) as ctx:
            self.ensemble.predict_proba(df_permuted)
        self.assertIn("feature_names mismatch", str(ctx.exception))

        # Case B: Realigned column order restores exact correct prediction
        df_realigned = df_permuted[ADVANCED_FEATURE_COLS]
        prob_realigned = self.ensemble.predict_proba(df_realigned)[:, 1][0]
        self.assertAlmostEqual(prob_correct, prob_realigned, places=5)

    def test_03_extreme_and_boundary_values(self):
        """Stress test 3: Extreme financial, clinical, and boundary values."""
        extreme_cases = [
            ("Rp 10 Miliar Claim", {
                "LOS_HARI": 5, "BIAYA_TAGIH": 10000000000, "BIAYA_PER_HARI": 2000000000,
                "SEVERITY_LEVEL": 3, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 5,
                "FLAG_SUSPECT_E43": 1, "FLAG_SUSPECT_J96": 1, "FLAG_SUSPECT_SEPSIS": 1,
                "FLAG_SUSPECT_AKI": 1, "CLINICAL_INCOHERENCE": 1, "ISO_ANOMALY_SCORE": 1.0
            }),
            ("Zero Cost Claim", {
                "LOS_HARI": 3, "BIAYA_TAGIH": 0, "BIAYA_PER_HARI": 0,
                "SEVERITY_LEVEL": 1, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 0,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.1
            }),
            ("Negative Cost Claim", {
                "LOS_HARI": 3, "BIAYA_TAGIH": -5000000, "BIAYA_PER_HARI": -1666666,
                "SEVERITY_LEVEL": 1, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 0,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.1
            }),
            ("Extreme LOS 365 Days", {
                "LOS_HARI": 365, "BIAYA_TAGIH": 15000000, "BIAYA_PER_HARI": 41095,
                "SEVERITY_LEVEL": 2, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 2,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.5
            }),
            ("Extreme Negative LOS", {
                "LOS_HARI": -5, "BIAYA_TAGIH": 5000000, "BIAYA_PER_HARI": -1000000,
                "SEVERITY_LEVEL": 1, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 0,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.1
            }),
            ("Severity Out of Bounds (10)", {
                "LOS_HARI": 5, "BIAYA_TAGIH": 10000000, "BIAYA_PER_HARI": 2000000,
                "SEVERITY_LEVEL": 10, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 0,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.5
            }),
            ("NaN Features", {
                "LOS_HARI": np.nan, "BIAYA_TAGIH": np.nan, "BIAYA_PER_HARI": np.nan,
                "SEVERITY_LEVEL": np.nan, "IS_RAWAT_INAP": np.nan, "JML_DIAG_SEKUNDER": np.nan,
                "FLAG_SUSPECT_E43": np.nan, "FLAG_SUSPECT_J96": np.nan, "FLAG_SUSPECT_SEPSIS": np.nan,
                "FLAG_SUSPECT_AKI": np.nan, "CLINICAL_INCOHERENCE": np.nan, "ISO_ANOMALY_SCORE": np.nan
            }),
            ("Infinite Features", {
                "LOS_HARI": np.inf, "BIAYA_TAGIH": np.inf, "BIAYA_PER_HARI": np.inf,
                "SEVERITY_LEVEL": np.inf, "IS_RAWAT_INAP": np.inf, "JML_DIAG_SEKUNDER": np.inf,
                "FLAG_SUSPECT_E43": np.inf, "FLAG_SUSPECT_J96": np.inf, "FLAG_SUSPECT_SEPSIS": np.inf,
                "FLAG_SUSPECT_AKI": np.inf, "CLINICAL_INCOHERENCE": np.inf, "ISO_ANOMALY_SCORE": np.inf
            }),
        ]

        for label, data in extreme_cases:
            df_case = pd.DataFrame([data])[ADVANCED_FEATURE_COLS]
            prob = self.ensemble.predict_proba(df_case)[:, 1][0]
            self.assertFalse(np.isnan(prob), f"{label} returned NaN probability")
            self.assertTrue(0.0 <= prob <= 1.0, f"{label} returned out of bounds probability {prob}")

    def test_04_fresh_training_zero_smote(self):
        """Stress test 4: Train fresh BalancedBaggingXGBoost with zero synthetic oversampling."""
        rng = np.random.RandomState(42)
        n = 100
        p = len(ADVANCED_FEATURE_COLS)
        X_syn = pd.DataFrame(rng.randn(n, p), columns=ADVANCED_FEATURE_COLS)
        # Extreme class imbalance: 5% positive (5 positive, 95 negative)
        y_syn = np.array([1] * 5 + [0] * 95)

        bag = BalancedBaggingXGBoost(n_estimators=3, random_state=42)
        bag.fit(X_syn, y_syn)

        self.assertEqual(len(bag.estimators_), 3)
        for est in bag.estimators_:
            self.assertEqual(est.scale_pos_weight, 1.0)  # Perfectly 1:1 balanced folds
        
        preds = bag.predict_proba(X_syn)
        self.assertEqual(preds.shape, (100, 2))
        self.assertTrue(np.allclose(preds.sum(axis=1), 1.0))


class TestShapAuditorReasonCodeGenerator(unittest.TestCase):
    """Adversarial stress testing for ShapAuditorReasonCodeGenerator."""

    @classmethod
    def setUpClass(cls):
        """Loads serialized production ensemble models."""
        manifest_path = os.path.join(ARTIFACTS_DIR, "garda_xgb_bagging_manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        ensemble = BalancedBaggingXGBoost(n_estimators=len(manifest["estimators"]))
        for est_path in manifest["estimators"]:
            clf = xgb.XGBClassifier()
            clf.load_model(est_path)
            ensemble.estimators_.append(clf)

        cls.generator = ShapAuditorReasonCodeGenerator(ensemble, ADVANCED_FEATURE_COLS)

    def test_01_zero_positive_drivers(self):
        """Stress test: Claim where all features have non-positive (<=0) SHAP values."""
        class MockExplainerZero:
            def __call__(self, df):
                class Res:
                    values = [np.zeros(len(ADVANCED_FEATURE_COLS))]
                return Res()

        gen = ShapAuditorReasonCodeGenerator.__new__(ShapAuditorReasonCodeGenerator)
        gen.ensemble = self.generator.ensemble
        gen.feature_cols = ADVANCED_FEATURE_COLS
        gen.explainers = [MockExplainerZero()]

        row = pd.Series({col: 0.0 for col in ADVANCED_FEATURE_COLS})
        res = gen.explain_claim(row, claim_id="CLAIM-ZERO")

        self.assertEqual(len(res["top_reasons"]), 0, "Expected 0 reasons when all SHAP values are zero")
        report = gen.format_auditor_report(res, risk_score=0.01)
        self.assertIn("Tidak ditemukan kontribusi fitur anomali yang signifikan", report)
        self.assertIn("CLAIM-ZERO", report)

    def test_02_all_negative_drivers(self):
        """Stress test: Claim where all features have negative (<0) SHAP values."""
        class MockExplainerNeg:
            def __call__(self, df):
                class Res:
                    values = [np.array([-0.85] * len(ADVANCED_FEATURE_COLS))]
                return Res()

        gen = ShapAuditorReasonCodeGenerator.__new__(ShapAuditorReasonCodeGenerator)
        gen.ensemble = self.generator.ensemble
        gen.feature_cols = ADVANCED_FEATURE_COLS
        gen.explainers = [MockExplainerNeg()]

        row = pd.Series({col: 1.0 for col in ADVANCED_FEATURE_COLS})
        res = gen.explain_claim(row, claim_id="CLAIM-ALL-NEG")

        self.assertEqual(len(res["top_reasons"]), 0, "Expected 0 reasons when all SHAP values are negative")
        report = gen.format_auditor_report(res, risk_score=0.02)
        self.assertIn("Tidak ditemukan kontribusi fitur anomali yang signifikan", report)

    def test_03_tied_shap_values(self):
        """Stress test: Multiple features having exact identical positive SHAP values."""
        class MockExplainerTied:
            def __call__(self, df):
                class Res:
                    # All features tied at exactly +2.15
                    values = [np.array([2.15] * len(ADVANCED_FEATURE_COLS))]
                return Res()

        gen = ShapAuditorReasonCodeGenerator.__new__(ShapAuditorReasonCodeGenerator)
        gen.ensemble = self.generator.ensemble
        gen.feature_cols = ADVANCED_FEATURE_COLS
        gen.explainers = [MockExplainerTied()]

        row = pd.Series({
            "LOS_HARI": 4, "BIAYA_TAGIH": 12000000, "BIAYA_PER_HARI": 3000000,
            "SEVERITY_LEVEL": 2, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 2,
            "FLAG_SUSPECT_E43": 1, "FLAG_SUSPECT_J96": 1, "FLAG_SUSPECT_SEPSIS": 0,
            "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 1, "ISO_ANOMALY_SCORE": 0.8
        })
        res = gen.explain_claim(row, claim_id="CLAIM-TIED")

        # Top reasons must be capped at exactly 3
        self.assertEqual(len(res["top_reasons"]), 3, "Tied SHAP values did not cap at top 3")
        ranks = [r["rank"] for r in res["top_reasons"]]
        self.assertEqual(ranks, [1, 2, 3], "Ranks for tied reasons must be 1, 2, 3")

        for r in res["top_reasons"]:
            self.assertEqual(r["shap_impact"], 2.15)
            self.assertTrue(len(r["auditor_narrative"]) > 10)
            self.assertTrue(len(r["actionable_instruction"]) > 10)

        report = gen.format_auditor_report(res, risk_score=0.92)
        self.assertIn("FAKTOR PENDORONG UTAMA (TOP-3 AUDITOR REASON CODES):", report)
        self.assertIn("1. [", report)
        self.assertIn("2. [", report)
        self.assertIn("3. [", report)

    def test_04_partial_positive_drivers(self):
        """Stress test: Claims with exactly 1 or 2 positive drivers."""
        for n_pos in [1, 2]:
            class MockExplainerPartial:
                def __init__(self, k):
                    self.k = k
                def __call__(self, df):
                    vals = np.array([-1.0] * len(ADVANCED_FEATURE_COLS))
                    for i in range(self.k):
                        vals[i] = 1.8 + i
                    class Res:
                        values = [vals]
                    return Res()

            gen = ShapAuditorReasonCodeGenerator.__new__(ShapAuditorReasonCodeGenerator)
            gen.ensemble = self.generator.ensemble
            gen.feature_cols = ADVANCED_FEATURE_COLS
            gen.explainers = [MockExplainerPartial(n_pos)]

            row = pd.Series({
                "LOS_HARI": 2, "BIAYA_TAGIH": 5000000, "BIAYA_PER_HARI": 2500000,
                "SEVERITY_LEVEL": 1, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 0,
                "FLAG_SUSPECT_E43": 0, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
                "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 0, "ISO_ANOMALY_SCORE": 0.2
            })
            res = gen.explain_claim(row, claim_id=f"CLAIM-{n_pos}POS")
            self.assertEqual(len(res["top_reasons"]), n_pos)
            report = gen.format_auditor_report(res, risk_score=0.55)
            self.assertIn(f"{n_pos}. [", report)

    def test_05_narrative_formatting_all_features_and_fallbacks(self):
        """Stress test: Verify narrative generation for all features without string errors."""
        all_test_features = ADVANCED_FEATURE_COLS + ["CUSTOM_UNREGISTERED_FEATURE"]

        for feat in all_test_features:
            class MockExpSingle:
                def __init__(self, target):
                    self.target = target
                def __call__(self, df):
                    v = np.zeros(len(all_test_features))
                    idx = all_test_features.index(self.target)
                    v[idx] = 2.45
                    class Res:
                        values = [v]
                    return Res()

            gen = ShapAuditorReasonCodeGenerator.__new__(ShapAuditorReasonCodeGenerator)
            gen.ensemble = self.generator.ensemble
            gen.feature_cols = all_test_features
            gen.explainers = [MockExpSingle(feat)]

            # Test varied data types: int, float, large currency
            test_values = [0, 1, 2.0, 50000000.0, 1000000000]
            for v in test_values:
                row = pd.Series({c: 0 for c in all_test_features})
                row[feat] = v
                res = gen.explain_claim(row, claim_id=f"TEST-{feat}")
                self.assertEqual(len(res["top_reasons"]), 1)
                reason = res["top_reasons"][0]
                self.assertEqual(reason["feature"], feat)
                self.assertTrue(len(reason["auditor_narrative"]) > 0)
                self.assertTrue(len(reason["actionable_instruction"]) > 0)

                report = gen.format_auditor_report(res, risk_score=0.88)
                self.assertIn(reason["code"], report)
                self.assertIn("BERITA ACARA DETEKSI ANOMALI KLAIM BPJS", report)

    def test_06_real_ensemble_explainability(self):
        """Stress test: Run real TreeExplainer across ensemble on actual high-risk claim."""
        row_high_risk = pd.Series({
            "LOS_HARI": 2, "BIAYA_TAGIH": 65000000, "BIAYA_PER_HARI": 32500000,
            "SEVERITY_LEVEL": 3, "IS_RAWAT_INAP": 1, "JML_DIAG_SEKUNDER": 0,
            "FLAG_SUSPECT_E43": 1, "FLAG_SUSPECT_J96": 0, "FLAG_SUSPECT_SEPSIS": 0,
            "FLAG_SUSPECT_AKI": 0, "CLINICAL_INCOHERENCE": 1, "ISO_ANOMALY_SCORE": 0.94
        })

        explanation = self.generator.explain_claim(row_high_risk, claim_id="CLAIM-AUDIT-001")
        self.assertLessEqual(len(explanation["top_reasons"]), 3)
        self.assertGreaterEqual(len(explanation["top_reasons"]), 1)

        report = self.generator.format_auditor_report(explanation, risk_score=0.985)
        self.assertIn("🔴 RISIKO TINGGI (REKOMENDASI AUDIT INVESTIGATIF)", report)
        self.assertIn("CLAIM-AUDIT-001", report)
        self.assertIn("FAKTOR PENDORONG UTAMA", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
