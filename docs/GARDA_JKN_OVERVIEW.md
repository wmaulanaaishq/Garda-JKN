# GARDA-JKN: Generative Agent for Risk Detection and Adjudication

GARDA-JKN adalah sebuah sistem kecerdasan buatan terpadu (End-to-End AI System) yang dirancang khusus untuk mendeteksi, mengevaluasi, dan memberikan keputusan adjudikasi terhadap potensi kecurangan (*fraud*) klaim jaminan kesehatan. Proyek ini dikembangkan secara spesifik untuk berkompetisi dan memberikan solusi pada ajang **Healthkathon BPJS Kesehatan 2026**.

---

## 🎯 Latar Belakang & Tujuan (Purpose)

Setiap bulannya, BPJS Kesehatan menerima jutaan klaim dari Fasilitas Kesehatan Rujukan Tingkat Lanjut (FKRTL). Proses verifikasi manual yang dilakukan oleh dokter verifikator sangat rentan terhadap inefisiensi, human error, dan kelelahan, yang pada akhirnya menyebabkan kebocoran dana JKN akibat klaim fiktif atau manipulasi data.

**GARDA-JKN dikembangkan untuk:**
1. **Mencegah Fraud Medis:** Menggagalkan praktik *Upcoding* (manipulasi tingkat keparahan/severity level) dan *Phantom Billing* (klaim tindakan yang tidak pernah dilakukan).
2. **Efisiensi Waktu Verifikasi:** Mengotomatisasi pengecekan klaim dari hitungan menit (manual) menjadi kurang dari 10 detik per klaim.
3. **Meningkatkan Akurasi Klinis:** Membantu dokter verifikator mengambil keputusan berdasarkan landasan hukum dan medis yang kuat secara *real-time*.

---

## 🛠️ Arsitektur & Tech Stack

Sistem ini tidak hanya mengandalkan satu model AI, melainkan arsitektur berlapis (Multi-Layered AI) yang dipisahkan ke dalam beberapa *microservices* modern.

### 1. Frontend (Antarmuka Pengguna)
- **Framework:** Next.js & React
- **Fungsi:** Dashboard interaktif (VClaim Mockup UI) bagi verifikator medis untuk memasukkan data klaim, melihat skor anomali, dan menyetujui/menolak klaim (Human-in-the-Loop).

### 2. Backend & Orkestrasi
- **Web Framework:** FastAPI (Python) dengan dukungan *Asynchronous REST API* dan *Server-Sent Events* (SSE).
- **AI Orchestrator:** **LangGraph** (StateGraph) digunakan untuk mengatur alur kerja Multi-Agen (Intake -> Security -> ML Scoring -> RAG -> Arbiter).

### 3. Mesin Deteksi & Penalaran (Lapis 1 & 2)
- **Machine Learning (Lapis 1):** **XGBoost** dipadukan dengan **Stratified Isolation Forest**. Berfungsi untuk menghitung probabilitas anomali statistik dari biaya tagihan dan lama rawat inap.
- **Explainable AI (XAI):** **SHAP** (SHapley Additive exPlanations) untuk memberikan transparansi fitur mana yang paling mencurigakan.
- **Large Language Model (Lapis 2):** **DeepSeek-Chat** via AIML API yang bertindak sebagai *Clinical Arbiter* (Hakim Medis) untuk merangkum dan memutuskan status klinis pasien.

### 4. Manajemen Data (RAG & LLMOps)
- **Vector Database:** **Qdrant DB** (berjalan secara lokal via SQLite) untuk menyimpan jutaan vektor semantik secara cepat tanpa perlu infrastruktur eksternal yang berat.
- **PDF Parser:** **PyMuPDF4LLM** digunakan agar tabel bersarang (*nested tables*) di dalam PDF medis tidak hancur saat diubah menjadi teks (Markdown).
- **LLMOps Evaluation:** **DeepEval Framework** untuk menguji sistem secara ketat pada metrik *Faithfulness* (Ketiadaan Halusinasi) dan *Answer Relevancy*.

---

## 📂 Sumber Data (Data Sources)

Agar AI dapat memberikan keputusan medis yang sah dan akurat, GARDA-JKN dilatih dan dibekali dengan data yang berasal dari sumber resmi pemerintahan:

1. **Data Pelatihan ML (Machine Learning):**
   - Data Sampel BPJS Kesehatan (Data historis kunjungan FKRTL, diagnosis sekunder, tarif INA-CBG, dan durasi rawat inap/LOS).
2. **Data Basis Pengetahuan (Knowledge Base RAG):**
   - Dokumen **Pedoman Nasional Pelayanan Kedokteran (PNPK)** resmi yang diterbitkan oleh **Kementerian Kesehatan Republik Indonesia**. (Misal: PNPK Tata Laksana Stroke, PNPK Diabetes, PNPK Leukemia).
   - Dokumen Petunjuk Teknis Verifikasi Klaim INA-CBG.

---

## 🛡️ Keamanan & Kepatuhan Etika (Security & Compliance)

GARDA-JKN dibangun dengan standar *Enterprise Grade* untuk institusi kesehatan:
- **Zero-Knowledge Privacy Masking:** Agen secara otomatis mendeteksi dan menyensor Informasi Pribadi (PII) seperti Nama Pasien dan NIK sebelum data tersebut terkirim ke server Cloud LLM (Sesuai UU PDP).
- **Prompt Injection Guardrail:** Lapisan keamanan (Node 1.5) yang secara reguler menscan teks dari rekam medis untuk mendeteksi anomali teks manipulatif (contoh: *"Abaikan instruksi sebelumnya"*). Jika terdeteksi, klaim otomatis dihentikan.
- **High-Reliability Fallback:** Jika API LLM mati atau *timeout*, sistem akan mengambil alih secara programatik (*Regex Parsing*) agar *server* tidak mengalami *crash*.
