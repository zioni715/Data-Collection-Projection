from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from .models import EventEnvelope


class SQLiteStore:
    def __init__(self, db_path: Path, wal_mode: bool = True) -> None:
        self.db_path = Path(db_path)
        self.wal_mode = wal_mode
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()

    def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        if self.wal_mode:
            self._conn.execute("PRAGMA journal_mode = WAL;")

    def migrate(self, migrations_path: Path) -> None:
        if self._conn is None:
            raise RuntimeError("database is not connected")
        migrations_path = Path(migrations_path)
        sql_path = migrations_path / "001_init.sql"
        sql = sql_path.read_text()
        with self._lock:
            self._conn.executescript(sql)
            self._conn.commit()

    def insert_event(self, envelope: EventEnvelope) -> None:
        if self._conn is None:
            raise RuntimeError("database is not connected")
        payload_json = json.dumps(envelope.payload, separators=(",", ":"))
        privacy_json = json.dumps(envelope.privacy.__dict__, separators=(",", ":"))
        raw_json = json.dumps(envelope.raw or {}, separators=(",", ":"))
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO events (
                    schema_version,
                    event_id,
                    ts,
                    source,
                    app,
                    event_type,
                    priority,
                    resource_type,
                    resource_id,
                    payload_json,
                    privacy_json,
                    pid,
                    window_id,
                    raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    envelope.schema_version,
                    envelope.event_id,
                    envelope.ts,
                    envelope.source,
                    envelope.app,
                    envelope.event_type,
                    envelope.priority,
                    envelope.resource.type,
                    envelope.resource.id,
                    payload_json,
                    privacy_json,
                    envelope.pid,
                    envelope.window_id,
                    raw_json,
                ),
            )
            self._conn.commit()

    def close(self) -> None:
        if self._conn is None:
            return
        with self._lock:
            self._conn.close()
        self._conn = None
