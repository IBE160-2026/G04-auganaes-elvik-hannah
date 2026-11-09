"""The TaskType catalog (Story 2.1, FR-4, FR-8, AD-6; decisions 2, 3 and 6, 2026-11-09).

A versioned Python module, not a table: the recommended tasks change with the code and are
reviewed in PRs. A Task stores its catalog key and copies the name, so a later catalog version
never rewrites existing Tasks. Recommendations come only from here, never from a component or a
route. `photo_evidence_eligible` is read by Epic 4 and is not editable by anyone.
"""

from typing import Literal, NamedTuple, get_args

# Bump when an entry is added, removed or its recommendation changes.
CATALOG_VERSION = 1

Classification = Literal["must", "should"]
CLASSIFICATIONS: tuple[Classification, ...] = get_args(Classification)

# Decision 6: Frequencies are picked from fixed intervals, in days («Hver uke» … «Hvert år»).
Frequency = Literal[7, 14, 30, 42, 60, 90, 182, 365]
FREQUENCY_DAYS: tuple[Frequency, ...] = get_args(Frequency)


class TaskType(NamedTuple):
    key: str
    name: str
    classification: Classification
    frequency_days: Frequency
    photo_evidence_eligible: bool = False


# Decision 3: the eight starter entries. Mold or damage risk defaults to Must.
TASK_TYPES: tuple[TaskType, ...] = (
    TaskType("vask-badet", "Vask badet grundig", "must", 42),
    TaskType("rens-sluket", "Rens sluket", "must", 30, photo_evidence_eligible=True),
    TaskType(
        "kjokkenviftefilter",
        "Rens filteret i kjøkkenviften",
        "must",
        60,
        photo_evidence_eligible=True,
    ),
    TaskType("avkalk-vannkoker", "Avkalk vannkokeren", "should", 60),
    TaskType("bak-kjoleskapet", "Vask bak og under kjøleskapet", "should", 90),
    TaskType("stekeovn", "Vask stekeovnen", "should", 90),
    TaskType("gulv", "Støvsug og vask gulvene", "should", 14),
    TaskType("dusjfuger", "Vask fugene i dusjen", "should", 90),
)

_BY_KEY: dict[str, TaskType] = {t.key: t for t in TASK_TYPES}

# The longest key and name, for the column lengths in models/task.py.
TASK_TYPE_KEY_MAX_LENGTH = 50
TASK_NAME_MAX_LENGTH = 100


def task_type(key: str) -> TaskType | None:
    """The catalog entry with this key, or None."""
    return _BY_KEY.get(key)
