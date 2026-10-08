import os
import requests
import re
from urllib.parse import urljoin

urls = [
    "https://kemkes.go.id/id/pnpk-tatalaksana-diabetes-melitus-tipe-2-dewasa",
    "https://kemkes.go.id/id/pnpk-hipertensi-dewasa-kemenkes-2026",
    "https://kemkes.go.id/id/pnpk-tata-laksana-sindrom-koroner-akut-2026"
]

out_dir = "/home/wmaulanaaishq/projects/bpjs_2025/project Garda-JKN/Data RAG"
os.makedirs(out_dir, exist_ok=True)

for url in urls:
    print(f"\n🔍 Mencari PDF di: {url}")
    try:
        html = requests.get(url, timeout=10).text
        # Cari tautan download PDF di dalam halaman HTML
        match = re.search(r'href="(/app_asset/file_content_download/[^"]+\.pdf)"', html)
        if match:
            pdf_path = match.group(1)
            pdf_url = urljoin("https://kemkes.go.id", pdf_path)
            
            # Ekstrak judul dari URL asli
            title_match = re.search(r'id/([^/]+)$', url)
            title = title_match.group(1) if title_match else "Dokumen"
            
            out_file = os.path.join(out_dir, f"PNPK_{title}.pdf")
            if not os.path.exists(out_file):
                print(f"⬇️ Mendownload: {pdf_url}")
                pdf_data = requests.get(pdf_url, timeout=20).content
                with open(out_file, 'wb') as f:
                    f.write(pdf_data)
                print(f"✅ Tersimpan: {os.path.basename(out_file)}")
            else:
                print(f"✅ File {os.path.basename(out_file)} sudah ada, melewati download.")
        else:
            print("❌ Link unduhan PDF tidak ditemukan di halaman ini.")
    except Exception as e:
        print(f"❌ Error saat mengakses {url}: {e}")
