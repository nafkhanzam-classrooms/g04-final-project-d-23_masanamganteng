"""Raw TCP core server used by the production WebSocket layer and CLI scripts."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app import config
from app.game.manager import GameManager
from app.network.protocol import ProtocolError, decode_packet, encode_packet, error_packet, response_packet

logger = logging.getLogger(__name__)


class RawTCPServer:
    def __init__(self, manager: GameManager, host: str = config.TCP_HOST, port: int = config.TCP_PORT) -> None:
        self.manager = manager
        self.host = host
        self.port = port
        self.server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info("raw tcp server listening on %s:%s", self.host, self.port)

    async def stop(self) -> None:
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
            logger.info("raw tcp server stopped")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        logger.info("tcp client connected %s", peer)
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    packet = decode_packet(line.strip())
                    events = await self.manager.handle_command(packet)
                    response = response_packet(int(packet.get("seq", 0)), events)
                except ProtocolError as exc:
                    logger.warning("invalid tcp packet from %s: %s", peer, exc)
                    response = error_packet(0, str(exc))
                writer.write(encode_packet(response))
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info("tcp client disconnected %s", peer)
