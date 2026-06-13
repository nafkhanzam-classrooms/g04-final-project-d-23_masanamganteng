"""Typing progress, WPM/CPM, accuracy, and ranking helpers."""

from __future__ import annotations

from app.game.models import Player, TypingStats


def count_correct_by_position(target_text: str, typed_text: str) -> int:
    return sum(1 for i, char in enumerate(typed_text[: len(target_text)]) if char == target_text[i])


def count_new_typos(target_text: str, previous_text: str, new_text: str) -> int:
    """Count new typo events from the latest input update.

    This is event-based, not final-state-based. If a player types a wrong
    character, deletes it, and fixes it, the final wrong_chars may become 0,
    but typo_count remains incremented as requested for accuracy-point tie break.
    """

    new_typos = 0
    limit = min(len(new_text), len(target_text))
    for index in range(limit):
        actual = new_text[index]
        expected = target_text[index]
        if actual == expected:
            continue
        previous = previous_text[index] if index < len(previous_text) else None
        if previous != actual:
            new_typos += 1
    if len(new_text) > len(target_text) and len(new_text) > len(previous_text):
        new_typos += len(new_text) - max(len(previous_text), len(target_text))
    return new_typos


def compute_stats(
    target_text: str,
    typed_text: str,
    elapsed_seconds: float,
    *,
    previous_text: str = "",
    previous_typo_count: int = 0,
) -> TypingStats:
    typed_text = typed_text[: len(target_text)]
    correct_chars = count_correct_by_position(target_text, typed_text)
    typed_chars = len(typed_text)
    wrong_chars = max(0, typed_chars - correct_chars)
    progress = correct_chars / max(len(target_text), 1)
    accuracy_percent = correct_chars / max(typed_chars, 1) * 100.0
    typo_count = previous_typo_count + count_new_typos(target_text, previous_text, typed_text)
    accuracy_point = max(0, 100 - typo_count)
    elapsed_minutes = max(elapsed_seconds, 0.1) / 60.0
    cpm = correct_chars / elapsed_minutes
    wpm = (correct_chars / 5.0) / elapsed_minutes
    return TypingStats(
        typed_chars=typed_chars,
        correct_chars=correct_chars,
        wrong_chars=wrong_chars,
        progress=round(progress, 4),
        accuracy_percent=round(accuracy_percent, 2),
        typo_count=typo_count,
        accuracy_point=accuracy_point,
        cpm=round(cpm, 2),
        wpm=round(wpm, 2),
    )


def is_exactly_finished(target_text: str, typed_text: str) -> bool:
    return typed_text == target_text


def ranking_key(player: Player) -> tuple:
    """Ranking rule: finished normal > timeout > leave.

    Finished players are ordered by finish duration, then WPM, CPM, and accuracy
    point. Timeout and leave players are ordered by progress and accuracy point.
    """

    if player.status == "finished":
        return (
            0,
            player.finish_duration if player.finish_duration is not None else 999999.0,
            -player.stats.wpm,
            -player.stats.cpm,
            -player.stats.accuracy_point,
            player.stats.typo_count,
        )
    if player.status == "timeout":
        return (
            1,
            -player.stats.progress,
            -player.stats.accuracy_point,
            player.stats.typo_count,
            player.finish_duration if player.finish_duration is not None else 999999.0,
        )
    return (
        2,
        -player.stats.progress,
        -player.stats.accuracy_point,
        player.stats.typo_count,
        player.disconnected_at or 999999.0,
    )


def build_rankings(players: list[Player]) -> list[dict]:
    sorted_players = sorted(players, key=ranking_key)
    rankings: list[dict] = []
    for rank, player in enumerate(sorted_players, start=1):
        data = player.to_public_dict()
        data["rank"] = rank
        rankings.append(data)
    return rankings
