"""TCP load simulation for Jempol Turbo.

Run app first:

    python run.py

Then run:

    python scripts/simulate_clients.py --pairs 3 --game-type easy
"""

from __future__ import annotations

import argparse
import asyncio
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import config
from app.network.protocol import decode_packet, encode_packet


@dataclass
class BotResult:
    name: str
    session_id: str
    room_id: str | None = None
    finished: bool = False
    status: str = "unknown"
    progress: float = 0.0
    wpm: float = 0.0
    cpm: float = 0.0
    typo_count: int = 0
    duration: float = 0.0
    errors: list[str] = field(default_factory=list)


class TCPBot:
    def __init__(self, name: str, game_type: str, delay: float) -> None:
        self.name = name
        self.game_type = game_type
        self.delay = delay
        self.session_id = f"bot-{name}-{random.randint(10000, 99999)}"
        self.room_id: str | None = None
        self.seq = 0
        self.target_text = ""
        self.room_state = ""
        self.finished = False
        self.result = BotResult(name=name, session_id=self.session_id)

    async def command(self, packet_type: str, payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        reader, writer = await asyncio.open_connection(config.TCP_HOST, config.TCP_PORT)

        packet: dict[str, Any] = {
            "type": packet_type,
            "seq": self.seq,
            "session_id": self.session_id,
            "payload": payload or {},
        }

        if self.room_id:
            packet["room_id"] = self.room_id

        self.seq += 1

        try:
            writer.write(encode_packet(packet))
            await writer.drain()

            line = await asyncio.wait_for(reader.readline(), timeout=5)
            response = decode_packet(line.strip())
            events = response.get("payload", {}).get("events", [])

            self.consume_events(events)
            return events

        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    def consume_events(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            event_type = event.get("type")
            payload = event.get("payload") or {}

            if event_type == "ERROR":
                message = str(payload.get("message", "server error"))
                self.result.errors.append(message)
                continue

            room = payload.get("room")
            if isinstance(room, dict):
                self.room_id = room.get("room_id") or self.room_id
                self.room_state = room.get("state") or self.room_state
                self.target_text = room.get("target_text") or self.target_text

                for player in room.get("players", []):
                    if player.get("session_id") == self.session_id:
                        self.result.status = str(player.get("status", self.result.status))
                        self.result.progress = float(player.get("progress", self.result.progress) or 0)
                        self.result.wpm = float(player.get("wpm", self.result.wpm) or 0)
                        self.result.cpm = float(player.get("cpm", self.result.cpm) or 0)
                        self.result.typo_count = int(player.get("typo_count", self.result.typo_count) or 0)
                        if self.result.status == "finished":
                            self.finished = True
                            self.result.finished = True

            if event_type == "PERSONAL_RESULT":
                player = payload.get("player") or {}
                self.finished = True
                self.result.finished = True
                self.result.status = str(player.get("status", "finished"))
                self.result.progress = float(player.get("progress", 1) or 1)
                self.result.wpm = float(player.get("wpm", 0) or 0)
                self.result.cpm = float(player.get("cpm", 0) or 0)
                self.result.typo_count = int(player.get("typo_count", 0) or 0)

            if event_type == "GLOBAL_RESULT":
                rankings = payload.get("rankings") or []
                for player in rankings:
                    if player.get("session_id") == self.session_id or player.get("name") == self.name:
                        self.finished = True
                        self.result.finished = True
                        self.result.status = str(player.get("status", "finished"))
                        self.result.progress = float(player.get("progress", 1) or 1)
                        self.result.wpm = float(player.get("wpm", 0) or 0)
                        self.result.cpm = float(player.get("cpm", 0) or 0)
                        self.result.typo_count = int(player.get("typo_count", 0) or 0)

    async def wait_until_running(self, timeout: float = 12.0) -> bool:
        started = time.monotonic()

        while time.monotonic() - started < timeout:
            await self.command("RESTORE_SESSION")

            if self.room_state == "running" and self.target_text:
                return True

            await asyncio.sleep(0.2)

        self.result.errors.append("timeout waiting running state")
        return False

    async def type_until_finished(self, timeout: float = 40.0) -> None:
        if not self.target_text:
            self.result.errors.append("target text kosong")
            return

        started = time.monotonic()

        for i in range(1, len(self.target_text) + 1):
            if time.monotonic() - started > timeout:
                self.result.errors.append("timeout typing")
                return

            await self.command("INPUT_UPDATE", {"typed_text": self.target_text[:i]})
            await asyncio.sleep(self.delay)

        # Poll sebentar agar PERSONAL_RESULT/GLOBAL_RESULT sempat diterima.
        poll_started = time.monotonic()
        while not self.finished and time.monotonic() - poll_started < 5:
            await self.command("RESTORE_SESSION")
            await asyncio.sleep(0.2)

        if not self.finished:
            self.result.errors.append("finished text sent but result not received")


async def run_pair(index: int, game_type: str, delay: float) -> list[BotResult]:
    started = time.monotonic()

    creator = TCPBot(f"bot-{index}-A", game_type, delay)
    joiner = TCPBot(f"bot-{index}-B", game_type, delay)

    await creator.command(
        "CREATE_ROOM",
        {
            "name": creator.name,
            "max_players": 2,
            "game_type": game_type,
        },
    )

    joiner.room_id = creator.room_id
    await joiner.command("JOIN_ROOM", {"name": joiner.name})

    # Room 2/2 akan auto masuk prepare, lalu running setelah countdown.
    await asyncio.gather(
        creator.wait_until_running(),
        joiner.wait_until_running(),
    )

    await asyncio.gather(
        creator.type_until_finished(),
        joiner.type_until_finished(),
    )

    duration = round(time.monotonic() - started, 3)
    creator.result.duration = duration
    joiner.result.duration = duration
    creator.result.room_id = creator.room_id
    joiner.result.room_id = joiner.room_id

    return [creator.result, joiner.result]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate Jempol Turbo TCP clients.")
    parser.add_argument("--pairs", type=int, default=3)
    parser.add_argument("--game-type", default="easy", choices=["easy", "medium", "hard"])
    parser.add_argument("--delay", type=float, default=0.015)
    args = parser.parse_args()

    started = time.monotonic()

    results_nested = await asyncio.gather(
        *(run_pair(i + 1, args.game_type, args.delay) for i in range(args.pairs))
    )

    results = [item for pair in results_nested for item in pair]
    finished_count = sum(1 for result in results if result.finished)
    error_count = sum(1 for result in results if result.errors)

    print("=== TCP Load Simulation ===")
    print(f"pairs={args.pairs}")
    print(f"bots={len(results)}")
    print(f"finished={finished_count}")
    print(f"errors={error_count}")
    print(f"duration={time.monotonic() - started:.2f}s")

    print("\n=== Detail ===")
    for result in results:
        error_text = "; ".join(result.errors) if result.errors else "-"
        print(
            f"{result.name} | "
            f"room={result.room_id} | "
            f"finished={result.finished} | "
            f"status={result.status} | "
            f"progress={round(result.progress * 100)}% | "
            f"wpm={result.wpm:.2f} | "
            f"cpm={result.cpm:.2f} | "
            f"typo={result.typo_count} | "
            f"errors={error_text}"
        )


if __name__ == "__main__":
    asyncio.run(main())