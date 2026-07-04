# ============================================================
# SQL SAFETY (pure — no external dependencies)
# The guardrails around LLM-generated SQL: extract a clean statement and
# verify it's a single read-only SELECT. Dependency-free for easy testing.
# ============================================================

import re


def clean_sql(raw: str) -> str:
    """Strip markdown code fences / stray prose so only the SQL remains."""
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    sql = fenced.group(1) if fenced else raw
    return sql.strip().rstrip(";").strip()


def is_read_only(sql: str) -> bool:
    """
    Allow only a single SELECT statement.
    Blocks writes (INSERT/UPDATE/DELETE), DDL (DROP/ALTER), and stacked
    statements (anything after a ';').
    """
    cleaned = sql.strip().rstrip(";").strip()
    if ";" in cleaned:                       # no stacked statements
        return False
    return cleaned.lower().startswith("select")
