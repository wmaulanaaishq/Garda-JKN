import os
from playwright.sync_api import sync_playwright

MERMAID_DIAGRAM = """
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

    %% Alur Proses Ringkas & Deterministic
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
            padding: 24px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        #container {{
            background-color: #FFFFFF;
            padding: 12px;
        }}
        .nodeLabel, .edgeLabel, text, tspan, span, div {{
            color: #000000 !important;
            fill: #000000 !important;
            font-weight: 600;
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
                primaryTextColor: '#000000',
                primaryBorderColor: '#2563EB',
                lineColor: '#475569',
                secondaryColor: '#FFFFFF',
                tertiaryColor: '#FFFFFF',
                edgeLabelBackground: '#FFFFFF',
                textColor: '#000000',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: '13px'
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
        
    print("🎨 Merender diagram Mermaid yang to the point dengan font hitam...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 1400}, device_scale_factor=2)
        page.goto(f"file://{os.path.abspath(html_path)}")
        page.wait_for_selector(".mermaid svg", timeout=15000)
        
        element = page.locator("#container")
        element.screenshot(path=output_png)
        browser.close()
        
    if os.path.exists(html_path):
        os.remove(html_path)
        
    print(f"✅ Berhasil membuat gambar diagram di: {output_png}")
    return output_png

if __name__ == "__main__":
    generate_png()
