from app import config
from app.game.text_generator import generate_text


def count_words(text: str) -> int:
    return len(text.replace('.', ' ').replace(',', ' ').split())


def test_easy_text_rule():
    text = generate_text("easy", seed=42)
    assert text == text.lower()
    assert "." not in text and "," not in text
    assert config.GAME_TYPES["easy"]["word_min"] <= count_words(text) <= config.GAME_TYPES["easy"]["word_max"]


def test_hard_text_rule():
    text = generate_text("hard", seed=42)
    assert config.GAME_TYPES["hard"]["word_min"] <= count_words(text) <= config.GAME_TYPES["hard"]["word_max"]
    assert any(ch in text for ch in ".,")
