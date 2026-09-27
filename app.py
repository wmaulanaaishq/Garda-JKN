import streamlit as st
import json
import os
from app.agents.workflow import garda_app
from app.core.ml_engine import MLEngine

# Memuat model ML Lapis 1 (XGBoost) jika belum dimuat
st.set_page_config(page_title="GARDA-JKN | BPJS Adjudication AI", layout="wide")

st.title("🛡️ GARDA-JKN: AI Adjudikasi Klaim BPJS")
st.markdown("### Generative Agent for Risk Detection and Adjudication")
st.markdown("Sistem orkestrasi *Multi-Agent* dengan Lapis 1 (XGBoost) dan Lapis 2/3 (Qdrant RAG + DeepSeek-R1).")

st.sidebar.header("Data Klaim Pasien (Mockup V-Claim)")
# Contoh payload JSON klaim
default_claim = {
    "id_kunjungan": "K-99812",
    "nama_pasien": "Budi Santoso",
    "nik": "3201012345678901",
    "usia": 65,
    "diag_awal": "Stroke Iskemik",
    "diag_sekunder_1": "Gagal Ginjal Akut",
    "tindakan_1": "CT Scan Kepala",
    "severity_level": 3,
    "biaya_tagih": 15000000,
    "durasi_rawat": 2
}

claim_input = st.sidebar.text_area("JSON Payload dari RS:", value=json.dumps(default_claim, indent=2), height=300)

if st.sidebar.button("Proses Klaim (Adjudikasi Otonom)"):
    try:
        claim_data = json.loads(claim_input)
        
        st.info("Memulai Proses Investigasi Multi-Agen...")
        
        # Inisialisasi State Awal untuk LangGraph
        initial_state = {"claim_data": claim_data}
        
        # Menjalankan workflow (Graph)
        with st.spinner("AI sedang berpikir (Machine Learning + RAG + LLM Reasoning)..."):
            final_state = garda_app.invoke(initial_state)
            
        st.success("Proses Ajudikasi Selesai!")
        
        # Layout Hasil
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 Hasil Keputusan (Lapis 3: LLM Arbiter)")
            status = final_state.get("final_status", "UNKNOWN")
            
            if status == "APPROVED":
                st.success(f"**STATUS: {status}**")
            elif status == "DOWNGRADED":
                st.error(f"**STATUS: {status} (Terindikasi Upcoding!)**")
            else:
                st.warning(f"**STATUS: {status} (Eskalasi ke Verifikator)**")
                
            st.markdown(f"**Rasionalisasi Medis:**\n{final_state.get('adjudication_reason', '')}")
            
        with col2:
            st.subheader("📊 Metrik Deteksi Dini (Lapis 1: XGBoost)")
            is_anomali = final_state.get("is_anomalous", False)
            st.metric(label="Status Anomali Lapis 1", value="Terdeteksi" if is_anomali else "Normal")
            st.write(f"**Tingkat Risiko:** {final_state.get('ml_risk_score', 0):.2f}")
            st.write(f"**Penjelasan Variabel (SHAP):** {final_state.get('ml_explanation', '')}")
            
        st.divider()
        st.subheader("📚 Referensi Aturan (Lapis 2: Qdrant Vector DB)")
        with st.expander("Lihat Kutipan PNPK / INA-CBG yang Ditarik oleh RAG"):
            st.write(final_state.get("rag_context", "Tidak ada referensi terkait yang ditarik."))
            
        st.divider()
        st.subheader("🔒 Log Transparansi Data (Privacy Check)")
        st.write("Perhatikan bahwa NIK dan Nama Pasien telah disensor oleh *Intake Agent* sebelum dikirim ke Hugging Face (Sesuai UU PDP):")
        st.json(final_state.get("claim_data"))

    except Exception as e:
        st.error(f"Terjadi kesalahan saat parsing atau pemrosesan: {e}")
