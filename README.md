---
title: Garda JKN BPJS
emoji: ⚕️
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
---
# 🛡️ GARDA-JKN (Generative Agent for Risk Detection and Adjudication)

![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-Active-success)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![Model](https://img.shields.io/badge/AI-DeepSeek_R1_%7C_XGBoost-orange)

GARDA-JKN adalah ekosistem AI adjudikasi klaim medis *end-to-end* berskala *enterprise* yang dirancang khusus untuk BPJS Kesehatan. Sistem ini beralih dari deteksi penipuan berbasis aturan tradisional (*rule-based heuristic*) menjadi mesin penalaran klinis yang dapat menjelaskan keputusannya secara transparan (*Explainable AI*).

Sistem ini dilatih menggunakan **4 juta baris data empiris BPJS (FKRTL & Diagnosis Sekunder)** untuk memberantas fenomena *Upcoding*, *Phantom Billing*, dan *Clinical Incoherence*.

---

## 🏗️ Arsitektur Multi-Lapis (Microservice)

GARDA-JKN mengadopsi arsitektur tiga lapis yang berjalan secara konkuren:

1. **Lapis 1 (High-Speed Screening - XGBoost)** ⚡
   Mendeteksi anomali finansial (menggunakan *Stratified Isolation Forest* untuk menghindari bias faskes) dan menghasilkan **SHAP Auditor Reason Codes** untuk transparansi.
2. **Lapis 2 (Medical Knowledge - Qdrant RAG)** 📚
   Membaca otomatis ratusan dokumen PNPK Kemenkes via PDF *Vector Search* untuk menemukan landasan diagnosis yang valid berdasarkan kode ICD-10.
3. **Lapis 3 (Clinical Arbiter - LLM LangGraph)** 🤖
   Agen AI berotak *DeepSeek* yang bertugas sebagai Verifikator Medis. Ia menggabungkan hasil Lapis 1 & 2 untuk menghasilkan BAP (Berita Acara Pemeriksaan) medis (*Approved, Downgraded, Escalated*).

---

## 🚀 Panduan Instalasi (Development)

Sistem ini dipecah menjadi dua layanan: **FastAPI Backend** dan **Streamlit Frontend (SIMRS V-Claim Mockup)**.

### 1. Persiapan Environment
```bash
# Clone repository
git clone https://github.com/wmaulanaaishq/Garda-JKN.git
cd Garda-JKN

# Buat Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Install Dependensi
pip install -r requirements.txt
```

### 2. Menjalankan Microservice (Terminal 1)
Layanan backend AI akan berjalan di port `8000`.
```bash
source venv/bin/activate
python api.py
```

### 3. Menjalankan UI V-Claim (Terminal 2)
Layanan antarmuka petugas rumah sakit akan berjalan di port `8501`.
```bash
source venv/bin/activate
streamlit run app.py
```

---

## 🧪 Pengujian AI & CI/CD

GARDA-JKN mengimplementasikan **Standar Industri CI/CD** melalui GitHub Actions. 
Setiap kode yang didorong ke repositori ini akan secara otomatis melewati:
- **Linting (Flake8)** untuk memastikan kebersihan kode.
- **Unit Testing (PyTest)** untuk memvalidasi algoritma Lapis 1 (ML Engine).
- **AI Agent Evaluation (Ragas & DeepEval)** untuk menghitung tingkat *Faithfulness* dan *Answer Relevancy* (anti-halusinasi) dari LLM Arbiter.

*(Dikembangkan untuk memajukan ekosistem JKN Indonesia 🇮🇩)*
