"""HTTP and WebSocket routes."""

from __future__ import annotations

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app import config
from app.network.tcp_adapter import TCPAdapter
from app.network.websocket_hub import WebSocketHub


def create_router(adapter: TCPAdapter, hub: WebSocketHub) -> APIRouter:
    router = APIRouter()
    templates = Jinja2Templates(directory="app/web/templates")

    @router.get("/", response_class=HTMLResponse)
    async def landing(request: Request):
        return templates.TemplateResponse(
            "landing.html",
            {"request": request, "app_name": config.APP_NAME, "description": config.APP_DESCRIPTION},
        )

    @router.get("/home", response_class=HTMLResponse)
    async def home(request: Request):
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "app_name": config.APP_NAME},
        )

    @router.get("/create_room", response_class=HTMLResponse)
    async def create_room_page(request: Request):
        return templates.TemplateResponse(
            "create_room.html",
            {"request": request, "app_name": config.APP_NAME, "game_types": config.GAME_TYPES},
        )

    @router.get("/room/{room_id}", response_class=HTMLResponse)
    async def room_page(request: Request, room_id: str):
        return templates.TemplateResponse(
            "room.html",
            {
                "request": request,
                "app_name": config.APP_NAME,
                "room_id": room_id,
                "countdown": config.COUNTDOWN_SECONDS,
                "max_runtime": config.MAX_RUNTIME_SECONDS,
            },
        )

    @router.post("/api/rooms")
    async def create_room_api(request: Request):
        body = await request.json()
        events = await adapter.send_command(
            "CREATE_ROOM",
            session_id=str(body.get("session_id", "")),
            payload={
                "name": body.get("name", ""),
                "max_players": body.get("max_players", 2),
                "game_type": body.get("game_type", config.DEFAULT_GAME_TYPE),
            },
        )
        await hub.dispatch_events(events)
        error = next((event for event in events if event.get("type") == "ERROR"), None)
        if error:
            return JSONResponse(error.get("payload", {}), status_code=400)
        created = next((event for event in events if event.get("type") == "ROOM_CREATED"), None)
        room = created.get("payload", {}).get("room", {}) if created else {}
        return {"ok": True, "room": room}

    @router.websocket("/ws/home")
    async def home_ws(ws: WebSocket):
        await hub.connect_home(ws)
        try:
            while True:
                # Home socket only needs to stay alive. Client may send keepalive.
                await ws.receive_text()
        except WebSocketDisconnect:
            hub.disconnect_home(ws)

    @router.websocket("/ws/room/{room_id}")
    async def room_ws(ws: WebSocket, room_id: str):
        session_id = ws.query_params.get("session_id", "")
        await hub.connect_room(room_id, session_id, ws)
        try:
            while True:
                data = await ws.receive_json()
                command = str(data.get("type", ""))
                payload = data.get("payload") or {}
                if not isinstance(payload, dict):
                    payload = {}
                events = await adapter.send_command(
                    command,
                    room_id=room_id,
                    session_id=session_id,
                    payload=payload,
                )
                await hub.dispatch_events(events)
        except WebSocketDisconnect:
            events = await adapter.send_command("DISCONNECT", room_id=room_id, session_id=session_id, payload={})
            await hub.dispatch_events(events)
            hub.disconnect_room(room_id, session_id, ws)

    return router
