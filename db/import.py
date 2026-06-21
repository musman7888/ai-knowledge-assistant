# ============================================================
# CSV IMPORT (Approach A) — load sample data into PostgreSQL/Neon
# Run once:  python db/import.py
#
# Uses client-side COPY (psycopg2 copy_expert), which streams the local
# CSV file over the connection. This works on managed databases like Neon,
# unlike server-side `COPY FROM '/path'` which needs server filesystem access.
# ============================================================

from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]   # project root
DB_DIR = ROOT / "db"
DATA_DIR = ROOT / "data"


def load_database_url() -> str:
    """Read DATABASE_URL from backend/.env (no extra dependency needed)."""
    env_path = ROOT / "backend" / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("DATABASE_URL not found in backend/.env")


def main() -> None:
    db_url = load_database_url()

    # Connect to Neon. The URL carries sslmode/channel_binding, so SSL is on.
    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()

        # 1) Create the tables (drops + recreates — safe to re-run).
        print("Creating tables from schema.sql ...")
        cur.execute((DB_DIR / "schema.sql").read_text(encoding="utf-8"))

        # 2) Load each CSV with client-side COPY (Neon-safe).
        for table, csv_name in [("products", "products.csv"), ("sales", "sales.csv")]:
            csv_path = DATA_DIR / csv_name
            print(f"Importing {csv_name} -> {table} ...")
            with open(csv_path, "r", encoding="utf-8") as f:
                cur.copy_expert(
                    f"COPY {table} FROM STDIN WITH CSV HEADER",
                    f,
                )

        conn.commit()

        # 3) Report row counts so we can see it worked.
        for table in ("products", "sales"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]} rows")

        print("Import complete.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
