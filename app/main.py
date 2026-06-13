"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config
from app.game.cleanup import run_cleanup_loop
from app.game.manager import GameManager
from app.network.tcp_adapter import TCPAdapter
from app.network.tcp_server import RawTCPServer
from app.network.websocket_hub import WebSocketHub
from app.web.routes import create_router

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/server.log", encoding="utf-8")],
)

manager = GameManager()
hub = WebSocketHub(manager)
tcp_server = RawTCPServer(manager)
tcp_adapter = TCPAdapter()
cleanup_task: asyncio.Task | None = None

app = FastAPI(title=config.APP_NAME)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(create_router(tcp_adapter, hub))


@app.on_event("startup")
async def startup() -> None:
    global cleanup_task
    await tcp_server.start()
    cleanup_task = asyncio.create_task(run_cleanup_loop(manager, hub.dispatch_events))
    logging.info("%s started", config.APP_NAME)


@app.on_event("shutdown")
async def shutdown() -> None:
    if cleanup_task:
        cleanup_task.cancel()
    await tcp_server.stop()
    logging.info("%s stopped", config.APP_NAME)
