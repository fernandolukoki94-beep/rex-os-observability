"""Transactional SQLite queue for the REX Edge Agent.

The adapter stores each edge sample as one JSON payload. SQLite is part of the
Python standard library, so the edge runtime keeps a zero-cost dependency
surface while gaining durable transactions, locking and crash-safe commits.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class SQLiteQueue:
    """Small FIFO queue backed by a local SQLite database."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            self.path,
            timeout=5.0,
            isolation_level=None,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS edge_queue (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def append(self, record: dict[str, Any]) -> None:
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._connection.execute(
                    "INSERT INTO edge_queue (payload) VALUES (?)", (payload,)
                )
                self._connection.execute("COMMIT")
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

    def peek(self) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT payload FROM edge_queue ORDER BY sequence ASC LIMIT 1"
            ).fetchone()
            return json.loads(row["payload"]) if row else None

    def pop_if_matches(self, expected: dict[str, Any]) -> dict[str, Any] | None:
        """Remove the FIFO head only when it matches the delivered record.

        Identity and integrity hash protect the ACK -> removal boundary. Older
        records without those fields remain compatible through full-payload
        comparison.
        """
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    "SELECT sequence, payload FROM edge_queue ORDER BY sequence ASC LIMIT 1"
                ).fetchone()
                if row is None:
                    self._connection.execute("COMMIT")
                    return None
                current = json.loads(row["payload"])
                same_identity = (
                    expected.get("event_id")
                    and current.get("event_id") == expected.get("event_id")
                    and (
                        not expected.get("integrity_hash")
                        or current.get("integrity_hash") == expected.get("integrity_hash")
                    )
                )
                legacy_match = not expected.get("event_id") and current == expected
                if not (same_identity or legacy_match):
                    self._connection.execute("COMMIT")
                    return None
                self._connection.execute(
                    "DELETE FROM edge_queue WHERE sequence = ?", (row["sequence"],)
                )
                self._connection.execute("COMMIT")
                return current
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

    def pop(self) -> dict[str, Any] | None:
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    "SELECT sequence, payload FROM edge_queue ORDER BY sequence ASC LIMIT 1"
                ).fetchone()
                if row is None:
                    self._connection.execute("COMMIT")
                    return None
                self._connection.execute(
                    "DELETE FROM edge_queue WHERE sequence = ?", (row["sequence"],)
                )
                self._connection.execute("COMMIT")
                return json.loads(row["payload"])
            except Exception:
                self._connection.execute("ROLLBACK")
                raise

    def all(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT payload FROM edge_queue ORDER BY sequence ASC"
            ).fetchall()
            return [json.loads(row["payload"]) for row in rows]

    def depth(self) -> int:
        with self._lock:
            row = self._connection.execute("SELECT COUNT(*) AS count FROM edge_queue").fetchone()
            return int(row["count"])

    def integrity_check(self) -> bool:
        with self._lock:
            row = self._connection.execute("PRAGMA integrity_check").fetchone()
            return bool(row and row[0] == "ok")

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteQueue":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()
