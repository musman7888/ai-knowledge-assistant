-- ============================================================
-- PostgreSQL schema for the Text-to-SQL module (retail analytics).
-- Two tables: products (what we sell) and sales (transactions).
-- Run by db/import.py before loading the CSV data.
-- ============================================================

-- Drop first so re-running import is clean/idempotent.
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id          INTEGER PRIMARY KEY,
    name        TEXT        NOT NULL,
    category    TEXT        NOT NULL,
    price       NUMERIC(10, 2) NOT NULL,
    stock       INTEGER     NOT NULL,   -- units currently in stock (0 = out of stock)
    branch      TEXT        NOT NULL    -- store branch holding this stock
);

CREATE TABLE sales (
    id          INTEGER PRIMARY KEY,
    product_id  INTEGER     NOT NULL REFERENCES products(id),
    quantity    INTEGER     NOT NULL,
    amount      NUMERIC(10, 2) NOT NULL,  -- total sale amount for this transaction
    sale_date   DATE        NOT NULL
);
