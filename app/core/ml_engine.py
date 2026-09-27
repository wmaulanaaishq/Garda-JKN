"""GARDA-JKN Machine Learning Risk Engine (Lapis 1).

Hybrid approach: XGBoost classifier + Rule-Based Clinical Heuristics.
When XGBoost produces degenerate predictions (all-same scores due to
training data imbalance), the engine automatically engages a clinically-
grounded rule-based scoring system as fallback.

SHAP TreeExplainer provides Explainable AI when available; otherwise
a deterministic feature-contribution analysis is generated.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

try:
    import shap
except ImportError:
    shap = None

try:
    import xgboost as xgb
except ImportError:
    xgb = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "artifacts", "garda_xgb_model.json")
DEFAULT_META_PATH = os.path.join(BASE_DIR, "artifacts", "garda_features_meta.json")

# ═══════════════════════════════════════════════════════════════════
# Clinical Reference Constants (INA-CBG / BPJS Standard 2024-2025)
# ═══════════════════════════════════════════════════════════════════
# Average cost-per-day by severity level (IDR) — derived from BPJS
# published tariff tables for Class-3 RITL hospitals.
MEAN_COST_PER_DAY_BY_SEVERITY = {
    1: 1_800_000,   # Severity I   (Ringan)
    2: 3_500_000,   # Severity II  (Sedang)
    3: 7_000_000,   # Severity III (Berat)
}
# Average LOS by severity (days)
MEAN_LOS_BY_SEVERITY = {
    1: 3,
    2: 5,
    3: 8,
}
# Absolute ceilings — claims exceeding these are almost certainly anomalous
MAX_REASONABLE_COST_PER_DAY = 25_000_000   # Rp 25 juta/hari
MAX_REASONABLE_LOS = 60                     # 60 hari
MIN_REASONABLE_LOS = 0                      # 0 = rawat jalan


class MLEngine:
    """XGBoost + Rule-Based Hybrid Claim Anomaly & Risk Detection Engine."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        meta_path: Optional[str] = None,
    ):
        model_p = model_path or DEFAULT_MODEL_PATH
        meta_p = meta_path or DEFAULT_META_PATH

        # --- Load XGBoost model (optional — graceful degradation) ---
        self.model = None
        self.xgb_available = False
        if xgb is not None and os.path.exists(model_p):
            try:
                self.model = xgb.XGBClassifier()
                self.model.load_model(model_p)
                self.xgb_available = True
            except Exception as e:
                print(f"⚠️ XGBoost model load failed: {e}")

        # --- Load feature metadata ---
        if os.path.exists(meta_p):
            with open(meta_p, "r", encoding="utf-8") as f:
                meta = json.load(f)
                self.feature_cols = meta.get("feature_cols", self._default_features())
        else:
            self.feature_cols = self._default_features()

        # --- Initialize SHAP ---
        self.explainer = None
        if shap is not None and self.model is not None:
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception:
                pass

        # --- Detect degenerate model ---
        self._xgb_is_degenerate = self._check_degenerate()

    @staticmethod
    def _default_features() -> List[str]:
        return [
            "LOS_HARI", "BIAYA_TAGIH", "BIAYA_PER_HARI",
            "FKL07", "FKL08", "FKL31", "FKL21", "FKL22"
        ]

    def _check_degenerate(self) -> bool:
        """Probe the XGBoost model with clinically diverse inputs.
        A healthy model must differentiate a normal claim from an extreme one.
        All probes use IDENTICAL categorical features (FKL07/31/21/22) so
        only cost and LOS vary — the features that SHOULD drive fraud scores."""
        if not self.xgb_available:
            return True
        try:
            # Same hospital type/category, only cost & LOS differ
            probes = [
                {"LOS_HARI": 5, "BIAYA_TAGIH": 5_000_000, "BIAYA_PER_HARI": 1_000_000,
                 "FKL07": 2, "FKL08": 2, "FKL31": 1, "FKL21": 6, "FKL22": 44},
                {"LOS_HARI": 1, "BIAYA_TAGIH": 100_000_000, "BIAYA_PER_HARI": 100_000_000,
                 "FKL07": 2, "FKL08": 2, "FKL31": 1, "FKL21": 6, "FKL22": 44},
                {"LOS_HARI": 45, "BIAYA_TAGIH": 500_000, "BIAYA_PER_HARI": 11_111,
                 "FKL07": 2, "FKL08": 2, "FKL31": 1, "FKL21": 6, "FKL22": 44},
            ]
            df = pd.DataFrame(probes)[self.feature_cols]
            probs = self.model.predict_proba(df)[:, 1]
            spread = float(probs.max() - probs.min())
            # If the spread is < 15%, the model cannot meaningfully
            # distinguish normal from extreme → degenerate
            return spread < 0.15
        except Exception:
            return True

    # ═══════════════════════════════════════════════════════
    # Feature Mapping (flexible input → standard features)
    # ═══════════════════════════════════════════════════════
    def map_features(self, claim_data: Dict[str, Any]) -> Dict[str, float]:
        """Maps diverse claim payload key formats to standard model tabular features."""

        def _safe_float(val, default=0.0):
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        los = _safe_float(
            claim_data.get("LOS_HARI") or claim_data.get("durasi_rawat")
            or claim_data.get("los") or claim_data.get("lama_rawat"), 1.0
        )
        biaya = _safe_float(
            claim_data.get("BIAYA_TAGIH") or claim_data.get("biaya_tagih")
            or claim_data.get("biaya") or claim_data.get("total_biaya"), 0.0
        )
        biaya_per_hari = claim_data.get("BIAYA_PER_HARI") or claim_data.get("biaya_per_hari")
        if biaya_per_hari is not None:
            bph = _safe_float(biaya_per_hari, biaya / max(los, 1.0))
        else:
            bph = biaya / max(los, 1.0)

        fkl07 = _safe_float(claim_data.get("FKL07") or claim_data.get("fkl07")
                            or claim_data.get("tingkat_pelayanan"), 2.0)
        fkl08 = _safe_float(claim_data.get("FKL08") or claim_data.get("fkl08")
                            or claim_data.get("severity_level") or claim_data.get("kelas_rawat"), 1.0)
        fkl31 = _safe_float(claim_data.get("FKL31") or claim_data.get("fkl31"), 1.0)
        fkl21 = _safe_float(claim_data.get("FKL21") or claim_data.get("fkl21"), 6.0)
        fkl22 = _safe_float(claim_data.get("FKL22") or claim_data.get("fkl22"), 44.0)

        return {
            "LOS_HARI": los, "BIAYA_TAGIH": biaya, "BIAYA_PER_HARI": bph,
            "FKL07": fkl07, "FKL08": fkl08, "FKL31": fkl31,
            "FKL21": fkl21, "FKL22": fkl22,
        }

    # ═══════════════════════════════════════════════════════
    # Rule-Based Clinical Heuristic Scoring
    # ═══════════════════════════════════════════════════════
    def _rule_based_score(self, mapped: Dict[str, float]) -> Dict[str, Any]:
        """Deterministic fraud-risk scoring grounded in INA-CBG clinical norms.

        Produces a risk score 0.0–1.0 and a structured explanation listing
        which clinical rules fired and why.
        """
        penalties: List[Dict[str, Any]] = []
        severity = int(mapped["FKL08"]) if mapped["FKL08"] in (1, 2, 3) else 1

        los = mapped["LOS_HARI"]
        biaya = mapped["BIAYA_TAGIH"]
        bph = mapped["BIAYA_PER_HARI"]

        mean_bph = MEAN_COST_PER_DAY_BY_SEVERITY.get(severity, 3_500_000)
        mean_los = MEAN_LOS_BY_SEVERITY.get(severity, 5)

        # ── Rule 1: Biaya Per Hari vs Rata-rata INA-CBG ──
        if bph > 0:
            ratio_bph = bph / mean_bph
            if ratio_bph > 3.0:
                penalties.append({
                    "rule": "UPCODING_BIAYA",
                    "severity": "HIGH",
                    "weight": min(0.35, 0.10 * ratio_bph),
                    "detail": f"Biaya/hari Rp {bph:,.0f} = {ratio_bph:.1f}x rata-rata INA-CBG "
                              f"(Rp {mean_bph:,.0f}) untuk Severity-{severity}."
                })
            elif ratio_bph > 2.0:
                penalties.append({
                    "rule": "UPCODING_BIAYA",
                    "severity": "MEDIUM",
                    "weight": 0.15,
                    "detail": f"Biaya/hari Rp {bph:,.0f} = {ratio_bph:.1f}x rata-rata INA-CBG."
                })

        # ── Rule 2: LOS anomali (terlalu pendek untuk severity tinggi) ──
        if severity >= 2 and los <= 1:
            penalties.append({
                "rule": "PHANTOM_LOS_PENDEK",
                "severity": "HIGH",
                "weight": 0.25,
                "detail": f"LOS={los:.0f} hari sangat tidak wajar untuk Severity-{severity} "
                          f"(rata-rata {mean_los} hari). Indikasi Phantom Billing."
            })

        # ── Rule 3: LOS anomali (terlalu panjang) ──
        if los > mean_los * 3:
            penalties.append({
                "rule": "LOS_BERLEBIHAN",
                "severity": "MEDIUM",
                "weight": 0.20,
                "detail": f"LOS={los:.0f} hari melebihi 3x rata-rata ({mean_los} hari). "
                          f"Kemungkinan pemanjangan rawat inap untuk klaim tambahan."
            })

        # ── Rule 4: Biaya absolut sangat tinggi ──
        if bph > MAX_REASONABLE_COST_PER_DAY:
            penalties.append({
                "rule": "BIAYA_EKSTREM",
                "severity": "CRITICAL",
                "weight": 0.30,
                "detail": f"Biaya/hari Rp {bph:,.0f} melampaui batas wajar "
                          f"Rp {MAX_REASONABLE_COST_PER_DAY:,.0f}/hari."
            })

        # ── Rule 5: Severity tinggi tapi biaya rendah (under-billing → possible fraud scheme) ──
        if severity == 3 and biaya > 0 and bph < mean_bph * 0.3:
            penalties.append({
                "rule": "SEVERITY_MISMATCH",
                "severity": "MEDIUM",
                "weight": 0.15,
                "detail": f"Severity-3 (Berat) namun biaya/hari hanya Rp {bph:,.0f}, "
                          f"jauh di bawah rata-rata Rp {mean_bph:,.0f}. "
                          f"Kemungkinan upcoding severity untuk menaikkan tarif INA-CBG."
            })

        # ── Rule 6: Zero-cost claim (Phantom) ──
        if biaya <= 0 and los > 0:
            penalties.append({
                "rule": "PHANTOM_ZERO_COST",
                "severity": "HIGH",
                "weight": 0.30,
                "detail": f"Klaim dengan LOS={los:.0f} hari namun biaya Rp 0. "
                          f"Indikasi kuat Phantom Billing."
            })

        # Aggregate score
        total_weight = sum(p["weight"] for p in penalties)
        risk_score = min(total_weight, 0.99)  # cap at 0.99
        is_anomaly = risk_score > 0.30  # 30% threshold for rule-based

        # Build explanation
        feature_contributions = {}
        if penalties:
            detail_lines = []
            for p in sorted(penalties, key=lambda x: x["weight"], reverse=True):
                detail_lines.append(f"[{p['severity']}] {p['rule']}: {p['detail']}")
                feature_contributions[p["rule"]] = p["weight"]
            explanation = (
                f"Skor risiko heuristik: {risk_score*100:.1f}%. "
                + " | ".join(detail_lines)
            )
        else:
            explanation = (
                f"Skor risiko heuristik: {risk_score*100:.1f}%. "
                f"Distribusi biaya (Rp {bph:,.0f}/hari) dan LOS ({los:.0f} hari) "
                f"konsisten dengan standar INA-CBG Severity-{severity}. Tidak ada indikasi fraud."
            )

        return {
            "risk_score": risk_score,
            "is_anomaly": is_anomaly,
            "analyzed_features": self.feature_cols,
            "explanation": explanation,
            "feature_contributions": feature_contributions,
            "rules_fired": [p["rule"] for p in penalties],
            "scoring_method": "rule_based_heuristic",
        }

    # ═══════════════════════════════════════════════════════
    # Main Prediction Entry Point (Hybrid)
    # ═══════════════════════════════════════════════════════
    def predict_risk(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Hybrid prediction: uses XGBoost if calibrated, falls back to rule-based."""
        mapped = self.map_features(claim_data)

        # If XGBoost is degenerate or unavailable, use rule-based
        if self._xgb_is_degenerate or not self.xgb_available:
            result = self._rule_based_score(mapped)
            result["scoring_method"] = (
                "rule_based_heuristic (XGBoost degenerate — fallback aktif)"
                if self.xgb_available else
                "rule_based_heuristic (XGBoost tidak tersedia)"
            )
            return result

        # XGBoost path (healthy model)
        df_claim = pd.DataFrame([mapped])[self.feature_cols]
        prob = float(self.model.predict_proba(df_claim)[0][1])
        is_anomaly = bool(prob > 0.5)

        feature_contributions: Dict[str, float] = {}
        driver_summary = ""

        if self.explainer is not None:
            try:
                shap_values = self.explainer(df_claim).values[0]
                feature_contributions = dict(zip(self.feature_cols, [float(v) for v in shap_values]))
                sorted_drivers = sorted(
                    feature_contributions.items(), key=lambda x: abs(x[1]), reverse=True
                )
                top_drivers = [
                    f"{feat} ({'+' if val > 0 else ''}{val:.2f})"
                    for feat, val in sorted_drivers[:3]
                ]
                driver_summary = ", ".join(top_drivers)
            except Exception:
                pass

        if not driver_summary:
            driver_summary = (
                f"LOS={mapped['LOS_HARI']}, "
                f"BIAYA={mapped['BIAYA_TAGIH']:,.0f}, "
                f"FKL08={mapped['FKL08']}"
            )

        if is_anomaly:
            explanation = (
                f"Probabilitas anomali statistik {prob*100:.1f}% melebihi ambang batas 50%. "
                f"Fitur pendorong utama: {driver_summary}."
            )
        else:
            explanation = (
                f"Probabilitas risiko {prob*100:.1f}% dalam batas wajar (<50%). "
                f"Distribusi fitur konsisten dengan klaim normal ({driver_summary})."
            )

        return {
            "risk_score": float(prob),
            "is_anomaly": is_anomaly,
            "analyzed_features": self.feature_cols,
            "explanation": explanation,
            "feature_contributions": feature_contributions,
            "rules_fired": [],
            "scoring_method": "xgboost_shap",
        }

    def predict_fraud(self, claim_data: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Backward-compatible alias for legacy calls."""
        res = self.predict_risk(claim_data)
        return res["is_anomaly"], res["risk_score"], res["explanation"]


# Global Singleton Instance
try:
    ml_engine = MLEngine(DEFAULT_MODEL_PATH, DEFAULT_META_PATH)
except Exception as e:
    print(f"Warning: MLEngine singleton initialization deferred/failed: {e}")
    ml_engine = None
