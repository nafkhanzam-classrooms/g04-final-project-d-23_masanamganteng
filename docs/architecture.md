# Arsitektur Jempol Turbo

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

## Komponen

- `web/routes.py`: render HTTP page dan WebSocket endpoint.
- `network/websocket_hub.py`: daftar koneksi browser dan broadcast event.
- `network/tcp_adapter.py`: internal TCP client dari WebSocket ke TCP server.
- `network/tcp_server.py`: raw TCP server Python untuk command game.
- `game/manager.py`: state machine waiting, prepare, running, finished.
- `game/scoring.py`: progress per-character, WPM, CPM, typo, ranking.
- `game/text_generator.py`: generator teks dinamis berbasis pola kalimat.
- `game/repository.py`: in-memory repository yang bisa diganti database.

## State Room

```text
waiting -> prepare -> running -> finished
```

## Session

Satu tab browser adalah satu player session. Browser menyimpan `session_id` di `sessionStorage` agar refresh tidak memutus player. Jika WebSocket putus, server memberi grace period sebelum dianggap leave.
