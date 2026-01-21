from __future__ import annotations

import json
import threading
import time
from collections import Counter
from typing import Any, Dict, Optional


class Observability:
    def __init__(self, log_interval_sec: int = 60) -> None:
        self._lock = threading.Lock()
        self._counters: Counter[str] = Counter()
        self._gauges: Dict[str, float] = {}
        self._minute_bucket = int(time.time() // 60)
        self._minute_counters: Counter[str] = Counter()
        self._last_log = time.time()
        self._log_interval_sec = max(10, int(log_interval_sec))
        self._last_event_ts: Optional[str] = None

    def inc(self, name: str, count: int = 1, track_minute: bool = True) -> None:
        if not name:
            return
        with self._lock:
            self._counters[name] += count
            self._tick_minute()
            if track_minute:
                self._minute_counters[name] += count

    def set_gauge(self, name: str, value: float) -> None:
        if not name:
            return
        with self._lock:
            self._gauges[name] = value

    def set_last_event_ts(self, ts: Optional[str]) -> None:
        if not ts:
            return
        with self._lock:
            self._last_event_ts = ts

    def record_drop(self, reason: str) -> None:
        self.inc("pipeline.dropped_total")
        if reason:
            self.inc(f"drop.reason.{reason}")

    def record_priority(self, priority: str) -> None:
        if not priority:
            return
        key = priority.strip().upper()
        if key in {"P0", "P1", "P2"}:
            self.inc(f"priority.{key.lower()}_total")

    def record_privacy_denied(self) -> None:
        self.inc("privacy.denied_total")
        self.record_drop("denylist")

    def record_privacy_redacted(self) -> None:
        self.inc("privacy.redacted_total")

    def record_ingest_received(self) -> None:
        self.inc("ingest.received_total")

    def record_ingest_ok(self) -> None:
        self.inc("ingest.ok_total")

    def record_ingest_invalid(self) -> None:
        self.inc("ingest.invalid_total")
        self.record_drop("schema")

    def record_store_insert_ok(self) -> None:
        self.inc("store.insert_ok_total")

    def record_store_insert_fail(self) -> None:
        self.inc("store.insert_fail_total")
        self.record_drop("store_fail")

    def snapshot(self, db_size_bytes: int) -> Dict[str, Any]:
        with self._lock:
            self._tick_minute()
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "minute": self._minute_bucket,
                "minute_counters": dict(self._minute_counters),
                "db_size_bytes": db_size_bytes,
                "last_event_ts": self._last_event_ts,
            }

    def maybe_log(self, logger, db_size_bytes: int) -> None:
        now = time.time()
        if now - self._last_log < self._log_interval_sec:
            return
        self._last_log = now
        payload = self.snapshot(db_size_bytes=db_size_bytes)
        payload["event"] = "metrics_minute"
        logger.info(json.dumps(payload, separators=(",", ":")))

    def _tick_minute(self) -> None:
        now_bucket = int(time.time() // 60)
        if now_bucket != self._minute_bucket:
            self._minute_bucket = now_bucket
            self._minute_counters = Counter()
