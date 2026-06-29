from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [row_to_dict(row) for row in rows if row is not None]


class MySQLCursorResult:
    def __init__(self, cursor: Any):
        self.cursor = cursor

    def fetchone(self) -> dict | None:
        return self.cursor.fetchone()

    def fetchall(self) -> list[dict]:
        return list(self.cursor.fetchall())


class MySQLConnection:
    def __init__(self, conn: Any):
        self.conn = conn

    def execute(self, sql: str, params: tuple | list | None = None) -> MySQLCursorResult:
        cursor = self.conn.cursor()
        # Repositories use SQLite-style placeholders so the local and MySQL
        # implementations can share most SQL call sites during the MVP phase.
        cursor.execute(self._translate(sql), params or ())
        return MySQLCursorResult(cursor)

    def _translate(self, sql: str) -> str:
        return sql.replace("?", "%s")


class MySQLDatabase:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    @contextmanager
    def connect(self) -> Iterator[MySQLConnection]:
        # Import lazily so local SQLite development does not require MySQL
        # client libraries until DATABASE_BACKEND=mysql is actually selected.
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError as exc:
            raise RuntimeError("PyMySQL is required when DATABASE_BACKEND=mysql") from exc

        conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            autocommit=False,
            cursorclass=DictCursor,
        )
        try:
            yield MySQLConnection(conn)
            conn.commit()
        finally:
            conn.close()
