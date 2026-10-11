# Workflow Sistem GARDA-JKN (LangGraph StateGraph)

Diagram ini mengilustrasikan alur kerja penanganan klaim BPJS Kesehatan secara *deterministik* dan aman, yang diorkestrasi menggunakan **LangGraph StateGraph**.

---

## 📊 Diagram Mermaid (Kompatibel dengan Draw.io & GitHub)

Salin kode Mermaid di bawah ini langsung ke:
- **GitHub / Markdown Viewer**: Otomatis ter-render sebagai diagram visual.
- **Draw.io**: Buka [app.diagrams.net](https://app.diagrams.net), lalu pilih menu **Arrange** > **Insert** > **Advanced** > **Mermaid**, tempel kode ini, dan klik **Insert**.

```mermaid
flowchart TD
    %% Styling Definisi
    classDef startNode fill:#1E293B,stroke:#0F172A,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef securityNode fill:#EF4444,stroke:#B91C1C,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef mlNode fill:#3B82F6,stroke:#1D4ED8,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef decisionNode fill:#F59E0B,stroke:#D97706,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef ragNode fill:#8B5CF6,stroke:#6D28D9,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef llmNode fill:#06B6D4,stroke:#0891B2,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef hitlNode fill:#EC4899,stroke:#BE185D,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef endApproved fill:#10B981,stroke:#047857,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef endReject fill:#64748B,stroke:#475569,stroke-width:2px,color:#FFFFFF,font-weight:bold;

    %% Subgraphs & Nodes
    subgraph S1 ["Fase 1: Ingestion & Keamanan Data (Zero-Knowledge)"]
        A(["Klaim Rumah Sakit Masuk (JSON Payload)"]):::startNode
        B["Intake & Security Node<br/>- Zero-Knowledge Privacy Masking (Sensor NIK & Nama)<br/>- Pemindaian Prompt Injection / Jailbreak"]:::securityNode
        C{"Pemeriksaan Keamanan Valid?"}:::decisionNode
    end

    subgraph S2 ["Fase 2: Skrining Cepat & Pembagian Beban (Lapis 1)"]
        D["Risk Scoring Node (Lapis 1 ML Engine)<br/>- XGBoost + Stratified Isolation Forest<br/>- Deteksi Anomali Finansial & SHAP Values"]:::mlNode
        E{"Conditional Handoff:<br/>Apakah Klaim Anomali?"}:::decisionNode
    end

    subgraph S3 ["Fase 3: Penalaran Medis & Regulasi (Lapis 2 & 3)"]
        F["Medical Knowledge RAG (Lapis 2)<br/>- Qdrant Vector Search<br/>- Pencocokan Pasal PNPK Kemenkes & Juknis INA-CBG"]:::ragNode
        G["Validator Agent (Pengecek Klinis)<br/>- Uji Kesesuaian Lab, Prosedur & Komorbiditas"]:::ragNode
        H["Arbiter Node (Lapis 3: LLM DeepSeek-Chat)<br/>- Sintesis Bukti Klinis & Legalitas<br/>- Perumusan Draf Rekomendasi & Confidence Score"]:::llmNode
    end

    subgraph S4 ["Fase 4: Putusan & Human-in-the-Loop (HITL)"]
        I{"Status Hasil Evaluasi"}:::decisionNode
        J(["Auto-Approved:<br/>Klaim Bersih Wajar, Pembayaran Otomatis Diteruskan"]):::endApproved
        K(["Final Status: APPROVED / DOWNGRADED<br/>Berita Acara Putusan Otomatis Diterbitkan"]):::endApproved
        L["Human-in-the-Loop (HITL):<br/>Dorong Draf BAP ke Dasbor VClaim Mockup UI"]:::hitlNode
        M(["Dokter Verifikator BPJS<br/>Mengetuk Palu Keputusan Hukum Terakhir"]):::hitlNode
        N(["Security Alert: DITOLAK / ESCALATED<br/>Indikasi Ancaman Keamanan Siber"]):::endReject
    end

    %% Hubungan Alur (Edges)
    A --> B
    B --> C
    C -- "Terdeteksi Ancaman / Jailbreak" --> N
    C -- "Aman & Lolos Sensor PII" --> D
    D --> E
    E -- "Inlier (Skor Wajar / Bersih)" --> J
    E -- "Outlier (Mencurigakan / Anomali)" --> F
    F --> G
    G --> H
    H --> I
    I -- "Rekomendasi Jelas (Approve / Downgrade)" --> K
    I -- "Status Ambigu / Kompleks (ESCALATED)" --> L
    L --> M
```

---

## 🔍 Penjelasan Tiap Komponen Alur

1. **Intake & Security Node (Fase 1)**
   - **Zero-Knowledge Privacy Masking**: Sebelum data menyentuh mesin ML atau Cloud LLM, data identitas pribadi (PII) seperti NIK dan Nama Pasien disamarkan sesuai amanat UU PDP No. 27/2022.
   - **Prompt Injection Defense**: Memeriksa kolom `catatan_klinis` dan diagnosis dari teks eksploitatif (seperti *"ignore previous instructions"*). Jika ada serangan, proses langsung dihentikan demi integritas sistem.

2. **Risk Scoring Node (Lapis 1 - XGBoost)**
   - Melakukan evaluasi statistik berkecepatan tinggi (<100ms) menggunakan model ensemble *Stratified Isolation Forest* dan *XGBoost*.
   - Menghasilkan probabilitas anomali finansial dan alasan *SHAP* (misal: rasio biaya harian berlebih, durasi rawat janggal).

3. **Conditional Handoff (Percabangan Cerdas)**
   - **Inlier (Klaim Wajar)**: 70-80% klaim rutin langsung dialihkan ke **Auto-Approve**, menghemat biaya token API dan memangkas antrean faskes.
   - **Outlier (Klaim Mencurigakan)**: Diteruskan ke pipeline penalaran medis mendalam (RAG & LLM).

4. **Medical Knowledge RAG & Validator Agent (Lapis 2)**
   - **Qdrant Vector DB**: Menarik dokumen Pedoman Nasional Pelayanan Kedokteran (PNPK) resmi Kemenkes RI yang relevan dengan diagnosis dan tindakan pasien.
   - **Validator Agent**: Memvalidasi kesesuaian klinis (misalnya kriteria AKI KDIGO pada stroke, atau batas LOS pada STEMI).

5. **Arbiter Node (Lapis 3 - LLM DeepSeek-Chat)**
   - Mengintegrasikan temuan Lapis 1 dan Lapis 2 untuk menyusun pertimbangan medis formal secara terstruktur.
   - Mengeluarkan rekomendasi status:
     - `APPROVED`: Terbukti memenuhi indikasi medis.
     - `DOWNGRADED`: Ditemukan indikasi upcoding tingkat severity (misal Severity III diturunkan ke Severity II karena komorbiditas tidak terbukti).
     - `ESCALATED`: Temuan anomali kompleks atau bukti tidak lengkap.

6. **Human-in-the-Loop (HITL) pada Dasbor VClaim**
   - Klaim ambigu (`ESCALATED`) tidak ditolak sepihak oleh AI. 
   - Draf Berita Acara Pemeriksaan (BAP) beserta ringkasan bukti klinis disajikan di antarmuka Next.js VClaim.
   - **Dokter Verifikator Manusia** tetap memegang kendali penuh sebagai pemutus hukum (*final adjudicator*).

---

## 💡 Cara Import ke Draw.io

1. Buka [Draw.io / diagrams.net](https://app.diagrams.net).
2. Klik menu **Arrange** di bar navigasi atas.
3. Pilih **Insert** > **Advanced** > **Mermaid**.
4. Salin seluruh blok kode Mermaid di atas (mulai dari `flowchart TD` sampai baris terakhir).
5. Klik tombol **Insert**.
6. Diagram akan langsung dikonversi menjadi elemen kotak, garis, dan ikon yang dapat digeser, diwarnai, atau diekspor ke PNG/PDF/SVG untuk kebutuhan proposal dan slide presentasi Healthkathon.
