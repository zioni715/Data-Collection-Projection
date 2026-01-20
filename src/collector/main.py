from __future__ import annotations

import argparse
import json
import logging
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List

from .bus import EventBus
from .config import load_config
from .logging_ import setup_logging
from .privacy import PrivacyGuard, load_privacy_rules
from .priority import PriorityProcessor
from .store import SQLiteStore

logger = logging.getLogger(__name__)


class IngestServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, handler, bus: EventBus):
        super().__init__(server_address, handler)
        self.bus = bus


class IngestHandler(BaseHTTPRequestHandler):
    server_version = "CollectorHTTP/0.1"

    def do_GET(self) -> None:
        if self.path != "/health":
            self._send_json(404, {"error": "not found"})
            return
        self._send_json(200, {"status": "ok"})

    def do_POST(self) -> None:
        if self.path != "/events":
            self._send_json(404, {"error": "not found"})
            return
        content_length = self.headers.get("Content-Length")
        if not content_length:
            self._send_json(411, {"error": "missing content-length"})
            return
        try:
            body = self.rfile.read(int(content_length))
            payload = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid json"})
            return

        events = _normalize_payload(payload)
        if events is None:
            self._send_json(400, {"error": "payload must be object or list"})
            return

        for event in events:
            if not isinstance(event, dict):
                self._send_json(400, {"error": "event must be object"})
                return

        queued = 0
        for event in events:
            if not self.server.bus.enqueue(event):
                self._send_json(429, {"error": "queue full", "queued": queued})
                return
            queued += 1

        self._send_json(200, {"status": "queued", "count": queued})

    def log_message(self, format: str, *args: Any) -> None:
        logger.info("%s - %s", self.address_string(), format % args)

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _normalize_payload(payload: Any) -> List[Dict[str, Any]] | None:
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return payload
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Data Collector Core")
    parser.add_argument(
        "--config", default="configs/config.yaml", help="path to config file"
    )
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    config = load_config(args.config)
    setup_logging(config.log_level)

    logger.info("starting collector")

    store = SQLiteStore(config.db_path, wal_mode=config.wal_mode)
    store.connect()
    store.migrate(config.migrations_path)

    privacy_rules = load_privacy_rules(config.privacy_rules_path)
    privacy_guard = PrivacyGuard(privacy_rules, config.privacy.hash_salt)

    priority = PriorityProcessor(
        debounce_seconds=config.priority.debounce_seconds,
        focus_event_types=config.priority.focus_event_types,
        focus_block_event_type=config.priority.focus_block_event_type,
        drop_p2_when_queue_over=config.priority.drop_p2_when_queue_over,
    )

    bus = EventBus(
        store,
        privacy_guard,
        priority,
        validation_level=config.validation_level,
        queue_size=config.queue.max_size,
    )
    bus.start()

    server: IngestServer | None = None
    server_thread: threading.Thread | None = None

    if config.ingest.enabled:
        server = IngestServer(
            (config.ingest.host, config.ingest.port),
            IngestHandler,
            bus,
        )
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info(
            "ingest listening on http://%s:%s",
            config.ingest.host,
            config.ingest.port,
        )
    else:
        logger.info("ingest disabled")

    stop_event = threading.Event()

    def _handle_signal(signum, frame):
        logger.info("shutdown requested")
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        while not stop_event.is_set():
            time.sleep(0.25)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if server_thread is not None:
            server_thread.join(timeout=5)
        bus.stop()
        store.close()
        logger.info("collector stopped")


if __name__ == "__main__":
    run()
