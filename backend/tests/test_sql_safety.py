# Unit tests for the SQL guardrails (app/utils/sql_safety.py).
# These protect against LLM-generated queries doing anything but a read.

import pytest

from app.utils.sql_safety import clean_sql, is_read_only


# --- is_read_only ---------------------------------------------------------

@pytest.mark.parametrize("sql", [
    "SELECT * FROM products",
    "select name from products where stock = 0",
    "  SELECT 1  ",
    "SELECT COUNT(*) FROM sales;",          # trailing semicolon is fine
])
def test_allows_single_select(sql):
    assert is_read_only(sql) is True


@pytest.mark.parametrize("sql", [
    "INSERT INTO products VALUES (1)",
    "UPDATE products SET price = 0",
    "DELETE FROM sales",
    "DROP TABLE products",
    "ALTER TABLE products ADD COLUMN x int",
    "SELECT 1; DROP TABLE products",        # stacked statement
    "SELECT 1; SELECT 2",                   # stacked, even if both SELECT
    "",
])
def test_blocks_non_select_and_stacked(sql):
    assert is_read_only(sql) is False


# --- clean_sql ------------------------------------------------------------

def test_strips_sql_code_fence():
    raw = "```sql\nSELECT * FROM products\n```"
    assert clean_sql(raw) == "SELECT * FROM products"


def test_strips_plain_code_fence():
    raw = "```\nSELECT 1\n```"
    assert clean_sql(raw) == "SELECT 1"


def test_passthrough_and_trailing_semicolon():
    assert clean_sql("  SELECT 1;  ") == "SELECT 1"


def test_cleaned_query_passes_guard():
    # end-to-end: a fenced LLM reply → clean → still a valid read-only query
    assert is_read_only(clean_sql("```sql\nSELECT 1\n```")) is True
