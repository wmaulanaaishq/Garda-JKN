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

# Berikan akses eksekusi ke skrip start.sh
RUN chmod +x start.sh

# Hugging Face Spaces secara default hanya membuka port 7860 ke publik
EXPOSE 7860

# Gunakan skrip start.sh sebagai pintu masuk (menyala dua layanan sekaligus)
ENTRYPOINT ["./start.sh"]
