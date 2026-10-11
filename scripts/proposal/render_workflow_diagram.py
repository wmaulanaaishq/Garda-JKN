import os
from playwright.sync_api import sync_playwright

MERMAID_DIAGRAM = """
flowchart TD
    %% Styling Definisi Khusus Background Putih (Light Theme / Word Document)
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

    %% Subgraph Styling
    style S1 fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A
    style S2 fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A
    style S3 fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A
    style S4 fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A
"""

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            background-color: #FFFFFF;
            margin: 0;
            padding: 30px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        #container {{
            background-color: #FFFFFF;
            padding: 20px;
        }}
        .mermaid {{
            background-color: #FFFFFF;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div class="mermaid">
{MERMAID_DIAGRAM}
        </div>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                background: '#FFFFFF',
                primaryColor: '#EFF6FF',
                primaryTextColor: '#1E3A8A',
                primaryBorderColor: '#2563EB',
                lineColor: '#475569',
                secondaryColor: '#F8FAFC',
                tertiaryColor: '#FFFFFF',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: '14px'
            }}
        }});
    </script>
</body>
</html>
"""

def generate_png():
    output_dir = "docs/evidence"
    os.makedirs(output_dir, exist_ok=True)
    output_png = os.path.join(output_dir, "plot_workflow_system.png")
    
    html_path = "temp_workflow.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE)
        
    print("🎨 Merender diagram Mermaid dengan latar belakang putih murni...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(device_scale_factor=2)  # High resolution / Retina quality
        page.goto(f"file://{os.path.abspath(html_path)}")
        page.wait_for_selector(".mermaid svg", timeout=15000)
        
        # Cari elemen svg dan screenshot
        element = page.locator("#container")
        element.screenshot(path=output_png)
        browser.close()
        
    if os.path.exists(html_path):
        os.remove(html_path)
        
    print(f"✅ Berhasil membuat gambar diagram di: {output_png}")
    return output_png

if __name__ == "__main__":
    generate_png()
