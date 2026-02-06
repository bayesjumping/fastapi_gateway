"""Tests for database helpers."""
from app.db.database import get_next_id, reset_next_id


def test_get_next_id_increments():
    reset_next_id(1)
    assert get_next_id() == 1
    assert get_next_id() == 2


def test_reset_next_id_sets_value():
    reset_next_id(10)
    assert get_next_id() == 10