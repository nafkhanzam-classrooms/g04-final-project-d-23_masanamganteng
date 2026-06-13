"""Internal TCP client used by FastAPI/WebSocket handlers.

This adapter keeps one TCP connection open instead of opening and closing a new
socket for every key press. It makes the production WebSocket -> TCP bridge much
lighter during typing spam.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app import config
from app.network.protocol import decode_packet, encode_packet

logger = logging.getLogger(__name__)


class TCPAdapter:
    def __init__(self, host: str = config.TCP_HOST, port: int = config.TCP_PORT) -> None:
        self.host = host
        self.port = port
        self.seq = 0
        self._io_lock = asyncio.Lock()
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def _connect_locked(self) -> None:
        if self._writer is not None and not self._writer.is_closing() and self._reader is not None:
            return
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)

    async def _close_locked(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def close(self) -> None:
        async with self._io_lock:
            await self._close_locked()

    async def send_command(
        self,
        command_type: str,
        *,
        room_id: str | None = None,
        session_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        packet: dict[str, Any] = {
            "type": command_type,
            "payload": payload or {},
        }
        if room_id:
            packet["room_id"] = room_id
        if session_id:
            packet["session_id"] = session_id

        async with self._io_lock:
            packet["seq"] = self.seq
            self.seq += 1

            for attempt in range(2):
                try:
                    await self._connect_locked()
                    assert self._reader is not None
                    assert self._writer is not None

                    self._writer.write(encode_packet(packet))
                    await self._writer.drain()

                    line = await asyncio.wait_for(self._reader.readline(), timeout=5)
                    if not line:
                        raise ConnectionError("TCP core closed connection")
                    response = decode_packet(line.strip())
                    return response.get("payload", {}).get("events", [])
                except Exception as exc:
                    await self._close_locked()
                    if attempt == 0:
                        continue
                    logger.warning("tcp adapter command failed: %s", exc)
                    return [{"type": "ERROR", "payload": {"message": f"tcp adapter error: {exc}"}}]

        return []
