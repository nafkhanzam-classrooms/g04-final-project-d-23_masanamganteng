"""Domain models for Jempol Turbo."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

RoomState = Literal["waiting", "prepare", "running", "finished"]
PlayerStatus = Literal["waiting", "active", "finished", "timeout", "leave"]


@dataclass
class TypingStats:
    typed_chars: int = 0
    correct_chars: int = 0
    wrong_chars: int = 0
    progress: float = 0.0
    accuracy_percent: float = 100.0
    typo_count: int = 0
    accuracy_point: int = 100
    cpm: float = 0.0
    wpm: float = 0.0

    def to_dict(self) -> dict:
        return {
            "typed_chars": self.typed_chars,
            "correct_chars": self.correct_chars,
            "wrong_chars": self.wrong_chars,
            "progress": self.progress,
            "accuracy_percent": self.accuracy_percent,
            "typo_count": self.typo_count,
            "accuracy_point": self.accuracy_point,
            "cpm": self.cpm,
            "wpm": self.wpm,
        }


@dataclass
class Player:
    session_id: str
    name: str
    is_initiator: bool = False
    status: PlayerStatus = "waiting"
    connected: bool = True
    joined_at: float = field(default_factory=time.monotonic)
    disconnected_at: float | None = None
    typed_text: str = ""
    previous_typed_text: str = ""
    stats: TypingStats = field(default_factory=TypingStats)
    started_at: float | None = None
    finished_at: float | None = None
    finish_duration: float | None = None
    latency_ms: float | None = None

    def is_final(self) -> bool:
        return self.status in {"finished", "timeout", "leave"}

    def to_public_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "is_initiator": self.is_initiator,
            "status": self.status,
            "connected": self.connected,
            "joined_at": round(self.joined_at, 3),
            "disconnected_at": round(self.disconnected_at, 3) if self.disconnected_at else None,
            "typed_text": self.typed_text,
            "started_at": round(self.started_at, 3) if self.started_at else None,
            "finished_at": round(self.finished_at, 3) if self.finished_at else None,
            "finish_duration": self.finish_duration,
            "latency_ms": self.latency_ms,
            **self.stats.to_dict(),
        }


@dataclass
class Room:
    room_id: str
    creator_name: str
    creator_session_id: str
    game_type: str
    max_players: int
    target_text: str
    state: RoomState = "waiting"
    created_at: float = field(default_factory=time.monotonic)
    prepare_started_at: float | None = None
    running_started_at: float | None = None
    finished_at: float | None = None
    hard_start_unlocked_for_all: bool = False
    players: dict[str, Player] = field(default_factory=dict)

    def connected_players(self) -> list[Player]:
        return [p for p in self.players.values() if p.connected and not p.is_final()]

    def active_players(self) -> list[Player]:
        return [p for p in self.players.values() if not p.is_final()]

    def player_count(self) -> int:
        return len([p for p in self.players.values() if p.status != "leave" or self.state in {"prepare", "running", "finished"}])

    def current_waiting_count(self) -> int:
        return len([p for p in self.players.values() if p.connected and p.status == "waiting"])

    def is_available(self) -> bool:
        return self.state == "waiting" and self.current_waiting_count() < self.max_players

    def can_hard_start(self, session_id: str) -> bool:
        if self.state != "waiting":
            return False
        if self.current_waiting_count() < 2:
            return False
        player = self.players.get(session_id)
        if not player or not player.connected:
            return False
        return player.is_initiator or self.hard_start_unlocked_for_all

    def to_list_item(self) -> dict:
        return {
            "room_id": self.room_id,
            "creator_name": self.creator_name,
            "game_type": self.game_type,
            "state": self.state,
            "current_players": self.current_waiting_count(),
            "max_players": self.max_players,
            "available": self.is_available(),
        }

    def to_public_dict(self, viewer_session_id: str | None = None) -> dict:
        viewer = self.players.get(viewer_session_id or "")
        now = time.monotonic()
        countdown_remaining = 0.0
        elapsed = 0.0
        if self.state == "prepare" and self.prepare_started_at is not None:
            from app import config
            countdown_remaining = max(0.0, config.COUNTDOWN_SECONDS - (now - self.prepare_started_at))
        if self.running_started_at is not None:
            elapsed = max(0.0, now - self.running_started_at)
        return {
            "room_id": self.room_id,
            "creator_name": self.creator_name,
            "creator_session_id": self.creator_session_id,
            "game_type": self.game_type,
            "max_players": self.max_players,
            "state": self.state,
            "target_text": self.target_text,
            "created_at": round(self.created_at, 3),
            "prepare_started_at": round(self.prepare_started_at, 3) if self.prepare_started_at else None,
            "running_started_at": round(self.running_started_at, 3) if self.running_started_at else None,
            "finished_at": round(self.finished_at, 3) if self.finished_at else None,
            "countdown_remaining": round(countdown_remaining, 2),
            "elapsed": round(elapsed, 2),
            "current_players": self.current_waiting_count() if self.state == "waiting" else len(self.players),
            "hard_start_unlocked_for_all": self.hard_start_unlocked_for_all,
            "can_hard_start": self.can_hard_start(viewer_session_id or ""),
            "viewer": viewer.to_public_dict() if viewer else None,
            "players": [p.to_public_dict() for p in self.players.values()],
        }
