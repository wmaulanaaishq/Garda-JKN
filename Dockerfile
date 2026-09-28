FROM python:3.10-slim

WORKDIR /app

# Install pustaka sistem yang dibutuhkan
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Salin requirements.txt dan install dependensi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode sumber ke dalam container
COPY . .

# Hugging Face Spaces secara default hanya membuka port 7860 ke publik
EXPOSE 7860

# Gunakan streamlit secara langsung
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
