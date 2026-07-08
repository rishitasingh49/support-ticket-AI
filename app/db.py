import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "support_tickets.csv"
DB_PATH = BASE_DIR / "data" / "tickets.db"
TABLE_NAME = "tickets"


def load_csv_to_db():
    df = pd.read_csv(CSV_PATH)

    df.columns = [c.strip() for c in df.columns]

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    numeric_cols = ["response_time_hrs", "resolution_time_hrs", "customer_rating"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    conn = sqlite3.connect(DB_PATH)
    df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.close()

    print(f"Loaded {len(df)} rows into {DB_PATH} (table: {TABLE_NAME})")


def get_connection():
    return sqlite3.connect(DB_PATH)


if __name__ == "__main__":
    load_csv_to_db()