# 🛡️ GARDA-JKN (Generative Agent for Risk Detection and Adjudication)

![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![Model](https://img.shields.io/badge/AI-DeepSeek_R1_%7C_XGBoost-orange)
![Orchestration](https://img.shields.io/badge/Orchestration-LangGraph-purple)

**GARDA-JKN** adalah ekosistem AI adjudikasi klaim medis *end-to-end* berskala *enterprise* yang dirancang khusus untuk BPJS Kesehatan. Sistem ini beralih dari deteksi penipuan berbasis aturan tradisional (*rule-based heuristic*) menjadi mesin penalaran klinis yang dapat menjelaskan keputusannya secara transparan (*Explainable AI*) dan mengintegrasikan peran manusia dalam pengambilan keputusan (*Human-in-the-Loop*).

Sistem ini dilatih menggunakan **4 juta baris data empiris BPJS (FKRTL & Diagnosis Sekunder)** untuk memberantas fenomena *Upcoding*, *Phantom Billing*, dan *Clinical Incoherence*.

---

## 🏗️ Arsitektur Multi-Lapis (Microservice)

GARDA-JKN mengadopsi arsitektur yang sepenuhnya *decoupled* (Frontend Next.js dan Backend FastAPI) dengan AI tiga lapis yang berjalan secara konkuren:

1. **Lapis 1 (High-Speed Screening - XGBoost)** ⚡
   Mendeteksi anomali finansial (menggunakan *Stratified Isolation Forest* untuk menghindari bias faskes) dan menghasilkan **SHAP Auditor Reason Codes** untuk transparansi (*Explainable AI*).
2. **Lapis 2 (Medical Knowledge - Qdrant RAG)** 📚
   Membaca otomatis ratusan dokumen PNPK Kemenkes via PDF *Vector Search* untuk menemukan landasan diagnosis yang valid berdasarkan kode ICD-10.
3. **Lapis 3 (Clinical Arbiter - LLM LangGraph)** 🤖
   Agen AI yang bertugas sebagai Verifikator Medis. Ia menggabungkan hasil Lapis 1 & 2 untuk menghasilkan BAP medis (*Approved, Downgraded, Escalated*).

## ✨ Fitur Utama (UI/UX)

Sistem antarmuka (Frontend) dibuat semirip mungkin dengan **SIMRS VClaim BPJS**, ditambah fitur-fitur AI tingkat lanjut:
* **Human-in-the-Loop (HITL)**: Apabila AI tidak yakin (status `ESCALATED`), UI secara cerdas akan mengalihkan kendali kepada Verifikator Manusia untuk memberikan keputusan akhir (Setujui, Turunkan Severity, atau Tolak) beserta catatan klinis.
* **Audit Log SHAP**: Dasbor transparan untuk melihat jejak penalaran (Reason Codes) XGBoost.
* **Database RAG (PNPK) terintegrasi**: Manajemen dokumen PDF pedoman medis langsung dari *browser*.
* **Zero-Knowledge Privacy Masking**: Sesuai UU PDP No. 27/2022, semua data identitas (*PII*) disensor di Node 1 sebelum diproses oleh LLM.

---

## 🚀 Panduan Instalasi (Development)

Proyek ini dipisahkan menjadi dua bagian utama: **Backend FastAPI** dan **Frontend Next.js**. Keduanya harus dijalankan secara paralel.

### 1. Menyiapkan Backend (Python / FastAPI)
Backend mengelola ML Pipeline (XGBoost, LangGraph, Qdrant).
```bash
# Clone repository
git clone https://github.com/wmaulanaaishq/Garda-JKN.git
cd Garda-JKN

# Buat Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Untuk Windows: venv\Scripts\activate

# Install Dependensi
pip install -r requirements.txt

# Jalankan Peladen API
uvicorn api:app --host 0.0.0.0 --port 8000
```
Backend akan berjalan di `http://localhost:8000`.

### 2. Menyiapkan Frontend (Node.js / Next.js)
Frontend berisi antarmuka petugas rumah sakit (VClaim).
```bash
# Buka terminal baru dan masuk ke folder frontend
cd Garda-JKN/frontend

# Install dependensi Node.js
npm install

# Jalankan server Next.js mode development
npm run dev
```
Frontend akan berjalan di `http://localhost:3000`. 
Buka *browser* Anda dan arahkan ke alamat tersebut untuk menggunakan sistem.

---

## 📂 Struktur Repositori

```text
Garda-JKN/
├── api.py                  # Entrypoint peladen FastAPI
├── app/
│   ├── agents/             # Logic LangGraph (nodes, state, workflow, trace)
│   ├── core/               # Konfigurasi LLM, ML Engine (XGBoost), dan Qdrant DB
│   └── models/             # Schema Pydantic
├── frontend/               # Kode sumber Next.js (React, Tailwind CSS)
│   ├── src/app/page.tsx    # Halaman utama (VClaim UI + Dasbor AI)
│   └── package.json        # Dependensi Node.js
├── Data RAG/               # Repositori file PDF PNPK medis (Kemenkes)
├── artifacts/              # File binary ML (Model XGBoost, Scaler, Imputer)
├── evaluation/             # Pipeline pengujian LLM (DeepEval & Ragas)
└── requirements.txt        # Dependensi Python backend
```

---

## 🧪 Pengujian AI & CI/CD

GARDA-JKN mengimplementasikan **Standar Industri CI/CD** melalui GitHub Actions. 
Setiap kode yang didorong ke repositori ini akan secara otomatis melewati:
- **Unit Testing (PyTest)** untuk memvalidasi algoritma Lapis 1 (ML Engine).
- **Adversarial & Concurrency Testing** untuk memastikan keandalan *State Machine* LangGraph di bawah beban tinggi (5+ *requests* bersamaan).
- **AI Agent Evaluation (Ragas & DeepEval)** untuk menghitung tingkat *Faithfulness* dan *Answer Relevancy* (anti-halusinasi) dari LLM Arbiter.

*(Dikembangkan untuk memajukan ekosistem JKN Indonesia 🇮🇩)*
