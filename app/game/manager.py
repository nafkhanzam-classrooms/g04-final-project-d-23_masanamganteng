"""Game manager: state transitions, room/player lifecycle, and events."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from app import config
from app.game.models import Player, Room
from app.game.repository import InMemoryRepository
from app.game.scoring import build_rankings, compute_stats, is_exactly_finished
from app.game.text_generator import generate_text


class GameError(ValueError):
    pass


class GameManager:
    def __init__(self, repository: InMemoryRepository | None = None) -> None:
        self.repo = repository or InMemoryRepository()
        self.lock = asyncio.Lock()

    async def handle_command(self, packet: dict[str, Any]) -> list[dict[str, Any]]:
        command = packet.get("type")
        payload = packet.get("payload") or {}
        try:
            if command == "CREATE_ROOM":
                return await self.create_room(
                    creator_name=str(payload.get("name", "")),
                    max_players=int(payload.get("max_players", 2)),
                    game_type=str(payload.get("game_type", config.DEFAULT_GAME_TYPE)),
                    session_id=str(packet.get("session_id", "")),
                )
            if command == "JOIN_ROOM":
                return await self.join_room(
                    room_id=str(packet.get("room_id", "")),
                    name=str(payload.get("name", "")),
                    session_id=str(packet.get("session_id", "")),
                )
            if command == "RESTORE_SESSION":
                return await self.restore_session(
                    room_id=str(packet.get("room_id", "")),
                    session_id=str(packet.get("session_id", "")),
                )
            if command == "HARD_START":
                return await self.start_prepare(
                    room_id=str(packet.get("room_id", "")),
                    session_id=str(packet.get("session_id", "")),
                    reason="hard_start",
                )
            if command == "INPUT_UPDATE":
                return await self.update_input(
                    room_id=str(packet.get("room_id", "")),
                    session_id=str(packet.get("session_id", "")),
                    typed_text=str(payload.get("typed_text", "")),
                )
            if command == "DISCONNECT":
                return await self.mark_disconnected(
                    room_id=str(packet.get("room_id", "")),
                    session_id=str(packet.get("session_id", "")),
                )
            if command == "LEAVE_ROOM":
                return await self.leave_room(
                    room_id=str(packet.get("room_id", "")),
                    session_id=str(packet.get("session_id", "")),
                )
            if command == "LATENCY_PING":
                return await self.update_latency(
                    room_id=str(packet.get("room_id", "")),
                    session_id=str(packet.get("session_id", "")),
                    client_ts=payload.get("client_ts"),
                )
            return [self.error_event(f"unknown command: {command}")]
        except (GameError, ValueError) as exc:
            return [self.error_event(str(exc))]

    def error_event(self, message: str) -> dict[str, Any]:
        return {"type": "ERROR", "payload": {"message": message}}

    async def create_room(self, creator_name: str, max_players: int, game_type: str, session_id: str) -> list[dict[str, Any]]:
        async with self.lock:
            name = self._validate_name(creator_name)
            session_id = self._validate_session_id(session_id)
            if game_type not in config.GAME_TYPES:
                game_type = config.DEFAULT_GAME_TYPE
            if max_players < config.MIN_PLAYERS_PER_ROOM or max_players > config.MAX_PLAYERS_PER_ROOM:
                raise GameError(f"jumlah pemain harus {config.MIN_PLAYERS_PER_ROOM}-{config.MAX_PLAYERS_PER_ROOM}")
            room_id = uuid.uuid4().hex[:8]
            room = Room(
                room_id=room_id,
                creator_name=name,
                creator_session_id=session_id,
                game_type=game_type,
                max_players=max_players,
                target_text=generate_text(game_type),
            )
            player = Player(session_id=session_id, name=name, is_initiator=True)
            room.players[session_id] = player
            self.repo.save_room(room)
            return [
                self.room_event("ROOM_CREATED", room, session_id),
                self.home_event(),
            ]

    async def join_room(self, room_id: str, name: str, session_id: str) -> list[dict[str, Any]]:
        async with self.lock:
            room = self._get_room(room_id)
            session_id = self._validate_session_id(session_id)
            name = self._validate_name(name)
            if room.state != "waiting":
                raise GameError("room sudah tidak menerima pemain")
            if room.current_waiting_count() >= room.max_players:
                raise GameError("room sudah penuh")
            if session_id in room.players:
                player = room.players[session_id]
                player.connected = True
                player.disconnected_at = None
                player.name = player.name or name
            else:
                if any(p.name.lower() == name.lower() and p.status != "leave" for p in room.players.values()):
                    raise GameError("nama sudah dipakai di room ini")
                room.players[session_id] = Player(session_id=session_id, name=name)
            events = [self.private_room_event("JOINED_ROOM", room, session_id), self.waiting_event(room), self.home_event()]
            if room.current_waiting_count() >= room.max_players:
                self._start_prepare_locked(room, reason="room_full")
                events.append(self.room_event("ROOM_PREPARE", room, session_id))
                events.append(self.home_event())
            return events

    async def restore_session(self, room_id: str, session_id: str) -> list[dict[str, Any]]:
        async with self.lock:
            room = self._get_room(room_id)
            session_id = self._validate_session_id(session_id)
            player = room.players.get(session_id)
            if not player:
                raise GameError("session belum terdaftar di room ini")
            if player.status == "leave":
                raise GameError("session ini sudah leave")
            player.connected = True
            player.disconnected_at = None
            event_type = "RESTORED_SESSION"
            return [self.private_room_event(event_type, room, session_id), self.waiting_event(room), self.state_event(room)]

    async def start_prepare(self, room_id: str, session_id: str, *, reason: str) -> list[dict[str, Any]]:
        async with self.lock:
            room = self._get_room(room_id)
            session_id = self._validate_session_id(session_id)
            if not room.can_hard_start(session_id):
                raise GameError("room belum bisa dimulai")
            self._start_prepare_locked(room, reason=reason)
            return [self.room_event("ROOM_PREPARE", room, session_id), self.home_event()]

    async def update_input(self, room_id: str, session_id: str, typed_text: str) -> list[dict[str, Any]]:
        async with self.lock:
            room = self._get_room(room_id)
            player = self._get_player(room, session_id)
            if room.state != "running" or room.running_started_at is None:
                raise GameError("game belum berjalan")
            if player.is_final():
                return [self.state_event(room)]
            typed_text = self._sanitize_typed_text(typed_text)
            typed_text = typed_text[: len(room.target_text) + config.MAX_TYPED_EXTRA_CHARS]
            # Ignore duplicate echo/no-op input so spam key events do not trigger
            # unnecessary state broadcasts. Shorter strings from Backspace are
            # still processed normally.
            if typed_text == player.typed_text:
                return []
            elapsed = time.monotonic() - room.running_started_at
            player.previous_typed_text = player.typed_text
            player.typed_text = typed_text[: len(room.target_text)]
            player.stats = compute_stats(
                room.target_text,
                player.typed_text,
                elapsed,
                previous_text=player.previous_typed_text,
                previous_typo_count=player.stats.typo_count,
            )
            events: list[dict[str, Any]] = [self.state_event(room)]
            if is_exactly_finished(room.target_text, player.typed_text):
                self._finish_player_locked(room, player, status="finished")
                events.append(self.personal_result_event(room, player))
                if self._all_players_final(room):
                    self._finish_room_locked(room, reason="all_players_done")
                    events.append(self.global_result_event(room, reason="all_players_done"))
                else:
                    events.append(self.state_event(room))
            return events

    async def update_latency(self, room_id: str, session_id: str, client_ts: Any) -> list[dict[str, Any]]:
        async with self.lock:
            room = self._get_room(room_id)
            player = self._get_player(room, session_id)
            try:
                player.latency_ms = round((time.time() * 1000.0) - float(client_ts), 2)
            except (TypeError, ValueError):
                player.latency_ms = None
            return [{"type": "LATENCY_PONG", "room_id": room.room_id, "payload": {"latency_ms": player.latency_ms}}, self.state_event(room)]

    async def mark_disconnected(self, room_id: str, session_id: str) -> list[dict[str, Any]]:
        async with self.lock:
            room = self.repo.get_room(room_id)
            if not room or session_id not in room.players:
                return []
            player = room.players[session_id]
            player.connected = False
            player.disconnected_at = time.monotonic()
            return [self.state_event(room)]

    async def leave_room(self, room_id: str, session_id: str) -> list[dict[str, Any]]:
        async with self.lock:
            room = self._get_room(room_id)
            player = self._get_player(room, session_id)
            events = self._apply_leave_locked(room, player, explicit=True)
            return events

    async def tick(self) -> list[dict[str, Any]]:
        async with self.lock:
            now = time.monotonic()
            events: list[dict[str, Any]] = []
            for room in list(self.repo.list_rooms()):
                events.extend(self._handle_disconnected_grace_locked(room, now))
                if room.state == "prepare" and room.prepare_started_at is not None:
                    if now - room.prepare_started_at >= config.COUNTDOWN_SECONDS:
                        self._start_running_locked(room)
                        events.append(self.room_event("MATCH_START", room, None))
                    else:
                        events.append(self.room_event("COUNTDOWN", room, None))
                elif room.state == "running" and room.running_started_at is not None:
                    if now - room.running_started_at >= config.MAX_RUNTIME_SECONDS:
                        for player in room.players.values():
                            if not player.is_final():
                                self._finish_player_locked(room, player, status="timeout")
                        self._finish_room_locked(room, reason="max_runtime")
                        events.append(self.global_result_event(room, reason="max_runtime"))
                    elif self._all_players_final(room):
                        self._finish_room_locked(room, reason="all_players_done")
                        events.append(self.global_result_event(room, reason="all_players_done"))
                    else:
                        events.append(self.state_event(room))
                self._cleanup_room_if_needed_locked(room, now, events)
            if events:
                events.append(self.home_event())
            return events

    def _start_prepare_locked(self, room: Room, *, reason: str) -> None:
        if room.state != "waiting":
            return
        room.state = "prepare"
        room.prepare_started_at = time.monotonic()
        room.target_text = generate_text(room.game_type)
        for player in room.players.values():
            if player.connected and player.status == "waiting":
                player.status = "active"

    def _start_running_locked(self, room: Room) -> None:
        if room.state != "prepare":
            return
        room.state = "running"
        room.running_started_at = time.monotonic()
        for player in room.players.values():
            if not player.is_final():
                player.status = "active"
                player.started_at = room.running_started_at

    def _finish_player_locked(self, room: Room, player: Player, *, status: str) -> None:
        if player.is_final():
            return
        now = time.monotonic()
        elapsed = now - (room.running_started_at or now)
        player.status = status  # type: ignore[assignment]
        player.connected = status != "leave" and player.connected
        player.finished_at = now
        player.finish_duration = round(elapsed, 3)

    def _finish_room_locked(self, room: Room, *, reason: str) -> None:
        if room.state == "finished":
            return
        room.state = "finished"
        room.finished_at = time.monotonic()

    def _apply_leave_locked(self, room: Room, player: Player, *, explicit: bool) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if room.state == "waiting":
            was_initiator = player.is_initiator
            room.players.pop(player.session_id, None)
            if was_initiator:
                room.hard_start_unlocked_for_all = True
            events += [self.waiting_event(room), self.home_event()]
            if not room.players:
                self.repo.delete_room(room.room_id)
                events.append(self.home_event())
        elif room.state in {"prepare", "running"}:
            self._finish_player_locked(room, player, status="leave")
            player.connected = False
            events.append(self.state_event(room))
            if self._all_players_final(room):
                self._finish_room_locked(room, reason="all_players_done")
                events.append(self.global_result_event(room, reason="all_players_done"))
        else:
            player.connected = False
        return events

    def _handle_disconnected_grace_locked(self, room: Room, now: float) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for player in list(room.players.values()):
            if player.connected or player.disconnected_at is None or player.is_final():
                continue
            if now - player.disconnected_at < config.REFRESH_GRACE_SECONDS:
                continue
            events.extend(self._apply_leave_locked(room, player, explicit=False))
        return events

    def _cleanup_room_if_needed_locked(self, room: Room, now: float, events: list[dict[str, Any]]) -> None:
        if room.room_id not in self.repo.rooms:
            return
        if room.state == "waiting" and not room.players:
            self.repo.delete_room(room.room_id)
            events.append(self.home_event())
            return
        if room.state == "waiting" and now - room.created_at > config.WAITING_ROOM_TTL_SECONDS:
            self.repo.delete_room(room.room_id)
            events.append(self.home_event())
            return
        if room.state == "finished" and room.finished_at and now - room.finished_at > config.ROOM_RESULT_TTL_SECONDS:
            self.repo.delete_room(room.room_id)
            events.append(self.home_event())

    def _all_players_final(self, room: Room) -> bool:
        return bool(room.players) and all(player.is_final() for player in room.players.values())

    def _get_room(self, room_id: str) -> Room:
        room = self.repo.get_room(room_id)
        if not room:
            raise GameError("room tidak ditemukan")
        return room

    def _get_player(self, room: Room, session_id: str) -> Player:
        session_id = self._validate_session_id(session_id)
        player = room.players.get(session_id)
        if not player:
            raise GameError("player belum terdaftar")
        return player

    def _sanitize_typed_text(self, typed_text: str) -> str:
        """Remove control characters that should never affect a typing race.

        Allowed characters include letters, numbers, spaces, and punctuation.
        Blocked examples: newline, tab, escape, and other ASCII control chars.
        """
        clean_chars = []

        for char in str(typed_text or ""):
            code = ord(char)

            # Keep normal printable characters, including space.
            if code >= 32 and code != 127:
                clean_chars.append(char)

        return "".join(clean_chars)

    def _validate_name(self, name: str) -> str:
        clean = " ".join(name.strip().split())
        if not clean:
            raise GameError("nama wajib diisi")
        if len(clean) > config.MAX_NAME_LENGTH:
            raise GameError(f"nama maksimal {config.MAX_NAME_LENGTH} karakter")
        return clean

    def _validate_session_id(self, session_id: str) -> str:
        clean = str(session_id or "").strip()
        if not clean:
            raise GameError("session_id wajib ada")
        if len(clean) > 96:
            raise GameError("session_id terlalu panjang")
        return clean

    def home_event(self) -> dict[str, Any]:
        return {"type": "ROOM_LIST_UPDATE", "payload": {"rooms": self.available_rooms_snapshot()}}

    def waiting_event(self, room: Room) -> dict[str, Any]:
        return self.room_event("WAITING_UPDATE", room, None)

    def state_event(self, room: Room) -> dict[str, Any]:
        return self.room_event("STATE_UPDATE", room, None)

    def personal_result_event(self, room: Room, player: Player) -> dict[str, Any]:
        return {
            "type": "PERSONAL_RESULT",
            "room_id": room.room_id,
            "session_id": player.session_id,
            "payload": {"player": player.to_public_dict()},
        }

    def global_result_event(self, room: Room, *, reason: str) -> dict[str, Any]:
        return {
            "type": "GLOBAL_RESULT",
            "room_id": room.room_id,
            "payload": {
                "reason": reason,
                "room": room.to_public_dict(),
                "rankings": build_rankings(list(room.players.values())),
            },
        }

    def private_room_event(self, event_type: str, room: Room, session_id: str) -> dict[str, Any]:
        event = self.room_event(event_type, room, session_id)
        event["session_id"] = session_id
        return event

    def room_event(self, event_type: str, room: Room, viewer_session_id: str | None) -> dict[str, Any]:
        return {
            "type": event_type,
            "room_id": room.room_id,
            "payload": {"room": room.to_public_dict(viewer_session_id)},
        }

    def available_rooms_snapshot(self) -> list[dict[str, Any]]:
        return [room.to_list_item() for room in self.repo.list_available_rooms()]
