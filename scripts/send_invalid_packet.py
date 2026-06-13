"""Send malformed/invalid packet to demonstrate anti-invalid packet handling."""

from __future__ import annotations

import asyncio
import contextlib
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import config


def raw_json_line(packet: dict) -> bytes:
    """Encode raw JSON without local protocol validation.

    Ini sengaja bypass encode_packet(), karena tujuan script ini adalah
    mengirim packet invalid ke server.
    """
    return json.dumps(packet, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


async def send_raw_packet(raw: bytes) -> str:
    reader, writer = await asyncio.open_connection(config.TCP_HOST, config.TCP_PORT)
    try:
        writer.write(raw)
        await writer.drain()

        line = await asyncio.wait_for(reader.readline(), timeout=3)
        return line.decode("utf-8", errors="replace").strip()
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


async def main() -> None:
    tests = [
        (
            "BROKEN_JSON",
            b'{"type":"BROKEN","seq":0,"payload":{}\n',
        ),
        (
            "UNKNOWN_PACKET_TYPE",
            raw_json_line({"type": "UNKNOWN", "seq": 0, "payload": {}}),
        ),
        (
            "INVALID_SEQ",
            raw_json_line({"type": "JOIN_ROOM", "seq": -1, "payload": {}}),
        ),
        (
            "INVALID_PAYLOAD",
            raw_json_line({"type": "JOIN_ROOM", "seq": 0, "payload": "not-object"}),
        ),
    ]

    print("=== Invalid Packet Test ===")

    for name, raw in tests:
        print(f"\n[{name}]")
        try:
            response = await send_raw_packet(raw)
            print(response)
        except Exception as exc:
            print(f"ERROR: {exc}")

    print("\nSelesai. Jika semua response berisi ERROR dari server, anti-invalid packet bekerja.")


if __name__ == "__main__":
    asyncio.run(main())