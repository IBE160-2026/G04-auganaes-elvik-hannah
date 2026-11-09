"""Story 2.1 (FR-4, FR-8, AD-6): the TaskType catalog's invariants (decisions 2, 3 and 6)."""

import ast
from pathlib import Path

from app.domain import task_types
from app.domain.task_types import (
    CATALOG_VERSION,
    CLASSIFICATIONS,
    FREQUENCY_DAYS,
    TASK_NAME_MAX_LENGTH,
    TASK_TYPE_KEY_MAX_LENGTH,
    TASK_TYPES,
)

APP = Path(__file__).resolve().parents[1] / "app"


def test_catalog_has_at_least_eight_entries_with_unique_keys() -> None:
    assert len(TASK_TYPES) >= 8
    keys = [t.key for t in TASK_TYPES]
    assert len(set(keys)) == len(keys)
    assert isinstance(CATALOG_VERSION, int) and CATALOG_VERSION >= 1


def test_catalog_covers_both_classifications_and_two_photo_eligible() -> None:
    assert {t.classification for t in TASK_TYPES} == set(CLASSIFICATIONS) == {"must", "should"}
    assert sum(t.photo_evidence_eligible for t in TASK_TYPES) >= 2


def test_every_recommended_frequency_is_one_of_the_fixed_intervals() -> None:
    assert FREQUENCY_DAYS == (7, 14, 30, 42, 60, 90, 182, 365)
    assert all(t.frequency_days in FREQUENCY_DAYS for t in TASK_TYPES)


def test_keys_and_names_fit_the_columns() -> None:
    for t in TASK_TYPES:
        assert 1 <= len(t.key) <= TASK_TYPE_KEY_MAX_LENGTH
        assert 1 <= len(t.name) <= TASK_NAME_MAX_LENGTH


def test_the_agreed_starter_entries() -> None:
    # Decision 3 (Eirik, 2026-11-09).
    assert [
        (t.key, t.classification, t.frequency_days, t.photo_evidence_eligible) for t in TASK_TYPES
    ] == [
        ("vask-badet", "must", 42, False),
        ("rens-sluket", "must", 30, True),
        ("kjokkenviftefilter", "must", 60, True),
        ("avkalk-vannkoker", "should", 60, False),
        ("bak-kjoleskapet", "should", 90, False),
        ("stekeovn", "should", 90, False),
        ("gulv", "should", 14, False),
        ("dusjfuger", "should", 90, False),
    ]


def test_lookup_by_key() -> None:
    entry = task_types.task_type("stekeovn")
    assert entry is not None and entry.name == "Vask stekeovnen"
    assert task_types.task_type("finnes-ikke") is None


def test_no_route_or_seed_module_names_a_catalog_key() -> None:
    """AD-6: recommendations come only from the catalog, never hardcoded in a route."""
    keys = {t.key for t in TASK_TYPES}
    for path in [*(APP / "routes").glob("*.py"), *(APP / "seed").glob("*.py")]:
        strings = {
            node.value
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert not strings & keys, path.name
