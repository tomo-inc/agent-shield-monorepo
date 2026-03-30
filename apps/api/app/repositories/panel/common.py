from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Insert


def utc_now() -> datetime:
    return datetime.now(UTC)


def build_upsert(
    session: Session,
    table: Table,
    values: dict[str, Any],
    index_elements: Sequence[str],
    update_columns: Sequence[str],
) -> Insert:
    dialect_name = session.bind.dialect.name if session.bind is not None else ""
    if dialect_name == "postgresql":
        statement = pg_insert(table).values(**values)
    elif dialect_name == "sqlite":
        statement = sqlite_insert(table).values(**values)
    else:
        raise RuntimeError(f"unsupported SQL dialect for upsert: {dialect_name}")
    return statement.on_conflict_do_update(
        index_elements=list(index_elements),
        set_={column: getattr(statement.excluded, column) for column in update_columns},
    )
