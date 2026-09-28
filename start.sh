#!/bin/bash

# 1. Jalankan layanan Microservice Backend (FastAPI) di latar belakang (port 8000)
echo "Menjalankan GARDA-JKN FastAPI Backend..."
python api.py &

# Beri waktu sedikit agar API menyala sebelum UI dijalankan
sleep 3

# 2. Jalankan layanan Frontend (Streamlit) di latar depan (port 7860)
# Port 7860 adalah port wajib yang diekspos oleh Hugging Face Spaces
echo "Menjalankan V-Claim Streamlit Frontend..."
streamlit run app.py --server.port=7860 --server.address=0.0.0.0
