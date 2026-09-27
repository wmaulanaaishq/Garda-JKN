"""
═══════════════════════════════════════════════════════════════
GARDA-JKN | Re-Training XGBoost Model (Lapis 1)
Google Colab Notebook — Healthkathon BPJS 2026
═══════════════════════════════════════════════════════════════
Jalankan notebook ini di Google Colab untuk melatih ulang model
XGBoost menggunakan data BPJS Sampel Reguler Edisi 2025 (FKRTL).

Strategi:
  1. Feature Engineering dari kolom FKRTL asli
  2. Labeling heuristik (proxy) untuk deteksi anomali
  3. Class Balancing dengan scale_pos_weight
  4. Ekspor model (.json) + metadata siap pakai di WSL
═══════════════════════════════════════════════════════════════
"""

# ── Cell 1: Install & Imports ──────────────────────────────
# !pip install xgboost shap pandas scikit-learn

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import json
import warnings
warnings.filterwarnings('ignore')

print("✅ Libraries loaded!")

# ── Cell 2: Upload & Load Data ─────────────────────────────
# Di Colab, upload file .dta dari folder:
#   /mnt/e/Data Bpjs Kesehatan rilis 2025/2025/Data Sampel Reguler Edisi 2025/data/
#
# Atau mount Google Drive:
# from google.colab import drive
# drive.mount('/content/drive')
# DATA_PATH = '/content/drive/MyDrive/202403_fkrtl.dta'

# Jika file sudah di-upload langsung:
DATA_PATH = '202403_fkrtl.dta'  # <-- Sesuaikan path

df = pd.read_stata(DATA_PATH, convert_categoricals=False)
print(f"📊 Data dimuat: {df.shape[0]:,} baris × {df.shape[1]} kolom")
print(f"📋 Kolom: {list(df.columns)}")

# ── Cell 3: Feature Engineering ────────────────────────────
# Kolom target yang kita butuhkan:
#   FKL07  = Tingkat pelayanan (RJTL/RITL)
#   FKL08  = Severity level (1/2/3)
#   FKL21  = Kelompok diagnosis
#   FKL22  = Sub-kelompok diagnosis
#   FKL31  = Jenis kepesertaan
#   FKL25  = LOS (Length of Stay)
#   FKL32  = Total biaya tagih (atau FKL47/FKL48)

# Mapping kolom BPJS → fitur model
df_feat = pd.DataFrame()
df_feat['LOS_HARI'] = pd.to_numeric(df['FKL25'], errors='coerce').fillna(1).clip(lower=0)
df_feat['BIAYA_TAGIH'] = pd.to_numeric(df['FKL47'], errors='coerce').fillna(0).clip(lower=0)
df_feat['BIAYA_PER_HARI'] = df_feat['BIAYA_TAGIH'] / df_feat['LOS_HARI'].replace(0, 1)
df_feat['FKL07'] = pd.to_numeric(df['FKL07'], errors='coerce').fillna(2)
df_feat['FKL08'] = pd.to_numeric(df['FKL08'], errors='coerce').fillna(1)
df_feat['FKL31'] = pd.to_numeric(df['FKL31'], errors='coerce').fillna(1)
df_feat['FKL21'] = pd.to_numeric(df['FKL21'], errors='coerce').fillna(6)
df_feat['FKL22'] = pd.to_numeric(df['FKL22'], errors='coerce').fillna(44)

print(f"\n📐 Feature DataFrame: {df_feat.shape}")
print(df_feat.describe().round(2))

# ── Cell 4: Heuristic Labeling (Proxy untuk Anomali) ──────
# Karena data BPJS tidak memiliki label fraud/non-fraud,
# kita membuat PROXY LABEL berdasarkan aturan klinis INA-CBG.
#
# Klaim dicurigai anomali jika memenuhi ≥1 kondisi:
#   1. Biaya/hari > 3x median biaya/hari per severity level
#   2. LOS = 0 tapi ada biaya > 0 (Phantom)
#   3. LOS > 3x median LOS per severity level
#   4. Severity-3 tapi biaya/hari < 30% median severity-3

MEAN_BPH = df_feat.groupby('FKL08')['BIAYA_PER_HARI'].transform('median')
MEAN_LOS = df_feat.groupby('FKL08')['LOS_HARI'].transform('median')

rule1 = (df_feat['BIAYA_PER_HARI'] > MEAN_BPH * 3)
rule2 = (df_feat['LOS_HARI'] <= 0) & (df_feat['BIAYA_TAGIH'] > 0)
rule3 = (df_feat['LOS_HARI'] > MEAN_LOS * 3) & (df_feat['LOS_HARI'] > 10)
rule4 = (df_feat['FKL08'] == 3) & (df_feat['BIAYA_PER_HARI'] < MEAN_BPH * 0.3) & (df_feat['BIAYA_TAGIH'] > 0)

df_feat['is_anomaly'] = (rule1 | rule2 | rule3 | rule4).astype(int)

n_pos = df_feat['is_anomaly'].sum()
n_neg = (df_feat['is_anomaly'] == 0).sum()
print(f"\n🏷️  Label Distribution:")
print(f"   Normal   : {n_neg:>10,} ({n_neg/len(df_feat)*100:.1f}%)")
print(f"   Anomali  : {n_pos:>10,} ({n_pos/len(df_feat)*100:.1f}%)")
print(f"   Ratio    : 1:{n_neg/max(n_pos,1):.1f}")

# ── Cell 5: Train/Test Split ──────────────────────────────
FEATURE_COLS = ['LOS_HARI', 'BIAYA_TAGIH', 'BIAYA_PER_HARI',
                'FKL07', 'FKL08', 'FKL31', 'FKL21', 'FKL22']

X = df_feat[FEATURE_COLS]
y = df_feat['is_anomaly']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\n📦 Train: {len(X_train):,} | Test: {len(X_test):,}")

# ── Cell 6: XGBoost Training (with Class Balancing) ───────
# scale_pos_weight = jumlah_normal / jumlah_anomali
# Ini memberitahu XGBoost agar memberikan bobot lebih pada
# kelas minoritas (anomali) sehingga model tidak bias.

spw = n_neg / max(n_pos, 1)

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    scale_pos_weight=spw,      # ← KUNCI PERBAIKAN!
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='auc',
    random_state=42,
    use_label_encoder=False,
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=20
)

# ── Cell 7: Evaluasi Model ────────────────────────────────
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print("\n" + "="*60)
print("📊 CLASSIFICATION REPORT")
print("="*60)
print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomali']))

auc = roc_auc_score(y_test, y_proba)
print(f"🎯 ROC-AUC Score: {auc:.4f}")

cm = confusion_matrix(y_test, y_pred)
print(f"\n📈 Confusion Matrix:")
print(f"   TN={cm[0][0]:,}  FP={cm[0][1]:,}")
print(f"   FN={cm[1][0]:,}  TP={cm[1][1]:,}")

# ── Cell 8: Sanity Check — Variasi Prediksi ───────────────
test_cases = pd.DataFrame([
    {"LOS_HARI": 5, "BIAYA_TAGIH": 8_000_000, "BIAYA_PER_HARI": 1_600_000,
     "FKL07": 2, "FKL08": 2, "FKL31": 1, "FKL21": 6, "FKL22": 44},
    {"LOS_HARI": 1, "BIAYA_TAGIH": 50_000_000, "BIAYA_PER_HARI": 50_000_000,
     "FKL07": 2, "FKL08": 3, "FKL31": 1, "FKL21": 2, "FKL22": 11},
    {"LOS_HARI": 30, "BIAYA_TAGIH": 2_000_000, "BIAYA_PER_HARI": 66_666,
     "FKL07": 4, "FKL08": 1, "FKL31": 2, "FKL21": 2, "FKL22": 16},
])

probas = model.predict_proba(test_cases[FEATURE_COLS])[:, 1]
print("\n🧪 Sanity Check Prediksi:")
labels = ["Normal (LOS=5, 8jt)", "Upcoding (LOS=1, 50jt)", "Phantom (LOS=30, 2jt)"]
for label, p in zip(labels, probas):
    status = "🚨 ANOMALI" if p > 0.5 else "✅ NORMAL"
    print(f"   {label}: {p:.4f} → {status}")

spread = probas.max() - probas.min()
print(f"\n   Spread prediksi: {spread:.4f} {'✅ MODEL SEHAT!' if spread > 0.05 else '❌ MASIH DEGENERATE'}")

# ── Cell 9: Export Model ──────────────────────────────────
MODEL_OUT = 'garda_xgb_model.json'
META_OUT = 'garda_features_meta.json'

model.save_model(MODEL_OUT)
with open(META_OUT, 'w') as f:
    json.dump({"feature_cols": FEATURE_COLS}, f, indent=2)

print(f"\n💾 Model disimpan: {MODEL_OUT}")
print(f"💾 Metadata disimpan: {META_OUT}")
print("\n🎯 SELESAI! Download kedua file ini dan taruh di folder:")
print("   /home/wmaulanaaishq/projects/bpjs_2025/artifacts/")
