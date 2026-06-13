# Deploy dan Menjalankan

## Local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Buka:

```text
http://127.0.0.1:8000
```

Raw TCP core berjalan di:

```text
127.0.0.1:5050
```

## Demo Online Cepat

Untuk deadline mepet, jalankan lokal lalu gunakan tunnel seperti ngrok atau cloudflared untuk HTTP/WebSocket port `8000`.

Contoh ngrok:

```bash
ngrok http 8000
```

## Catatan

Aplikasi saat ini memakai in-memory storage, sehingga data room akan hilang jika server restart. Ini sengaja dibuat agar implementasi ringan untuk final project, namun struktur repository sudah disiapkan agar mudah diganti database.
