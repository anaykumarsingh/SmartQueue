import sqlite3
from pathlib import Path

database = Path(__file__).resolve().parents[2] / "smartqueue.db"
connection = sqlite3.connect(database)

try:
    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(queue_tokens)"
        ).fetchall()
    }

    additions = {
        "qr_token_hash": "VARCHAR(64)",
        "expires_at": "DATETIME",
        "claimed_at": "DATETIME",
    }

    for column, data_type in additions.items():
        if column not in columns:
            connection.execute(
                f"ALTER TABLE queue_tokens ADD COLUMN {column} {data_type}"
            )
            print(f"Added column: {column}")
        else:
            print(f"Already exists: {column}")

    connection.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        ix_queue_tokens_qr_token_hash
        ON queue_tokens (qr_token_hash)
    """)

    connection.commit()
    print("\nQR database migration completed successfully.")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
