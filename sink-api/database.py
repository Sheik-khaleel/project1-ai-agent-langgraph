from __future__ import annotations

from collections.abc import Iterable

from schemas import Record


DATABASE: list[Record] = []


def all_records() -> list[Record]:
    """Return a copy of the stored records."""
    return list(DATABASE)


def extend_records(records: Iterable[Record]) -> None:
    """Append records to the database."""
    DATABASE.extend(records)


def count_records() -> int:
    return len(DATABASE)


def clear_records() -> None:
    DATABASE.clear()
