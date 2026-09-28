import streamlit as st
import json
from app.agents.workflow import garda_app

st.set_page_config(page_title="SIMRS V-Claim | GARDA-JKN", layout="wide", initial_sidebar_state="expanded")

# --- CSS INJECTION (SIMRS V-Claim Aesthetic) ---
st.markdown("""
<style>
    /* Mengubah warna Sidebar (Abu-abu gelap ala SIMRS) */
    [data-testid="stSidebar"] {
        background-color: #3b4248 !important;
        color: #e0e0e0;
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    
    /* Highlight aktif di Sidebar (Aksen Hijau Toska) */
    .css-17lntkn {
        border-left: 4px solid #1abc9c;
        background-color: #2c3236;
    }

    /* Modifikasi Header & Main Container */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        background-color: #f8f9fa;
        color: #212529;
    }
    
    /* Styling Tabs ala VClaim */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #e9ecef;
        padding: 5px 5px 0px 5px;
        border-radius: 5px 5px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        color: #495057;
        font-weight: 500;
        border: 1px solid #dee2e6;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1abc9c !important;
        color: #ffffff !important;
        border-color: #1abc9c !important;
    }
    
    /* Styling Tombol Aksi */
    .stButton>button {
        background-color: #1abc9c;
        color: white !important;
        border-radius: 4px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #16a085;
    }

    /* Kotak Hasil Analisis */
    .result-box {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 100%;
    }
    
    /* Header Top Bar */
    .top-bar {
        background-color: white;
        padding: 15px 20px;
        border-bottom: 2px solid #1abc9c;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .top-bar h3 {
        margin: 0;
        color: #2c3e50;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- TOP NAVIGATION BAR MOCKUP ---
st.markdown("""
<div class="top-bar">
    <h3>🏥 SIMRSGOS2 | RSUP. Dr. Wahidin Sudirohusodo</h3>
    <span style="color: #7f8c8d; font-size: 0.9rem;">Mode: Adjudikasi Otomatis (GARDA-JKN)</span>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR (Data Klaim) ---
st.sidebar.markdown("### ⚙️ Master - BPJS")
st.sidebar.markdown("Menerima *Payload* dari Modul Rekam Medis / Billing untuk diproses ke V-Claim.")

default_claim = {
    "id_kunjungan": "K-11201",
    "nama_pasien": "Agus Pratama",
    "nik": "3201012345678903",
    "usia": 55,
    "diag_awal": "Pneumonia Berat",
    "diag_sekunder_1": "Gagal Napas (Respiratory Failure)",
    "diag_sekunder_2": "Sepsis",
    "tindakan_1": "Pemasangan Ventilator Mekanik",
    "tindakan_2": "Perawatan ICU Intensif",
    "icu_days": 6,
    "severity_level": 3,
    "biaya_tagih": 28000000,
    "durasi_rawat": 12
}

claim_input = st.sidebar.text_area("JSON Payload Tindakan & Tagihan:", value=json.dumps(default_claim, indent=2), height=400)
process_button = st.sidebar.button("Kirim ke V-Claim (Evaluasi AI)")

# --- MAIN CONTENT AREA (Tabs) ---
tab_garda, tab_referensi, tab_peserta, tab_sep, tab_monitoring = st.tabs([
    "🛡️ Adjudikasi AI (GARDA-JKN)", 
    "Referensi", 
    "Peserta", 
    "SEP", 
    "Monitoring"
])

with tab_garda:
    st.markdown("#### Analisis Klaim Medis & Deteksi Anomali Otonom")
    
    if process_button:
        try:
            claim_data = json.loads(claim_input)
            st.info("📡 Menjalankan Evaluasi GARDA-JKN...")
            
            with st.spinner("Mengolah 4 Juta Parameter XGBoost & DeepSeek LLM..."):
                # Menjalankan LangGraph agent secara langsung (Tanpa HTTP API)
                initial_state = {"claim_data": claim_data}
                final_state = garda_app.invoke(initial_state)
                
                result = {
                    "decision": final_state.get("final_status", "UNKNOWN"),
                    "adjudication_reason": final_state.get("adjudication_reason", ""),
                    "ml_risk_score": final_state.get("ml_risk_score", 0.0),
                    "ml_explanation": final_state.get("ml_explanation", ""),
                    "is_anomalous": final_state.get("is_anomalous", False),
                    "rag_context": final_state.get("rag_context", "")
                }
                
                # Menggunakan container kustom untuk hasil
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.subheader("⚖️ Keputusan Arbiter (Lapis 3)")
                    status = result.get("decision", "UNKNOWN")
                    
                    if status == "APPROVED":
                        st.success(f"**STATUS: {status} (Layak Bayar)**")
                    elif status == "DOWNGRADED":
                        st.error(f"**STATUS: {status} (Terindikasi Upcoding!)**")
                    else:
                        st.warning(f"**STATUS: {status} (Eskalasi Verifikator)**")
                        
                    st.write("**Justifikasi Medis:**")
                    st.info(result.get('adjudication_reason', ''))
                    
                    st.write("**📚 Referensi Hukum (Qdrant RAG):**")
                    st.caption(result.get("rag_context", "Tidak ada rujukan khusus."))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                with col2:
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.subheader("📊 Metrik Auditor (Lapis 1)")
                    is_anomali = result.get("is_anomalous", False)
                    score = result.get('ml_risk_score', 0) * 100
                    
                    if is_anomali:
                        st.error(f"⚠️ RISIKO FRAUD TINGGI (Skor: {score:.1f}%)")
                    else:
                        st.success(f"✅ KLAIM WAJAR (Skor Risiko: {score:.1f}%)")
                    
                    st.markdown("**SHAP Auditor Reason Codes (BAP):**")
                    st.warning(result.get('ml_explanation', 'Tidak ada anomali terdeteksi.'))
                    st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Kesalahan pemrosesan data: {e}")
    else:
        st.info("👈 Silakan modifikasi data klaim di Sidebar dan klik 'Kirim ke V-Claim (Evaluasi AI)' untuk memulai.")

with tab_referensi:
    st.markdown("#### Database Referensi Faskes")
    st.write("Area ini menampilkan daftar faskes rujukan sesuai desain SIMRS asli.")
    
with tab_peserta:
    st.markdown("#### Validasi Kepesertaan BPJS")
    st.write("Integrasi dengan layanan pengecekan NIK/No. Kartu BPJS pasien.")
