# ============================================================
# SQL SERVICE — connection + safe query execution (Phase 4a)
# Connects to PostgreSQL (Neon) and runs READ-ONLY queries.
# The Text-to-SQL generation (LLM -> SQL) is added in Phase 4b; this layer
# is the safety wall: even a bad generated query can only ever SELECT.
# ============================================================

from sqlalchemy import create_engine, text

from app.config import settings

# One shared engine (connection pool). pool_pre_ping checks a connection is
# alive before using it — important for Neon, which suspends when idle.
_engine = create_engine(settings.database_url, pool_pre_ping=True)


class UnsafeQueryError(Exception):
    """Raised when a query is not a read-only SELECT."""


def _is_read_only(sql: str) -> bool:
    """
    Allow only a single SELECT statement.
    Blocks writes (INSERT/UPDATE/DELETE), DDL (DROP/ALTER), and stacked
    statements (a second statement after a ';').
    """
    cleaned = sql.strip().rstrip(";").strip()
    if ";" in cleaned:                       # no stacked statements
        return False
    return cleaned.lower().startswith("select")


def run_query(sql: str) -> list[dict]:
    """
    Execute a read-only SELECT and return rows as a list of dicts.
    Raises UnsafeQueryError if the SQL is anything other than a SELECT.
    """
    if not _is_read_only(sql):
        raise UnsafeQueryError("Only single read-only SELECT queries are allowed.")

    with _engine.connect() as conn:
        result = conn.execute(text(sql))
        # row._mapping gives a dict-like {column: value} view.
        return [dict(row._mapping) for row in result]


def get_schema() -> str:
    """
    Return a compact text description of the tables and columns, used later
    (Phase 4b) to tell the LLM what it can query.
    """
    query = text(
        "SELECT table_name, column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema = 'public' "
        "ORDER BY table_name, ordinal_position"
    )
    lines: dict[str, list[str]] = {}
    with _engine.connect() as conn:
        for table, column, dtype in conn.execute(query):
            lines.setdefault(table, []).append(f"{column} ({dtype})")
    return "\n".join(f"{t}: {', '.join(cols)}" for t, cols in lines.items())
