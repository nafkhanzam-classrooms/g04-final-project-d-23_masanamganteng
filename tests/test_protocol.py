import pytest
from app.network.protocol import ProtocolError, decode_packet, encode_packet


def test_encode_decode_roundtrip():
    raw = encode_packet({"type": "JOIN_ROOM", "seq": 1, "room_id": "abc", "session_id": "s1", "payload": {"name": "A"}})
    packet = decode_packet(raw.strip())
    assert packet["type"] == "JOIN_ROOM"
    assert packet["payload"]["name"] == "A"


def test_invalid_json_rejected():
    with pytest.raises(ProtocolError):
        decode_packet(b'{"type":')


def test_unknown_type_rejected():
    with pytest.raises(ProtocolError):
        encode_packet({"type": "NOPE", "seq": 0, "payload": {}})
