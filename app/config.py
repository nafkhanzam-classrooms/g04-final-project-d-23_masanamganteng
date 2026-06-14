"""Central configuration for Jempol Turbo."""

import os
from __future__ import annotations

APP_NAME = "Jempol Turbo"
APP_DESCRIPTION = "Real-Time Typing Battle berbasis WebSocket + Raw TCP Python."

HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("PORT", os.getenv("HTTP_PORT", "8000")))

TCP_HOST = os.getenv("TCP_HOST", "127.0.0.1")
TCP_PORT = int(os.getenv("TCP_PORT", "5050"))

COUNTDOWN_SECONDS = 5
MAX_RUNTIME_SECONDS = 200
REFRESH_GRACE_SECONDS = 8
ROOM_RESULT_TTL_SECONDS = 120
WAITING_ROOM_TTL_SECONDS = 600
CLEANUP_INTERVAL_SECONDS = 0.5

MIN_PLAYERS_PER_ROOM = 2
MAX_PLAYERS_PER_ROOM = 6
MAX_PACKET_BYTES = 16 * 1024
MAX_NAME_LENGTH = 24
MAX_TYPED_EXTRA_CHARS = 32

GAME_TYPES = {
    "easy": {
        "word_min": 15,
        "word_max": 20,
        "all_lowercase": True,
        "add_punctuation": False,
    },
    "medium": {
        "word_min": 25,
        "word_max": 30,
        "all_lowercase": False,
        "add_punctuation": True,
    },
    "hard": {
        "word_min": 45,
        "word_max": 50,
        "all_lowercase": False,
        "add_punctuation": True,
    },
}

DEFAULT_GAME_TYPE = "easy"

MAX_INPUT_JUMP_CHARS = 8