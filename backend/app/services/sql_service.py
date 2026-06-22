# ============================================================
# SQL SERVICE — connection + safe query execution (Phase 4a)
# Connects to PostgreSQL (Neon) and runs READ-ONLY queries.
# The Text-to-SQL generation (LLM -> SQL) is added in Phase 4b; this layer
# is the safety wall: even a bad generated query can only ever SELECT.
# ============================================================

import re
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.prompts.system import SQL_ANSWER_PROMPT, SQL_GEN_PROMPT
from app.services.llm_service import complete

# One shared engine (connection pool). pool_pre_ping checks a connection is
# alive before using it — important for Neon, which suspends when idle.
_engine = create_engine(settings.database_url, pool_pre_ping=True)


def _connect(retries: int = 3, delay: float = 2.0):
    """
    Open a DB connection, retrying on OperationalError. Neon scales to zero
    when idle; the first connection after a suspend can fail while the
    database is waking up, so we retry instead of erroring out.
    """
    for attempt in range(retries):
        try:
            return _engine.connect()
        except OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)  # give Neon a moment to wake


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

    with _connect() as conn:
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
    with _connect() as conn:
        for table, column, dtype in conn.execute(query):
            lines.setdefault(table, []).append(f"{column} ({dtype})")
    return "\n".join(f"{t}: {', '.join(cols)}" for t, cols in lines.items())


# ============================================================
# Text-to-SQL (Phase 4b): question -> SQL -> rows -> answer
# ============================================================

def _clean_sql(raw: str) -> str:
    """Strip markdown fences / stray prose so we're left with just the SQL."""
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    sql = fenced.group(1) if fenced else raw
    return sql.strip().rstrip(";").strip()


def answer(question: str) -> dict | None:
    """
    Answer a question from the database.

    Flow: schema -> LLM writes SQL -> safe run_query -> LLM phrases the rows.
    Returns {answer, source, sql, row_count}. On any failure (bad SQL,
    blocked query, DB error) returns a safe fallback dict instead of crashing.
    """
    schema = get_schema()

    # 1) Ask the LLM to translate the question into SQL.
    gen_prompt = f"Database schema:\n{schema}\n\nQuestion: {question}"
    sql = _clean_sql(complete(gen_prompt, system=SQL_GEN_PROMPT))

    # 2) Execute it through the read-only guard.
    try:
        rows = run_query(sql)
    except Exception as error:
        print(f"[sql_service] query failed: {type(error).__name__}: {error}")
        return {
            "answer": "I couldn't answer that from the database.",
            "source": "database",
            "sql": sql,
            "row_count": 0,
        }

    # 3) Turn the rows into a natural-language answer.
    answer_prompt = (
        f"Question: {question}\n"
        f"SQL results: {rows}\n"
        "Write a short, clear answer."
    )
    phrased = complete(answer_prompt, system=SQL_ANSWER_PROMPT)

    return {
        "answer": phrased.strip(),
        "source": "database",
        "sql": sql,
        "row_count": len(rows),
    }
