from app.game.scoring import compute_stats, is_exactly_finished


def test_progress_position_based():
    stats = compute_stats("kamis", "kumis", 10.0)
    assert stats.correct_chars == 4
    assert stats.progress == 0.8


def test_zero_progress_when_all_positions_wrong():
    stats = compute_stats("senin", "gajah", 10.0)
    assert stats.correct_chars == 0
    assert stats.progress == 0.0


def test_accuracy_point_from_typo_count():
    stats = compute_stats("abc", "axc", 10.0)
    assert stats.typo_count == 1
    assert stats.accuracy_point == 99


def test_finished_requires_exact_text_case_sensitive():
    assert is_exactly_finished("Halo", "Halo")
    assert not is_exactly_finished("Halo", "halo")
