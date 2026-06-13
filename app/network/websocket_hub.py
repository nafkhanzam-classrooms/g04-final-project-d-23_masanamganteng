"""WebSocket connection registry and broadcast helpers."""

from __future__ import annotations

import contextlib
from collections import defaultdict
from fastapi import WebSocket

from app.game.manager import GameManager


class WebSocketHub:
    def __init__(self, manager: GameManager) -> None:
        self.manager = manager
        self.home_clients: set[WebSocket] = set()
        self.room_clients: dict[str, set[WebSocket]] = defaultdict(set)
        self.session_ws: dict[str, WebSocket] = {}

    async def connect_home(self, ws: WebSocket) -> None:
        await ws.accept()
        self.home_clients.add(ws)
        await self.send_json(ws, self.manager.home_event())

    def disconnect_home(self, ws: WebSocket) -> None:
        self.home_clients.discard(ws)

    async def connect_room(self, room_id: str, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self.room_clients[room_id].add(ws)
        self.session_ws[session_id] = ws

    def disconnect_room(self, room_id: str, session_id: str, ws: WebSocket) -> None:
        self.room_clients[room_id].discard(ws)
        if not self.room_clients[room_id]:
            self.room_clients.pop(room_id, None)
        if self.session_ws.get(session_id) is ws:
            self.session_ws.pop(session_id, None)

    async def dispatch_events(self, events: list[dict]) -> None:
        for event in events:
            event_type = event.get("type")
            room_id = event.get("room_id")
            session_id = event.get("session_id")
            if event_type == "ROOM_LIST_UPDATE":
                await self.broadcast_home(event)
            elif event_type in {"JOINED_ROOM", "RESTORED_SESSION", "PERSONAL_RESULT"} and session_id:
                await self.send_to_session(session_id, event)
            elif room_id:
                await self.broadcast_room(room_id, event)

    async def broadcast_home(self, event: dict) -> None:
        for ws in list(self.home_clients):
            await self.send_json(ws, event, on_error=lambda: self.disconnect_home(ws))

    async def broadcast_room(self, room_id: str, event: dict) -> None:
        for ws in list(self.room_clients.get(room_id, set())):
            await self.send_json(ws, event, on_error=lambda: self.room_clients[room_id].discard(ws))

    async def send_to_session(self, session_id: str, event: dict) -> None:
        ws = self.session_ws.get(session_id)
        if ws:
            await self.send_json(ws, event, on_error=lambda: self.session_ws.pop(session_id, None))

    async def send_json(self, ws: WebSocket, event: dict, on_error=None) -> None:
        with contextlib.suppress(Exception):
            await ws.send_json(event)
            return
        if on_error:
            on_error()
