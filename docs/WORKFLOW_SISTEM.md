# Workflow Sistem GARDA-JKN (LangGraph StateGraph) - Tema Putih (Word Document & Clean Light Mode)

Diagram ini mengilustrasikan alur kerja penanganan klaim BPJS Kesehatan secara *deterministik* dan aman, yang diorkestrasi menggunakan **LangGraph StateGraph**.

> **Khusus Dokumen & Proposal:** Palet warna diagram ini telah dioptimalkan khusus untuk **latar belakang putih (White Background)** agar tampak bersih, elegan, profesional, dan menyatu sempurna saat dimasukkan ke dalam Microsoft Word atau dokumen cetak resmi.

---

## 📊 Diagram Mermaid (Versi Light Theme / White Background)

Salin kode Mermaid di bawah ini langsung ke:
- **GitHub / Markdown Viewer**: Otomatis ter-render sebagai diagram bersih dengan aksen warna korporat.
- **Draw.io**: Buka [app.diagrams.net](https://app.diagrams.net), lalu pilih menu **Arrange** > **Insert** > **Advanced** > **Mermaid**, tempel kode ini, dan klik **Insert**.

```mermaid
flowchart TD
    %% Styling Khusus Latar Belakang Putih (Light Theme / Word Document)
    classDef startNode fill:#EFF6FF,stroke:#2563EB,stroke-width:2px,color:#1E3A8A,font-weight:bold;
    classDef securityNode fill:#FEF2F2,stroke:#DC2626,stroke-width:2px,color:#991B1B,font-weight:bold;
    classDef mlNode fill:#EEF2FF,stroke:#4F46E5,stroke-width:2px,color:#312E81,font-weight:bold;
    classDef decisionNode fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#92400E,font-weight:bold;
    classDef ragNode fill:#F5F3FF,stroke:#7C3AED,stroke-width:2px,color:#5B21B6,font-weight:bold;
    classDef llmNode fill:#F0FDFA,stroke:#0D9488,stroke-width:2px,color:#115E59,font-weight:bold;
    classDef hitlNode fill:#FDF2F8,stroke:#DB2777,stroke-width:2px,color:#9D174D,font-weight:bold;
    classDef endApproved fill:#F0FDF4,stroke:#16A34A,stroke-width:2px,color:#166534,font-weight:bold;
    classDef endReject fill:#FEF2F2,stroke:#B91C1C,stroke-width:2px,color:#7F1D1D,font-weight:bold;

    %% Subgraphs & Nodes
    subgraph S1 ["Fase 1: Ingestion & Keamanan Data (Zero-Knowledge)"]
        A(["Klaim Rumah Sakit Masuk (JSON Payload)"]):::startNode
        B["Intake & Security Node<br/>• Zero-Knowledge Privacy Masking (Sensor NIK & Nama)<br/>• Pemindaian Prompt Injection & Jailbreak"]:::securityNode
        C{"Pemeriksaan Keamanan Valid?"}:::decisionNode
    end

    subgraph S2 ["Fase 2: Skrining Cepat & Pembagian Beban (Lapis 1)"]
        D["Risk Scoring Node (Lapis 1 ML Engine)<br/>• XGBoost + Stratified Isolation Forest<br/>• Deteksi Anomali Finansial & SHAP Values"]:::mlNode
        E{"Conditional Handoff:<br/>Apakah Klaim Anomali?"}:::decisionNode
    end

    subgraph S3 ["Fase 3: Penalaran Medis & Regulasi (Lapis 2 & 3)"]
        F["Medical Knowledge RAG (Lapis 2)<br/>• Qdrant Vector Search<br/>• Pencocokan Pasal PNPK Kemenkes & Juknis INA-CBG"]:::ragNode
        G["Validator Agent (Pengecek Klinis)<br/>• Uji Kesesuaian Lab, Prosedur & Komorbiditas"]:::ragNode
        H["Arbiter Node (Lapis 3: LLM DeepSeek-Chat)<br/>• Sintesis Bukti Klinis & Legalitas<br/>• Perumusan Draf Rekomendasi & Confidence Score"]:::llmNode
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

    %% Subgraph Styling Khusus White Theme
    style S1 fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A
    style S2 fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A
    style S3 fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A
    style S4 fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A
```

---

## 🖼️ File Gambar Siap Pakai untuk Microsoft Word

Kami juga telah merender diagram beresolusi tinggi (Retina quality 2x) dengan latar belakang putih murni yang siap disisipkan ke dokumen Word:
- Lokasi file: `docs/evidence/plot_workflow_system.png`
- File ini juga **sudah otomatis disematkan ke dalam proposal resmi Word** Anda di:
  `docs/Proposal_Healthkathon_2026_GARDA_JKN.docx` (Bagian 3).

---

## 🎨 Palet Warna Ramah Latar Belakang Putih

| Komponen | Warna Latar (Fill) | Warna Garis (Stroke) | Warna Teks | Keterangan |
| :--- | :--- | :--- | :--- | :--- |
| **Start / Input** | `#EFF6FF` (Ice Blue) | `#2563EB` (Royal Blue) | `#1E3A8A` (Deep Blue) | Kontras tinggi, bersih |
| **Security Node** | `#FEF2F2` (Soft Red) | `#DC2626` (Red) | `#991B1B` (Deep Red) | Peringatan keamanan |
| **Risk Scoring ML** | `#EEF2FF` (Soft Indigo) | `#4F46E5` (Indigo) | `#312E81` (Deep Indigo) | Nuansa komputasi data |
| **Decision Gates** | `#FFFBEB` (Soft Amber) | `#D97706` (Amber) | `#92400E` (Deep Amber) | Titik percabangan |
| **RAG Knowledge** | `#F5F3FF` (Soft Violet) | `#7C3AED` (Violet) | `#5B21B6` (Deep Violet) | Basis pengetahuan |
| **LLM Arbiter** | `#F0FDFA` (Soft Teal) | `#0D9488` (Teal) | `#115E59` (Deep Teal) | Penalaran AI |
| **Success / Approved** | `#F0FDF4` (Soft Mint) | `#16A34A` (Green) | `#166534` (Deep Green) | Status lolos audit |
| **Human-in-the-Loop** | `#FDF2F8` (Soft Pink) | `#DB2777` (Magenta) | `#9D174D` (Deep Magenta) | Intervensi dokter manusia |
| **Subgraph Boxes** | `#F8FAFC` (Slate Tint) | `#CBD5E1` (Slate Border) | `#0F172A` (Slate Header) | Kotak pembungkus fase |
