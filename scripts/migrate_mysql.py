#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os

import pymysql


def main() -> None:
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "locusthub")
    password = os.getenv("MYSQL_PASSWORD", "locusthub")
    database = os.getenv("MYSQL_DATABASE", "locusthub")
    schema_path = Path(__file__).resolve().parents[1] / "backend" / "app" / "db" / "mysql_schema.sql"

    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database, charset="utf8mb4")
    try:
        with conn.cursor() as cursor:
            for statement in schema_path.read_text(encoding="utf-8").split(";"):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
        conn.commit()
    finally:
        conn.close()
    print(f"Applied MySQL schema to {host}:{port}/{database}")


if __name__ == "__main__":
    main()
