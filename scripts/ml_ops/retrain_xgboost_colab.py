"""
═══════════════════════════════════════════════════════════════
GARDA-JKN | Re-Training XGBoost Model (Lapis 1) + Sekunder
Google Colab Notebook — Healthkathon BPJS 2026
═══════════════════════════════════════════════════════════════
Script ini melatih model XGBoost dengan menggabungkan 2 tabel:
1. Data FKRTL (202403_fkrtl.dta)
2. Data Diagnosis Sekunder (202405_diagnosissekunder.dta)

Strategi:
  - Join tabel berdasarkan `FKL02` (Nomor Kunjungan).
  - Menghitung fitur baru: `JML_DIAG_SEKUNDER` (Jumlah komplikasi).
  - Labeling heuristik: Deteksi "Upcoding" jika Severity 3 (Berat) 
    tapi tidak ada diagnosis sekunder yang menyertai!
═══════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import json
import warnings
warnings.filterwarnings('ignore')

print("✅ Libraries loaded!")

# ── Cell 2: Load Data ──────────────────────────────────────
PATH_FKRTL = '202403_fkrtl.dta'
PATH_SEKUNDER = '202405_diagnosissekunder.dta'

print("⏳ Memuat data FKRTL...")
df_fkrtl = pd.read_stata(PATH_FKRTL, convert_categoricals=False)

print("⏳ Memuat data Diagnosis Sekunder...")
df_sekunder = pd.read_stata(PATH_SEKUNDER, convert_categoricals=False)

# ── Cell 3: Feature Engineering & Table Join ───────────────
# Menghitung jumlah diagnosis sekunder per kunjungan (FKL02)
print("🔄 Menggabungkan data (Join)...")
sekunder_count = df_sekunder.groupby('FKL02').size().reset_index(name='JML_DIAG_SEKUNDER')

# Merge ke tabel utama
df_merged = pd.merge(df_fkrtl, sekunder_count, on='FKL02', how='left')
df_merged['JML_DIAG_SEKUNDER'] = df_merged['JML_DIAG_SEKUNDER'].fillna(0)

# Pembuatan fitur untuk model
df_feat = pd.DataFrame()
df_feat['LOS_HARI'] = pd.to_numeric(df_merged['FKL25'], errors='coerce').fillna(1).clip(lower=0)
df_feat['BIAYA_TAGIH'] = pd.to_numeric(df_merged['FKL47'], errors='coerce').fillna(0).clip(lower=0)
df_feat['BIAYA_PER_HARI'] = df_feat['BIAYA_TAGIH'] / df_feat['LOS_HARI'].replace(0, 1)
df_feat['FKL07'] = pd.to_numeric(df_merged['FKL07'], errors='coerce').fillna(2)
df_feat['FKL08'] = pd.to_numeric(df_merged['FKL08'], errors='coerce').fillna(1)
df_feat['FKL31'] = pd.to_numeric(df_merged['FKL31'], errors='coerce').fillna(1)
df_feat['FKL21'] = pd.to_numeric(df_merged['FKL21'], errors='coerce').fillna(6)
df_feat['FKL22'] = pd.to_numeric(df_merged['FKL22'], errors='coerce').fillna(44)
df_feat['JML_DIAG_SEKUNDER'] = df_merged['JML_DIAG_SEKUNDER']

print(f"\n📐 Data berhasil digabung! Dimensi akhir: {df_feat.shape}")

# ── Cell 4: Heuristic Labeling (Proxy Anomali Baru!) ──────
MEAN_BPH = df_feat.groupby('FKL08')['BIAYA_PER_HARI'].transform('median')
MEAN_LOS = df_feat.groupby('FKL08')['LOS_HARI'].transform('median')

# Rule 1: Biaya ekstrem
rule1 = (df_feat['BIAYA_PER_HARI'] > MEAN_BPH * 3)
# Rule 2: Phantom Billing
rule2 = (df_feat['LOS_HARI'] <= 0) & (df_feat['BIAYA_TAGIH'] > 0)
# Rule 3: LOS ekstrem
rule3 = (df_feat['LOS_HARI'] > MEAN_LOS * 3) & (df_feat['LOS_HARI'] > 10)
# Rule 4: UPCODING SEVERITY TANPA KOMPLIKASI (Klaim Berat tapi penyakit tambahan 0)
rule4 = (df_feat['FKL08'] == 3) & (df_feat['JML_DIAG_SEKUNDER'] == 0)

df_feat['is_anomaly'] = (rule1 | rule2 | rule3 | rule4).astype(int)

n_pos = df_feat['is_anomaly'].sum()
n_neg = (df_feat['is_anomaly'] == 0).sum()
print(f"\n🏷️  Label Distribusi (Dengan fitur baru):")
print(f"   Normal   : {n_neg:>10,} ({n_neg/len(df_feat)*100:.1f}%)")
print(f"   Anomali  : {n_pos:>10,} ({n_pos/len(df_feat)*100:.1f}%)")

# ── Cell 5: Train/Test Split ──────────────────────────────
FEATURE_COLS = ['LOS_HARI', 'BIAYA_TAGIH', 'BIAYA_PER_HARI',
                'FKL07', 'FKL08', 'FKL31', 'FKL21', 'FKL22', 'JML_DIAG_SEKUNDER']

X = df_feat[FEATURE_COLS]
y = df_feat['is_anomaly']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Cell 6: XGBoost Training ──────────────────────────────
spw = n_neg / max(n_pos, 1)

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    scale_pos_weight=spw,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='auc',
    random_state=42,
)

print("\n🚀 Memulai Training XGBoost...")
model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

# ── Cell 7: Evaluasi ──────────────────────────────────────
y_pred = model.predict(X_test)
print("\n" + "="*60)
print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomali']))
print(f"🎯 ROC-AUC: {roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]):.4f}")

# ── Cell 8: Export Model ──────────────────────────────────
model.save_model('garda_xgb_model_v2.json')
with open('garda_features_meta_v2.json', 'w') as f:
    json.dump({"feature_cols": FEATURE_COLS}, f, indent=2)

print("\n💾 Model & Metadata versi baru berhasil disimpan!")
