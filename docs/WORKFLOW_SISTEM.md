# Workflow Sistem GARDA-JKN (Ringkas, To The Point, & Font Hitam)

Diagram alur kerja penanganan klaim BPJS Kesehatan ini telah disederhanakan agar **to the point**, mudah dipahami dalam sekali lihat, dengan **seluruh font berwarna hitam pekat (`#000000`)** dan bebas dari kotak bertingkat yang membingungkan.

---

## 📊 Diagram Mermaid (Versi To The Point & Font Hitam)

```mermaid
flowchart TD
    %% Styling Definisi - Font Hitam Pekat (#000000) & Background Lembut
    classDef startNode fill:#EFF6FF,stroke:#2563EB,stroke-width:2px,color:#000000;
    classDef securityNode fill:#FEF2F2,stroke:#DC2626,stroke-width:2px,color:#000000;
    classDef mlNode fill:#EEF2FF,stroke:#4F46E5,stroke-width:2px,color:#000000;
    classDef decisionNode fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#000000;
    classDef arbiterNode fill:#F0FDFA,stroke:#0D9488,stroke-width:2px,color:#000000;
    classDef hitlNode fill:#FDF2F8,stroke:#DB2777,stroke-width:2px,color:#000000;
    classDef successNode fill:#F0FDF4,stroke:#16A34A,stroke-width:2px,color:#000000;
    classDef rejectNode fill:#FEF2F2,stroke:#B91C1C,stroke-width:2px,color:#000000;

    A(["1. Klaim RS Masuk (JSON Payload)"]):::startNode
    B["2. Intake & Security Node<br/>• Sensor NIK & Nama Pasien (UU PDP No. 27/2022)<br/>• Pemindaian Prompt Injection / Jailbreak"]:::securityNode
    C["3. Risk Scoring Node (Lapis 1 ML Engine)<br/>• Evaluasi Anomali Finansial & Biaya (XGBoost + SHAP)"]:::mlNode
    D{"Klaim Anomali?"}:::decisionNode
    
    E(["Auto-Approved<br/>Klaim Bersih Wajar & Pembayaran Diteruskan"]):::successNode
    
    F["4. RAG Retrieval & Arbiter Node (Lapis 2 & 3)<br/>• Qdrant Vector Search Pedoman PNPK Kemenkes RI<br/>• LLM DeepSeek-Chat Menyusun Berita Acara Medis"]:::arbiterNode
    G{"Status Rekomendasi?"}:::decisionNode
    
    H(["Status: APPROVED / DOWNGRADED<br/>Berita Acara Putusan Otomatis Diterbitkan"]):::successNode
    I["5. Human-in-the-Loop (HITL)<br/>Draf BAP Didorong ke Dasbor VClaim UI"]:::hitlNode
    J(["Dokter Verifikator BPJS<br/>Mengetuk Palu Keputusan Hukum Terakhir"]):::hitlNode
    
    K(["Security Alert: DITOLAK<br/>Terdeteksi Serangan Siber"]):::rejectNode

    %% Alur Proses Ringkas & Linear
    A --> B
    B -- "Aman & Data Bersih" --> C
    B -- "Terdeteksi Jailbreak" --> K
    C --> D
    D -- "Inlier (Skor Wajar)" --> E
    D -- "Outlier (Curiga)" --> F
    F --> G
    G -- "Rekomendasi Pasti" --> H
    G -- "Ambigu (ESCALATED)" --> I
    I --> J
```

---

## 🖼️ File Gambar PNG untuk Microsoft Word
File gambar PNG resolusi tinggi siap pakai telah diperbarui di:
- **File:** `docs/evidence/plot_workflow_system.png`
- **Di Word:** Pilih menu **Insert > Pictures > This Device** dan pilih file tersebut.
- **Proposal Word Otomatis:** Sudah disematkan ke [`docs/Proposal_Healthkathon_2026_GARDA_JKN.docx`](file:///home/wmaulanaaishq/projects/bpjs_2025/docs/Proposal_Healthkathon_2026_GARDA_JKN.docx) pada Bagian 3.
