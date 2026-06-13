"""JSON-line protocol helpers for the raw TCP core server."""

from __future__ import annotations

import json
from typing import Any

from app import config

CLIENT_COMMANDS = {
    "CREATE_ROOM",
    "JOIN_ROOM",
    "RESTORE_SESSION",
    "HARD_START",
    "INPUT_UPDATE",
    "DISCONNECT",
    "LEAVE_ROOM",
    "LATENCY_PING",
}


class ProtocolError(ValueError):
    pass


def encode_packet(packet: dict[str, Any]) -> bytes:
    validate_packet(packet)
    raw = json.dumps(packet, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(raw) > config.MAX_PACKET_BYTES:
        raise ProtocolError("packet too large")
    return raw + b"\n"


def decode_packet(raw_line: bytes) -> dict[str, Any]:
    if not raw_line:
        raise ProtocolError("empty packet")
    if len(raw_line) > config.MAX_PACKET_BYTES:
        raise ProtocolError("packet too large")
    try:
        packet = json.loads(raw_line.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ProtocolError("packet is not valid utf-8") from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError("packet is not valid json") from exc
    if not isinstance(packet, dict):
        raise ProtocolError("packet must be json object")
    validate_packet(packet)
    return packet


def validate_packet(packet: dict[str, Any]) -> None:
    packet_type = packet.get("type")
    if not isinstance(packet_type, str) or not packet_type:
        raise ProtocolError("type is required")
    if len(packet_type) > 48:
        raise ProtocolError("type is too long")
    if packet_type not in CLIENT_COMMANDS and packet_type not in {"TCP_RESPONSE", "ERROR"}:
        raise ProtocolError(f"unknown packet type: {packet_type}")

    seq = packet.get("seq", 0)
    if not isinstance(seq, int) or seq < 0:
        raise ProtocolError("seq must be non-negative integer")

    payload = packet.get("payload", {})
    if payload is None:
        packet["payload"] = {}
    elif not isinstance(payload, dict):
        raise ProtocolError("payload must be object")

    session_id = packet.get("session_id")
    if session_id is not None and (not isinstance(session_id, str) or len(session_id) > 96):
        raise ProtocolError("session_id invalid")

    room_id = packet.get("room_id")
    if room_id is not None and (not isinstance(room_id, str) or len(room_id) > 32):
        raise ProtocolError("room_id invalid")


def response_packet(seq: int, events: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "TCP_RESPONSE", "seq": seq, "payload": {"events": events}}


def error_packet(seq: int, message: str) -> dict[str, Any]:
    return {"type": "TCP_RESPONSE", "seq": seq, "payload": {"events": [{"type": "ERROR", "payload": {"message": message}}]}}
