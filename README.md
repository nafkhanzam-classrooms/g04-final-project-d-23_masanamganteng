[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/4SHtB1vz)

# Jempol Turbo: Real-Time Typing Battle

**Jempol Turbo: Real-Time Typing Battle** adalah game typing battle berbasis jaringan yang mempertemukan beberapa pemain dalam satu room untuk berlomba mengetik teks yang sama secara real-time.

UI utama berjalan di browser menggunakan HTTP dan WebSocket, sedangkan core networking memakai **raw TCP socket Python** melalui internal TCP adapter. Server bertindak sebagai authoritative game server yang mengatur room, player session, countdown, state synchronization, progress, WPM, CPM, akurasi, typo, ranking, reconnect, timeout, logging, dan validasi packet.

---

| NRP        | Nama                         |
| :--------: | ---------------------------- |
| 5025231027 | Naufal Dariskarim            |
| 5025231042 | Rynofaldi Damario Dzaki      |
| 5025231187 | Dapunta Adyapaksi Ratyanasja |

| Mata Kuliah          | Kelas |
| :------------------: | :---: |
| Pemrograman Jaringan | D     |

---

## Daftar Isi

* [1. Identitas Project](#1-identitas-project)
* [2. Ringkasan Project](#2-ringkasan-project)
* [3. Kesesuaian dengan Ketentuan Final Project](#3-kesesuaian-dengan-ketentuan-final-project)
* [4. Fitur Utama](#4-fitur-utama)
* [5. Teknologi yang Digunakan](#5-teknologi-yang-digunakan)
* [6. Arsitektur Sistem](#6-arsitektur-sistem)
* [7. Cara Kerja Aplikasi](#7-cara-kerja-aplikasi)
* [8. Endpoint Aplikasi](#8-endpoint-aplikasi)
* [9. State Room](#9-state-room)
* [10. Session, Reconnect, dan Leave Handling](#10-session-reconnect-dan-leave-handling)
* [11. Desain Protokol Aplikasi](#11-desain-protokol-aplikasi)
* [12. Alasan Memilih TCP](#12-alasan-memilih-tcp)
* [13. Game Logic dan Scoring](#13-game-logic-dan-scoring)
* [14. Struktur Project](#14-struktur-project)
* [15. Instalasi dan Cara Menjalankan](#15-instalasi-dan-cara-menjalankan)
* [16. Cara Bermain](#16-cara-bermain)
* [17. Testing](#17-testing)
* [18. Pengujian Performa dan Beban Server](#18-pengujian-performa-dan-beban-server)
* [19. Invalid Packet Test](#19-invalid-packet-test)
* [20. Hasil dan Analisis](#20-hasil-dan-analisis)
* [21. Kendala dan Solusi](#21-kendala-dan-solusi)
* [22. Logging](#22-logging)
* [23. Konfigurasi Penting](#23-konfigurasi-penting)
* [24. Keterbatasan dan Pengembangan Selanjutnya](#24-keterbatasan-dan-pengembangan-selanjutnya)
* [25. Kesimpulan](#25-kesimpulan)

---

## 1. Identitas Project

| Item                            | Keterangan                                |
| ------------------------------- | ----------------------------------------- |
| Nama project                    | **Jempol Turbo: Real-Time Typing Battle** |
| Kategori                        | Game Berbasis Jaringan                    |
| Backend                         | Python                                    |
| Frontend                        | HTML, CSS, VanillaJS                      |
| Core networking                 | Raw TCP socket Python                     |
| Real-time browser communication | WebSocket                                 |
| Web framework                   | FastAPI                                   |
| Format message                  | JSON-line                                 |
| Storage                         | In-memory repository                      |
| Target demo awal                | Localhost                                 |
| HTTP port                       | `8000`                                    |
| TCP core port                   | `5050`                                    |

---

## 2. Ringkasan Project

Jempol Turbo adalah game typing battle real-time. Pemain dapat membuat room, bergabung ke room yang tersedia, menunggu pemain lain, lalu bertanding mengetik teks yang sama setelah countdown selesai.

Saat pertandingan berjalan, setiap pemain akan melihat progress pemain lain secara real-time dalam bentuk progress bar dengan ikon roket. Server menghitung metrik permainan seperti progress, WPM, CPM, akurasi, jumlah typo, accuracy point, status pemain, dan ranking akhir.

![State Waiting](/screenshot/state_waiting.png)
![State Running](/screenshot/state_running.png)
![State Finished](/screenshot/state_finished.png)

---

## 3. Kesesuaian dengan Ketentuan Final Project

### Checklist Ketentuan Game Berbasis Jaringan

| Ketentuan                     | Implementasi di Jempol Turbo                                        |  Status |
| ----------------------------- | ------------------------------------------------------------------- | ------: |
| Minimal 2 orang bermain       | Room bisa diisi 2 sampai 6 pemain                                   | Selesai |
| Room system                   | Ada create room, join room, leave room                              | Selesai |
| Matchmaking                   | Room list real-time menampilkan room yang bisa diikuti              | Selesai |
| Synchronization state         | Server broadcast `STATE_UPDATE` ke semua pemain                     | Selesai |
| Menggunakan TCP atau UDP      | Menggunakan raw TCP socket Python                                   | Selesai |
| Menjelaskan alasan protokol   | TCP dipilih karena reliable dan menjaga urutan packet               | Selesai |
| Real-time update              | Browser menerima update melalui WebSocket                           | Selesai |
| Game state synchronization    | State `waiting`, `prepare`, `running`, `finished` dikontrol server  | Selesai |
| Reconnect handling            | Refresh aman dengan `sessionStorage` dan grace period               | Selesai |
| Ping/latency indicator        | Client mengirim `LATENCY_PING`, server membalas latency             | Selesai |
| Logging aktivitas player      | Server mencatat event dan koneksi pada log                          | Selesai |
| Anti-invalid packet sederhana | Server menolak JSON rusak, unknown type, invalid seq, payload salah | Selesai |
| Ranking system                | Ranking akhir berdasarkan finished, timeout, leave                  | Selesai |
| Load test                     | Simulator TCP bot tersedia                                          | Selesai |

---

## 4. Fitur Utama

### Fitur User

* Landing page `/`
* Home page `/home`
* Create room `/create_room`
* Room page `/room/<room_id>`
* Room list real-time
* Create room dengan nama, jumlah pemain, dan tipe permainan
* Join room berdasarkan daftar room tersedia
* Waiting modal saat menunggu player
* Hard start jika pemain lebih dari 1
* Auto start jika room penuh
* Countdown sebelum mulai
* Typing area ala Monkeytype
* Karakter benar berwarna hijau
* Karakter salah berwarna merah
* Current cursor pada posisi ketik
* Progress bar real-time dengan ikon roket
* Result pribadi
* Result global
* Back to home setelah selesai

### Fitur Game

* Game type:

  * `easy`
  * `medium`
  * `hard`
* Dynamic text generator berbasis pola kalimat
* Progress dihitung per-character dan posisi
* Case-sensitive untuk medium dan hard
* Typo counter
* Accuracy percentage
* Accuracy point
* WPM dan CPM
* Ranking akhir
* Timeout handling
* Leave handling

### Fitur Jaringan

* Browser real-time memakai WebSocket
* Core game networking memakai raw TCP socket Python
* TCP adapter internal dari FastAPI ke TCP core
* JSON-line protocol
* Sequence number validation
* Payload validation
* Session validation
* Anti-invalid packet
* Latency ping/pong
* Load simulation dengan bot TCP
* Grace period untuk refresh/reconnect

---

## 5. Teknologi yang Digunakan

| Teknologi                           | Fungsi                                          |
| ----------------------------------- | ----------------------------------------------- |
| Python 3.10+                        | Bahasa utama                                    |
| FastAPI                             | HTTP route dan WebSocket endpoint               |
| Uvicorn                             | ASGI server                                     |
| Raw TCP socket / asyncio TCP server | Core networking game                            |
| WebSocket                           | Komunikasi real-time antara browser dan FastAPI |
| HTML                                | Struktur halaman                                |
| CSS                                 | UI, dark/light mode, progress bar, typing style |
| Vanilla JavaScript                  | Logic frontend, WebSocket, typing handler       |
| JSON                                | Serialization message                           |
| Pytest                              | Unit testing                                    |
| In-memory repository                | Penyimpanan room/player sementara               |
| Script simulator                    | Load test dan invalid packet test               |

---

## 6. Arsitektur Sistem

Arsitektur final project:

```text
Browser Web UI
        |
        | WebSocket
        v
FastAPI WebSocket Layer
        |
        | Internal TCP Client / Adapter
        v
Python Raw TCP Core Server
        |
        v
Game Engine
Room, Player, State, Scoring, Progress, Typing Logic
```

### Penjelasan Arsitektur

1. **Browser Web UI**
   Digunakan oleh pemain untuk membuka halaman, membuat room, bergabung ke room, mengetik teks, melihat progress, dan melihat hasil akhir.

2. **FastAPI WebSocket Layer**
   Menangani HTTP page dan koneksi WebSocket dari browser. WebSocket digunakan karena browser tidak menyediakan raw TCP socket secara langsung.

3. **Internal TCP Client / Adapter**
   Menjadi bridge antara WebSocket layer dan raw TCP core server. Setiap command dari browser diteruskan ke TCP server menggunakan packet JSON.

4. **Python Raw TCP Core Server**
   Server TCP yang menerima packet game, memvalidasi protocol, dan meneruskan command ke GameManager. Bagian ini menjadi implementasi socket programming.

5. **Game Engine**
   Berisi logic room, player, state transition, scoring, progress, typing validation, reconnect, timeout, leave, ranking, dan cleanup.

---

## 7. Cara Kerja Aplikasi

### Alur Utama

```text
User membuka browser
        |
        v
GET / atau /home
        |
        v
User membuat room atau join room
        |
        v
Browser membuka WebSocket ke /ws/room/<room_id>
        |
        v
FastAPI menerima event dari browser
        |
        v
TCPAdapter meneruskan command ke raw TCP server
        |
        v
TCP server validasi packet
        |
        v
GameManager update state
        |
        v
Server menghasilkan event STATE_UPDATE
        |
        v
FastAPI broadcast ke browser
        |
        v
UI progress bar dan roket bergerak real-time
```

### Alur Pertandingan

1. Player membuka `/home`.
2. Player membuat room melalui `/create_room`.
3. Player lain melihat room tersebut di room list real-time.
4. Player lain klik **Gabung**.
5. Jika pemain sudah lebih dari 1, room dapat dimulai.
6. Jika room penuh, game otomatis masuk `prepare`.
7. Server menjalankan countdown.
8. Setelah countdown selesai, state berubah menjadi `running`.
9. Player mengetik target text.
10. Client mengirim `INPUT_UPDATE` ke server.
11. Server menghitung progress, WPM, CPM, accuracy, typo, dan score.
12. Server broadcast `STATE_UPDATE`.
13. Jika player selesai, server mengirim `PERSONAL_RESULT`.
14. Jika semua player selesai, leave, atau timeout, server mengirim `GLOBAL_RESULT`.
15. Room masuk state `finished`.

---

## 8. Endpoint Aplikasi

| Endpoint             | Method    | Fungsi                          |
| -------------------- | --------- | ------------------------------- |
| `/`                  | GET       | Landing page                    |
| `/home`              | GET       | Home page dan daftar room       |
| `/create_room`       | GET       | Form membuat room               |
| `/room/<room_id>`    | GET       | Halaman utama pertandingan      |
| `/api/rooms`         | POST      | Membuat room baru               |
| `/ws/home`           | WebSocket | Broadcast room list real-time   |
| `/ws/room/<room_id>` | WebSocket | Komunikasi real-time dalam room |

### `/`

Landing page berisi:

* Judul game
* Deskripsi singkat
* Tombol **Ayo Main** ke `/home`

### `/home`

Home page berisi:

* Header
* Toggle dark/light mode
* Card untuk create room
* List room real-time
* Tombol **Gabung** untuk masuk room

Room yang ditampilkan hanya room dengan kondisi:

```text
state == waiting
current_players < max_players
```

Room penuh atau sudah mulai tidak ditampilkan di list room.

### `/create_room`

Form pembuatan room:

* Nama player
* Jumlah pemain
* Game type:

  * easy
  * medium
  * hard

Setelah room berhasil dibuat, player langsung diarahkan ke `/room/<room_id>` sebagai initiator.

### `/room/<room_id>`

Halaman pertandingan utama. Halaman ini menangani:

* Join modal
* Waiting modal
* Countdown
* Progress bar
* Typing area
* Personal result
* Global result
* Leave room
* Back to home

---

## 9. State Room

Room memiliki 4 state utama:

```text
waiting -> prepare -> running -> finished
```

### `waiting`

State saat room menunggu player.

Kondisi:

* Initiator sudah masuk room.
* Player lain dapat join.
* Room tampil di `/home` jika belum penuh.
* Tombol **Mulai Sekarang** aktif jika jumlah player lebih dari 1.
* Room auto-start jika jumlah player mencapai kapasitas maksimal.

### `prepare`

State countdown sebelum game dimulai.

Kondisi:

* Popup waiting ditutup.
* UI pertandingan ditampilkan.
* Target text sudah terlihat.
* Typing input masih terkunci.
* Countdown berjalan sesuai konfigurasi.

### `running`

State saat pertandingan berjalan.

Kondisi:

* Typing input aktif.
* Player mengetik target text.
* Progress dikirim ke server.
* Server broadcast state ke semua player.
* Result pribadi muncul saat player sendiri selesai.
* Result global menunggu semua player selesai, leave, atau timeout.

### `finished`

State saat pertandingan selesai.

Kondisi:

* Typing input terkunci.
* Progress final ditampilkan.
* Ranking global ditampilkan.
* Room akan dibersihkan setelah TTL tertentu.
* Player dapat kembali ke home.

---

## 10. Session, Reconnect, dan Leave Handling

### Session per Tab

Satu tab browser dianggap sebagai satu player session. Identitas session disimpan menggunakan `sessionStorage`.

Alasan menggunakan `sessionStorage`:

* Session berbeda untuk tiap tab.
* Satu browser bisa membuka beberapa tab sebagai player berbeda.
* Refresh halaman masih bisa restore session.
* Data session hilang jika tab ditutup.

### Refresh Handling

Refresh browser akan memutus WebSocket sementara. Server tidak langsung menganggap player leave. Server memberi grace period.

Jika client reconnect sebelum grace period habis:

```text
disconnect -> reconnect cepat -> session dipulihkan
```

### Close Tab Handling

Jika tab ditutup dan tidak reconnect sampai grace period habis:

```text
disconnect -> tidak reconnect -> player dianggap leave
```

### Leave Handling

Player bisa leave melalui:

* Tombol leave
* Back to home
* Close tab
* Disconnect melewati grace period

Jika player leave saat `waiting`, player dihapus dari room.
Jika player leave saat `prepare` atau `running`, player dianggap final dengan status `leave` dan ranking berada di bawah player finished dan timeout.

---

## 11. Desain Protokol Aplikasi

Jempol Turbo memakai dua layer komunikasi:

```text
Browser <-> FastAPI WebSocket
FastAPI <-> Raw TCP Core Server
```

### WebSocket Layer

WebSocket digunakan untuk komunikasi real-time antara browser dan FastAPI.

Contoh event dari browser:

```json
{
  "type": "INPUT_UPDATE",
  "payload": {
    "typed_text": "mahasiswa informatika"
  }
}
```

### TCP Core Layer

TCP core memakai JSON-line framing. Satu packet adalah satu JSON object UTF-8 dan diakhiri newline `\n`.

Contoh packet TCP:

```json
{
  "type": "INPUT_UPDATE",
  "seq": 7,
  "room_id": "ab12cd34",
  "session_id": "tab-xxxx",
  "payload": {
    "typed_text": "mahasiswa informatika"
  }
}
```

### Field Packet

| Field        |                Wajib | Fungsi                           |
| ------------ | -------------------: | -------------------------------- |
| `type`       |                   Ya | Jenis command atau event         |
| `seq`        |                   Ya | Sequence number non-negatif      |
| `room_id`    |   Untuk command room | Identitas room                   |
| `session_id` | Untuk command player | Identitas player session         |
| `payload`    |                   Ya | Data command dalam bentuk object |

### Command Utama Client ke Server

| Command           | Fungsi                                    |
| ----------------- | ----------------------------------------- |
| `CREATE_ROOM`     | Membuat room baru                         |
| `JOIN_ROOM`       | Join ke room yang tersedia                |
| `RESTORE_SESSION` | Restore session setelah refresh/reconnect |
| `HARD_START`      | Memulai room meskipun belum penuh         |
| `INPUT_UPDATE`    | Mengirim teks yang sedang diketik         |
| `DISCONNECT`      | Menandai WebSocket client terputus        |
| `LEAVE_ROOM`      | Keluar dari room                          |
| `LATENCY_PING`    | Mengukur latency client-server            |

### Event Utama Server ke Client

| Event              | Fungsi                               |
| ------------------ | ------------------------------------ |
| `ROOM_CREATED`     | Room berhasil dibuat                 |
| `JOINED_ROOM`      | Player berhasil join room            |
| `RESTORED_SESSION` | Session berhasil dipulihkan          |
| `WAITING_UPDATE`   | Update daftar player di waiting room |
| `ROOM_PREPARE`     | Room masuk countdown                 |
| `COUNTDOWN`        | Countdown sebelum start              |
| `MATCH_START`      | Pertandingan dimulai                 |
| `STATE_UPDATE`     | Sinkronisasi progress dan state      |
| `PERSONAL_RESULT`  | Hasil pribadi player                 |
| `GLOBAL_RESULT`    | Hasil akhir semua player             |
| `ROOM_LIST_UPDATE` | Update daftar room di home           |
| `ERROR`            | Packet invalid atau command gagal    |

### Validasi Packet

Server menolak packet jika:

* JSON rusak
* `type` tidak dikenal
* `seq` bukan integer non-negatif
* `payload` bukan object
* `session_id` kosong
* `room_id` tidak valid
* command tidak sesuai state game
* input mengandung control character yang tidak valid
* packet terlalu besar
* player belum terdaftar di room

Contoh response invalid packet:

```json
{
  "type": "TCP_RESPONSE",
  "seq": 0,
  "payload": {
    "events": [
      {
        "type": "ERROR",
        "payload": {
          "message": "packet is not valid json"
        }
      }
    ]
  }
}
```

---

## 12. Alasan Memilih TCP

Project ini memilih TCP sebagai core networking karena typing battle membutuhkan data yang:

* reliable
* berurutan
* konsisten antar-player
* tidak boleh hilang saat update penting
* mudah divalidasi dan dicatat

Jika menggunakan UDP, packet loss atau urutan packet yang berubah dapat membuat progress, WPM, dan ranking menjadi tidak konsisten. Untuk game seperti typing battle, reliability lebih penting daripada latency ekstrem seperti pada game shooter.

WebSocket tetap digunakan pada browser karena browser tidak menyediakan akses raw TCP socket secara langsung. Namun, WebSocket hanya menjadi layer komunikasi browser. Core game tetap diproses melalui raw TCP server Python.

---

## 13. Game Logic dan Scoring

### Game Type

| Game Type | Jumlah Kata |    Lowercase | Tanda Baca | Catatan                       |
| --------- | ----------: | -----------: | ---------: | ----------------------------- |
| `easy`    |       15-20 |           Ya |      Tidak | Cocok untuk demo cepat        |
| `medium`  |       25-30 | Tidak selalu |         Ya | Ada uppercase dan punctuation |
| `hard`    |       45-50 | Tidak selalu |         Ya | Teks lebih panjang            |

### Text Generator

Target text dibuat dinamis menggunakan template-based generator. Generator tidak hanya memilih kata secara random, tetapi menyusun pola kalimat agar teks tetap manusiawi dan logis.

Contoh topik kata:

* client
* server
* socket
* WebSocket
* TCP
* room
* progress
* latency
* packet
* reconnect
* final project
* game manager

### Progress

Progress dihitung berdasarkan karakter yang benar pada posisi yang benar.

Rumus sederhana:

```text
progress = jumlah_karakter_benar_di_posisi_yang_benar / panjang_target_text
```

Contoh:

```text
target: kamis
input : kumis
hasil : 4/5 benar = 80%
```

Contoh:

```text
target: senin
input : gajah
hasil : 0/5 benar = 0%
```

### Finish Condition

Player dianggap finish hanya jika:

```text
typed_text == target_text
```

Untuk medium dan hard, pengecekan bersifat case-sensitive.

### WPM

WPM dihitung dari jumlah karakter benar dan durasi mengetik.

```text
WPM = (correct_chars / 5) / elapsed_minutes
```

### CPM

CPM dihitung dari jumlah karakter benar per menit.

```text
CPM = correct_chars / elapsed_minutes
```

### Accuracy Percentage

Accuracy percentage menunjukkan persentase karakter benar terhadap panjang input.

```text
accuracy = correct_chars / typed_length * 100
```

### Typo Count

Typo count menghitung jumlah kesalahan input yang terjadi selama player mengetik.

### Accuracy Point

Accuracy point dihitung dengan rumus:

```text
accuracy_point = max(0, 100 - typo_count)
```

### Ranking

Urutan ranking:

```text
1. finished normal
2. timeout
3. leave
```

Prioritas ranking:

| Grup            | Prioritas                                              |
| --------------- | ------------------------------------------------------ |
| Finished normal | Finish duration tercepat, WPM, CPM, typo lebih sedikit |
| Timeout         | Progress tertinggi, accuracy point, typo lebih sedikit |
| Leave           | Progress tertinggi, accuracy point, typo lebih sedikit |

---

## 14. Struktur Project

```text
jempol-turbo/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── game/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── manager.py
│   │   ├── scoring.py
│   │   ├── text_generator.py
│   │   └── repository.py
│   │
│   ├── network/
│   │   ├── __init__.py
│   │   ├── protocol.py
│   │   ├── tcp_server.py
│   │   ├── tcp_adapter.py
│   │   └── websocket_hub.py
│   │
│   ├── web/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── templates/
│   │       ├── landing.html
│   │       ├── home.html
│   │       ├── create_room.html
│   │       └── room.html
│   │
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── common.js
│           ├── home.js
│           └── room.js
│
├── scripts/
│   ├── simulate_clients.py
│   └── send_invalid_packet.py
│
├── tests/
│   ├── test_protocol.py
│   ├── test_scoring.py
│   └── test_text_generator.py
│
├── logs/
│   └── .gitkeep
│
├── README.md
├── requirements.txt
└── run.py
```

### Penjelasan Folder

| Path                             | Fungsi                                            |
| -------------------------------- | ------------------------------------------------- |
| `app/main.py`                    | Entry point FastAPI app                           |
| `app/config.py`                  | Konfigurasi global                                |
| `app/game/models.py`             | Dataclass Room, Player, Stats                     |
| `app/game/manager.py`            | State machine dan lifecycle game                  |
| `app/game/scoring.py`            | Perhitungan progress, WPM, CPM, accuracy, ranking |
| `app/game/text_generator.py`     | Generator teks dinamis                            |
| `app/game/repository.py`         | In-memory room repository                         |
| `app/network/protocol.py`        | Encode, decode, validate packet                   |
| `app/network/tcp_server.py`      | Raw TCP server                                    |
| `app/network/tcp_adapter.py`     | Bridge FastAPI ke TCP server                      |
| `app/network/websocket_hub.py`   | Manajemen koneksi WebSocket                       |
| `app/web/routes.py`              | HTTP dan WebSocket route                          |
| `app/static/js/home.js`          | Logic room list real-time                         |
| `app/static/js/room.js`          | Logic gameplay dan typing                         |
| `scripts/simulate_clients.py`    | Load simulation bot                               |
| `scripts/send_invalid_packet.py` | Invalid packet test                               |
| `tests/`                         | Unit test                                         |

---

## 15. Instalasi dan Cara Menjalankan

Gunakan Python 3.10 atau lebih baru.

### Opsi 1: Menggunakan Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Opsi 2: Tanpa Virtual Environment

Jika dependency sudah terpasang di Python global:

```bash
pip install -r requirements.txt
python run.py
```

### Akses Aplikasi

Buka browser:

```text
http://127.0.0.1:8000
```

Raw TCP core berjalan di:

```text
127.0.0.1:5050
```

---

## 16. Cara Bermain

1. Jalankan server dengan:

```bash
python run.py
```

2. Buka browser ke:

```text
http://127.0.0.1:8000
```

3. Klik tombol **Ayo Main**.

4. Di halaman `/home`, klik **Buat Room**.

5. Isi form:

   * Nama player
   * Jumlah pemain
   * Game type: `easy`, `medium`, atau `hard`

6. Klik **Buat Room**.

7. Buka tab browser kedua atau browser lain.

8. Masuk ke `/home`.

9. Klik **Gabung** pada room yang tersedia.

10. Isi nama player berbeda.

11. Tunggu room penuh atau klik **Mulai Sekarang** jika pemain sudah lebih dari 1.

12. Tunggu countdown.

13. Saat status berubah menjadi `START`, ketik teks target.

14. Lihat progress roket, WPM, CPM, dan hasil akhir.

---

## 17. Testing

### Unit Test

Jalankan:

```bash
pytest
```

Hasil testing terakhir:

```text
collected 9 items

tests/test_protocol.py ...        [ 33%]
tests/test_scoring.py ....        [ 77%]
tests/test_text_generator.py ..   [100%]

9 passed in 0.04s
```

### Cakupan Unit Test

| Test File                | Cakupan                               |
| ------------------------ | ------------------------------------- |
| `test_protocol.py`       | Encode, decode, validasi packet       |
| `test_scoring.py`        | Progress, WPM, CPM, accuracy, ranking |
| `test_text_generator.py` | Generator teks easy, medium, hard     |

---

## 18. Pengujian Performa dan Beban Server

Load test dilakukan dengan simulator TCP bot.

### Cara Menjalankan

Terminal 1:

```bash
python run.py
```

Terminal 2:

```bash
python scripts/simulate_clients.py --pairs 3 --game-type easy
```

### Hasil Load Test Terakhir

```text
=== TCP Load Simulation ===
pairs=3
bots=6
finished=6
errors=0
duration=5.92s

=== Detail ===
bot-1-A | room=857ba8fe | finished=True | status=finished | progress=100% | wpm=2351.02 | cpm=11755.10 | typo=0 | errors=-
bot-1-B | room=857ba8fe | finished=True | status=finished | progress=100% | wpm=2351.02 | cpm=11755.10 | typo=0 | errors=-
bot-2-A | room=b816412c | finished=True | status=finished | progress=100% | wpm=2201.99 | cpm=11009.96 | typo=0 | errors=-
bot-2-B | room=b816412c | finished=True | status=finished | progress=100% | wpm=2201.99 | cpm=11009.96 | typo=0 | errors=-
bot-3-A | room=a687a0f4 | finished=True | status=finished | progress=100% | wpm=2167.85 | cpm=10839.26 | typo=0 | errors=-
bot-3-B | room=a687a0f4 | finished=True | status=finished | progress=100% | wpm=2167.85 | cpm=10839.26 | typo=0 | errors=-
```

### Ringkasan Hasil

| Skenario                 | Room | Bot | Finished | Error |     Durasi |
| ------------------------ | ---: | --: | -------: | ----: | ---------: |
| TCP load simulation easy |    3 |   6 |        6 |     0 | 5.92 detik |

### Catatan Analisis Load Test

WPM dan CPM bot sangat tinggi karena simulator mengetik dengan delay kecil. Angka tersebut tidak merepresentasikan kemampuan manusia, tetapi digunakan sebagai stress simulation untuk menguji apakah server mampu menangani banyak update input secara cepat.

Untuk simulasi lebih realistis, jalankan:

```bash
python scripts/simulate_clients.py --pairs 3 --game-type easy --delay 0.08
```

Untuk test lebih berat:

```bash
python scripts/simulate_clients.py --pairs 5 --game-type easy --delay 0.05
```

---

## 19. Invalid Packet Test

Invalid packet test digunakan untuk membuktikan bahwa server tidak langsung crash ketika menerima packet rusak atau tidak sesuai protokol.

### Cara Menjalankan

Terminal 1:

```bash
python run.py
```

Terminal 2:

```bash
python scripts/send_invalid_packet.py
```

### Hasil Invalid Packet Test Terakhir

```text
=== Invalid Packet Test ===

[BROKEN_JSON]
{"type":"TCP_RESPONSE","seq":0,"payload":{"events":[{"type":"ERROR","payload":{"message":"packet is not valid json"}}]}}

[UNKNOWN_PACKET_TYPE]
{"type":"TCP_RESPONSE","seq":0,"payload":{"events":[{"type":"ERROR","payload":{"message":"unknown packet type: UNKNOWN"}}]}}

[INVALID_SEQ]
{"type":"TCP_RESPONSE","seq":0,"payload":{"events":[{"type":"ERROR","payload":{"message":"seq must be non-negative integer"}}]}}

[INVALID_PAYLOAD]
{"type":"TCP_RESPONSE","seq":0,"payload":{"events":[{"type":"ERROR","payload":{"message":"payload must be object"}}]}}

Selesai. Jika semua response berisi ERROR dari server, anti-invalid packet bekerja.
```

### Ringkasan Invalid Packet

| Skenario            | Input Salah            | Response                                  |
| ------------------- | ---------------------- | ----------------------------------------- |
| Broken JSON         | JSON tidak valid       | `ERROR: packet is not valid json`         |
| Unknown packet type | `type` tidak dikenal   | `ERROR: unknown packet type`              |
| Invalid seq         | `seq` negatif          | `ERROR: seq must be non-negative integer` |
| Invalid payload     | `payload` bukan object | `ERROR: payload must be object`           |

---

## 20. Hasil dan Analisis

### Hasil Fungsional

| Fitur                   |   Status | Keterangan                                 |
| ----------------------- | -------: | ------------------------------------------ |
| Landing page            | Berhasil | `/` tampil dan tombol menuju `/home`       |
| Home page               | Berhasil | Room list real-time berjalan               |
| Create room             | Berhasil | Room berhasil dibuat                       |
| Join room               | Berhasil | Player kedua dapat bergabung               |
| Multi-tab session       | Berhasil | Tiap tab dianggap player berbeda           |
| Waiting state           | Berhasil | Popup waiting tampil                       |
| Prepare state           | Berhasil | Countdown berjalan                         |
| Running state           | Berhasil | Typing dan progress real-time              |
| Finished state          | Berhasil | Result pribadi dan global tampil           |
| Refresh handling        | Berhasil | Session dipulihkan dengan `sessionStorage` |
| Close tab handling      | Berhasil | Player dianggap leave setelah grace period |
| Invalid packet handling | Berhasil | Server mengirim response `ERROR`           |
| Load simulation         | Berhasil | 6 bot selesai tanpa error                  |

### Analisis Protokol

TCP dipilih karena typing battle membutuhkan urutan input yang konsisten. Jika packet progress tertukar atau hilang, progress bar dan ranking dapat menjadi salah. Dengan TCP, packet dikirim secara reliable dan berurutan.

WebSocket digunakan pada browser karena browser tidak dapat membuka raw TCP socket langsung. Namun, WebSocket bukan pengganti core TCP, karena semua command game tetap diteruskan ke raw TCP server melalui TCP adapter internal.

### Analisis State Synchronization

State game dikendalikan oleh server, bukan client. Client hanya mengirim input dan command, sedangkan server menentukan:

* kapan room mulai
* siapa yang aktif
* progress tiap player
* kapan player finish
* kapan room selesai
* ranking akhir

Model ini mengurangi risiko client memalsukan state.

### Analisis Reliability

Sistem menangani beberapa kondisi yang umum terjadi pada aplikasi jaringan:

* malformed packet
* reconnect setelah refresh
* disconnect saat game berjalan
* leave saat waiting atau running
* timeout jika player tidak selesai
* banyak room berjalan bersamaan

---

## 21. Kendala dan Solusi

| Kendala                                           | Penyebab                                                     | Solusi                                                                                       |
| ------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Browser tidak bisa raw TCP langsung               | Browser hanya mendukung HTTP/WebSocket, bukan raw TCP socket | Browser memakai WebSocket, lalu FastAPI meneruskan command ke raw TCP server melalui adapter |
| Refresh dan close tab sama-sama memutus WebSocket | Event browser tidak selalu bisa membedakan refresh dan close | Gunakan `sessionStorage` dan grace period                                                    |
| Tab berbeda sempat dianggap player yang sama      | Session browser dapat tercopy saat membuka tab baru          | Tambah tab session handling dan force new join                                               |
| Spam typing membuat CPU berat                     | Setiap input terlalu sering mengirim command                 | Tambah input throttling dan persistent TCP adapter                                           |
| Backspace sempat terasa stuck                     | Textarea native memindahkan caret atau menerima control key  | Input typing dibuat linear dan control key non-kompetisi diblok                              |
| Packet TCP tidak punya batas message bawaan       | TCP adalah byte stream                                       | Gunakan JSON-line framing dengan delimiter newline                                           |
| Client dapat mengirim packet rusak                | Packet dari client tidak selalu valid                        | Tambahkan protocol validator dan invalid packet response                                     |
| Player AFK dapat mengunci room                    | Player tidak finish dan tidak leave                          | Tambah max runtime dan timeout handling                                                      |
| Data hilang saat restart server                   | Storage masih in-memory                                      | Repository dibuat modular agar dapat diganti database                                        |

---

## 22. Logging

Server melakukan logging untuk aktivitas penting, seperti:

* server start
* server stop
* TCP client connected
* TCP client disconnected
* invalid packet
* room event
* error handling

Folder log:

```text
logs/
```

Contoh log TCP:

```text
INFO app.network.tcp_server tcp client connected ('127.0.0.1', 58339)
INFO app.network.tcp_server tcp client disconnected ('127.0.0.1', 58339)
INFO app.network.tcp_server raw tcp server stopped
```

Logging penting untuk demo karena menunjukkan aktivitas jaringan benar-benar terjadi di sisi server.

---

## 23. Konfigurasi Penting

Konfigurasi utama berada di:

```text
app/config.py
```

Contoh konfigurasi:

| Config                     | Fungsi                         |
| -------------------------- | ------------------------------ |
| `HTTP_HOST`                | Host HTTP/FastAPI              |
| `HTTP_PORT`                | Port HTTP/FastAPI              |
| `TCP_HOST`                 | Host raw TCP core              |
| `TCP_PORT`                 | Port raw TCP core              |
| `COUNTDOWN_SECONDS`        | Durasi countdown               |
| `MAX_RUNTIME_SECONDS`      | Durasi maksimal pertandingan   |
| `REFRESH_GRACE_SECONDS`    | Grace period reconnect         |
| `ROOM_RESULT_TTL_SECONDS`  | Waktu penyimpanan result room  |
| `WAITING_ROOM_TTL_SECONDS` | Waktu maksimal room waiting    |
| `MAX_PLAYERS_PER_ROOM`     | Batas player dalam room        |
| `GAME_TYPES`               | Konfigurasi easy, medium, hard |

---

## 24. Keterbatasan dan Pengembangan Selanjutnya

### Keterbatasan Saat Ini

* Storage masih in-memory.
* Data room hilang saat server restart.
* Belum ada database persistence.
* Belum ada spectator mode.
* Belum ada match replay permanen.
* Belum ada TLS/HTTPS lokal.
* Belum ada deployment permanen.
* Belum ada load balancing multi-server.

### Saran Pengembangan

* Menambahkan SQLite/PostgreSQL untuk menyimpan history match.
* Menambahkan leaderboard global.
* Menambahkan spectator mode.
* Menambahkan match replay.
* Menambahkan HTTPS/TLS.
* Menambahkan Docker deployment.
* Menambahkan Redis untuk shared state jika multi-server.
* Menambahkan dashboard admin untuk monitoring room dan player.
* Menambahkan grafik latency dan throughput.

---

## 25. Kesimpulan

Jempol Turbo berhasil mengimplementasikan game berbasis jaringan dengan konsep client-server, real-time synchronization, custom protocol, serialization, raw TCP socket programming, WebSocket, reconnect handling, latency indicator, invalid packet handling, dan load simulation.

Dengan arsitektur Browser Web UI -> FastAPI WebSocket Layer -> TCP Adapter -> Raw TCP Core Server -> Game Engine, project ini tetap nyaman digunakan melalui browser, tetapi masih mempertahankan implementasi pemrograman jaringan utama menggunakan Python raw TCP socket.

---

## Quick Command Summary

### Install

```bash
pip install -r requirements.txt
```

### Run App

```bash
python run.py
```

### Open App

```text
http://127.0.0.1:8000
```

### Unit Test

```bash
pytest
```

### Invalid Packet Test

```bash
python scripts/send_invalid_packet.py
```

### Load Test

```bash
python scripts/simulate_clients.py --pairs 3 --game-type easy
```

### Clear Browser Session

```js
sessionStorage.clear()
```