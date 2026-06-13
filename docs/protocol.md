# Desain Protokol Jempol Turbo

Jempol Turbo memakai dua layer komunikasi:

1. Browser ke FastAPI memakai WebSocket.
2. FastAPI ke core game memakai raw TCP socket Python.

TCP core memakai JSON-line framing. Satu packet adalah satu JSON object UTF-8 dan diakhiri `\n`.

## Format Packet TCP

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

Field:

- `type`: jenis command.
- `seq`: sequence number non-negatif.
- `room_id`: wajib untuk command terkait room.
- `session_id`: identitas 1 tab browser.
- `payload`: object data.

## Command Utama

- `CREATE_ROOM`
- `JOIN_ROOM`
- `RESTORE_SESSION`
- `HARD_START`
- `INPUT_UPDATE`
- `DISCONNECT`
- `LEAVE_ROOM`
- `LATENCY_PING`

## Event Utama

- `ROOM_CREATED`
- `JOINED_ROOM`
- `RESTORED_SESSION`
- `WAITING_UPDATE`
- `ROOM_PREPARE`
- `COUNTDOWN`
- `MATCH_START`
- `STATE_UPDATE`
- `PERSONAL_RESULT`
- `GLOBAL_RESULT`
- `ROOM_LIST_UPDATE`
- `ERROR`

## Validasi Packet

Server menolak packet jika:

- JSON rusak.
- `type` tidak dikenal.
- `seq` bukan integer non-negatif.
- `payload` bukan object.
- `session_id` atau `room_id` tidak valid.
- ukuran packet melebihi limit.
- command tidak sesuai state game.
