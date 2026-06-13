"""Cleanup loop helper for rooms and disconnected sessions."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable

from app import config
from app.game.manager import GameManager


async def run_cleanup_loop(
    manager: GameManager,
    dispatch_events: Callable[[list[dict]], Awaitable[None]],
) -> None:
    while True:
        with contextlib.suppress(Exception):
            events = await manager.tick()
            if events:
                await dispatch_events(events)
        await asyncio.sleep(config.CLEANUP_INTERVAL_SECONDS)
