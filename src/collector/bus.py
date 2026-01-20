from __future__ import annotations

import logging
import queue
import threading
from typing import Any, Dict

from .normalize import NormalizationError, normalize_event
from .privacy import PrivacyGuard
from .priority import PriorityProcessor
from .store import SQLiteStore

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(
        self,
        store: SQLiteStore,
        privacy_guard: PrivacyGuard,
        priority: PriorityProcessor,
        validation_level: str = "lenient",
        queue_size: int = 1000,
    ) -> None:
        self._store = store
        self._privacy_guard = privacy_guard
        self._priority = priority
        self._validation_level = validation_level
        self._queue: queue.Queue[Dict[str, Any]] = queue.Queue(maxsize=queue_size)
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._worker.join(timeout=5)
        for output in self._priority.flush():
            try:
                self._store.insert_event(output)
            except Exception:
                logger.exception("failed to flush focus block")

    def enqueue(self, event: Dict[str, Any]) -> bool:
        try:
            self._queue.put_nowait(event)
            return True
        except queue.Full:
            return False

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                envelope = normalize_event(item, validation_level=self._validation_level)
                envelope = self._privacy_guard.apply(envelope)
                if envelope is None:
                    continue
                queue_ratio = _queue_ratio(self._queue)
                for output in self._priority.process(envelope, queue_ratio):
                    self._store.insert_event(output)
            except NormalizationError as exc:
                logger.warning("drop event: %s", exc)
            except Exception:
                logger.exception("failed to process event")


def _queue_ratio(q: queue.Queue) -> float:
    maxsize = q.maxsize
    if maxsize <= 0:
        return 0.0
    return q.qsize() / maxsize
