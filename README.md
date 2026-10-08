# GARDA-JKN (Generative Agent for Risk Detection and Adjudication)

![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![Model](https://img.shields.io/badge/AI-DeepSeek_R1_%7C_XGBoost-orange)
![Orchestration](https://img.shields.io/badge/Orchestration-LangGraph-purple)
![Security](https://img.shields.io/badge/Security-Prompt_Injection_Guard-red)

**GARDA-JKN** adalah ekosistem AI adjudikasi klaim medis *end-to-end* berskala *enterprise* yang dirancang khusus untuk memberikan solusi mutakhir pada kompetisi **Healthkathon BPJS Kesehatan 2026**.

Sistem ini beralih dari deteksi penipuan berbasis aturan tradisional (*rule-based heuristic*) menjadi mesin penalaran klinis berlapis yang dapat menjelaskan keputusannya secara transparan (*Explainable AI*), mengamankan data medis (*Zero-Knowledge Masking*), dan mengintegrasikan peran manusia dalam pengambilan keputusan (*Human-in-the-Loop*).

Sistem ini dilatih menggunakan **4 juta baris data empiris BPJS (FKRTL & Diagnosis Sekunder)** untuk memberantas fenomena *Upcoding* (manipulasi tingkat keparahan), *Phantom Billing* (klaim fiktif), dan *Clinical Incoherence*.

---

## 🏗️ Arsitektur Multi-Lapis (Microservice & LangGraph)

GARDA-JKN mengadopsi arsitektur yang sepenuhnya terpisah (*decoupled*) antara Frontend Next.js dan Backend FastAPI, yang diorkestrasi oleh **LangGraph State Machine**. Alur kerja klaim melewati 4 lapisan perlindungan mutakhir:

1. **Lapis Keamanan (Intake & Security Guardrail)** 🔒
   Sistem menyamarkan identitas privasi (PII) sesuai **UU PDP No. 27/2022** (*Zero-Knowledge Masking*) dan melakukan pemindaian Regex ketat untuk memblokir serangan siber *Prompt Injection* (seperti bypass instruksi AI).
2. **Lapis 1 (High-Speed Screening - XGBoost)** ⚡
   Mendeteksi anomali finansial secara instan menggunakan *Stratified Isolation Forest* (menghindari bias antara RS Kelas A hingga D) dan menghasilkan skor probabilitas beserta **SHAP Auditor Reason Codes**.
3. **Lapis 2 (Medical Knowledge - Qdrant RAG)** 📚
   Membaca ratusan halaman dokumen PNPK Kemenkes via *Vector Search* untuk menemukan landasan klinis. Didukung oleh `PyMuPDF4LLM` agar format tabel dosis dan aturan medis tetap presisi.
4. **Lapis 3 (Clinical Arbiter - LLM)** 🤖
   Agen AI (DeepSeek via AIML API) bertindak sebagai Verifikator Medis. Ia menggabungkan hasil Lapis 1 & 2 untuk menerbitkan Berita Acara Medis (*Approved, Downgraded, Escalated*).

---

## ✨ Fitur Utama (UI/UX Dasbor Verifikator)

Antarmuka (Frontend) dibuat semirip mungkin dengan **SIMRS VClaim BPJS**, ditambah metrik AI:
* **Human-in-the-Loop (HITL)**: Apabila klaim meragukan (status `ESCALATED`), AI menyerahkan kendali kepada Verifikator Manusia untuk memberikan putusan manual terakhir. Mesin tidak pernah bertindak diktator.
* **Audit Log SHAP**: Dasbor transparan menampilkan kontribusi setiap variabel (misal: "Lama Rawat" atau "Biaya Tagih") yang membuat klaim dicurigai.
* **Streaming Responses**: Menggunakan Server-Sent Events (SSE) agar hasil adjudikasi tampil seketika (*real-time*).

---

## 🚀 Panduan Instalasi (Development)

Sistem ini dipisah menjadi Backend (FastAPI) dan Frontend (Next.js). Keduanya harus berjalan paralel.

### 1. Menyiapkan Backend (Python / FastAPI)
Backend mengelola ML Pipeline, LangGraph, dan Vector DB.
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
Frontend memuat antarmuka petugas VClaim.
```bash
# Buka terminal baru dan masuk ke folder frontend
cd Garda-JKN/frontend

# Install dependensi Node.js
npm install

# Jalankan server Next.js
npm run dev
```
Frontend akan terbuka di `http://localhost:3000`. 

---

## 📂 Struktur Repositori

```text
Garda-JKN/
├── api.py                  # Entrypoint peladen FastAPI (Mendukung SSE)
├── app/
│   ├── agents/             # Node LangGraph (Security, ML, RAG, Arbiter)
│   ├── core/               # Integrasi LLM, XGBoost, dan Qdrant DB
│   └── models/             # Schema Pydantic
├── frontend/               # Kode sumber Next.js (React, Tailwind CSS)
├── Data RAG/               # Kumpulan PDF Medis PNPK dari Kemenkes RI
├── artifacts/              # File binary ML statis (Model XGBoost & Config)
├── docs/                   # 📑 DOKUMENTASI LENGKAP & PROPOSAL
├── evaluation/             # Pipeline pengujian RAG Triad (DeepEval)
├── scripts/                # Utility untuk ML Ops & Generate Docs
└── tests/                  # Skrip PyTest
```
> **Lihat detail arsitektur dan bisnis plan lengkap di direktori [`docs/`](docs/)**

---

## 🧪 Pengujian AI & CI/CD (LLMOps)

GARDA-JKN menjunjung tinggi reliabilitas. Setiap eksekusi dapat diuji menggunakan kumpulan *script* di folder `tests/` yang mencakup:
- **Unit Testing (PyTest)** untuk memvalidasi algoritma Lapis 1.
- **Security Testing** untuk memvalidasi bahwa *Guardrail* sukses menangkis *Prompt Injection*.
- **AI Agent Evaluation (DeepEval)** untuk menghitung tingkat *Faithfulness* dan *Answer Relevancy* (anti-halusinasi) dari teks BAP medis yang dihasilkan AI.

*(Inovasi ini dikembangkan untuk menjaga amanah dan memajukan ekosistem JKN Indonesia 🇮🇩)*
