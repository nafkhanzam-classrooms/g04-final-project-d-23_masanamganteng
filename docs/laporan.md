# Laporan Project: Jempol Turbo

## Pendahuluan

Jempol Turbo adalah game typing battle real-time untuk mendemonstrasikan pemrograman jaringan dengan konsep client-server, WebSocket, raw TCP socket, serialization, state synchronization, latency indicator, reconnect handling, dan load testing.

## Deskripsi dan Tujuan Project

Pemain membuat atau bergabung ke room, lalu mengetik teks yang sama dalam kompetisi real-time. Server menghitung progress, CPM, WPM, akurasi, typo, ranking, serta mengunci hasil jika player selesai, timeout, atau leave.

## Arsitektur Sistem

Browser berkomunikasi dengan FastAPI melalui WebSocket. FastAPI meneruskan command ke raw TCP core server memakai TCP adapter internal. TCP server memvalidasi JSON packet lalu memanggil GameManager sebagai game engine.

## Desain Protokol Aplikasi

Protokol TCP memakai JSON-line. Setiap packet berisi `type`, `seq`, `room_id`, `session_id`, dan `payload`. Detail protocol ada di `docs/protocol.md`.

## Pengujian Performa dan Beban Server

Pengujian dilakukan dengan:

```bash
pytest
python scripts/simulate_clients.py --pairs 3 --game-type easy
python scripts/send_invalid_packet.py
```

Metrik yang dicatat:

| Skenario | Client | Berhasil | Error | Catatan |
|---|---:|---:|---:|---|
| Local test | TBD | TBD | TBD | Isi setelah run |

## Hasil dan Analisis

TCP dipilih karena typing battle membutuhkan urutan packet yang reliable. WebSocket digunakan pada browser karena browser tidak menyediakan raw TCP socket langsung, sedangkan raw TCP tetap menjadi core networking internal.

## Kendala dan Solusi

- Refresh dan close tab sama-sama memutus WebSocket. Solusinya memakai `sessionStorage` dan grace period.
- TCP adalah byte stream dan tidak punya batas message bawaan. Solusinya memakai JSON-line framing.
- Player AFK dapat mengunci room. Solusinya memakai `MAX_RUNTIME_SECONDS`.

## Kesimpulan dan Saran

Jempol Turbo memenuhi fitur game berbasis jaringan: room system, real-time update, state synchronization, reconnect handling, latency indicator, logging, anti-invalid packet, dan load test. Pengembangan berikutnya dapat menambahkan database, replay, dan deployment permanen.
