"""Repository abstraction. Currently in-memory, easy to replace with DB later."""

from __future__ import annotations

from app.game.models import Room


class InMemoryRepository:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def save_room(self, room: Room) -> None:
        self.rooms[room.room_id] = room

    def get_room(self, room_id: str) -> Room | None:
        return self.rooms.get(room_id)

    def delete_room(self, room_id: str) -> None:
        self.rooms.pop(room_id, None)

    def list_rooms(self) -> list[Room]:
        return list(self.rooms.values())

    def list_available_rooms(self) -> list[Room]:
        return [room for room in self.rooms.values() if room.is_available()]
