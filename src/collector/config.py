from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class IngestConfig:
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8080


@dataclass
class QueueConfig:
    max_size: int = 1000


@dataclass
class PrivacyConfig:
    hash_salt: str = "dev-salt"


@dataclass
class PriorityConfig:
    debounce_seconds: float = 2.0
    focus_event_types: list[str] = field(default_factory=lambda: ["os.foreground_changed"])
    focus_block_event_type: str = "os.app_focus_block"
    drop_p2_when_queue_over: float = 0.8


@dataclass
class Config:
    db_path: Path
    migrations_path: Path
    validation_level: str = "lenient"
    wal_mode: bool = True
    log_level: str = "INFO"
    privacy_rules_path: Path = PROJECT_ROOT / "configs" / "privacy_rules.yaml"
    ingest: IngestConfig = field(default_factory=IngestConfig)
    queue: QueueConfig = field(default_factory=QueueConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    priority: PriorityConfig = field(default_factory=PriorityConfig)


def load_config(path: str | Path) -> Config:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError("config root must be a mapping")

    db_path = _resolve_path(raw.get("db_path", "collector.db"))
    migrations_path = _resolve_path(raw.get("migrations_path", "migrations"))
    privacy_rules_path = _resolve_path(
        raw.get("privacy_rules_path", "configs/privacy_rules.yaml")
    )

    ingest_raw = _as_dict(raw.get("ingest"))
    ingest = IngestConfig(
        enabled=bool(ingest_raw.get("enabled", True)),
        host=str(ingest_raw.get("host", "127.0.0.1")),
        port=int(ingest_raw.get("port", 8080)),
    )

    queue_raw = _as_dict(raw.get("queue"))
    queue = QueueConfig(max_size=int(queue_raw.get("max_size", 1000)))

    privacy_raw = _as_dict(raw.get("privacy"))
    privacy = PrivacyConfig(hash_salt=str(privacy_raw.get("hash_salt", "dev-salt")))

    priority_raw = _as_dict(raw.get("priority"))
    focus_event_types = priority_raw.get("focus_event_types", ["os.foreground_changed"])
    if not isinstance(focus_event_types, list):
        focus_event_types = [str(focus_event_types)]
    priority = PriorityConfig(
        debounce_seconds=float(priority_raw.get("debounce_seconds", 2.0)),
        focus_event_types=[str(item) for item in focus_event_types],
        focus_block_event_type=str(
            priority_raw.get("focus_block_event_type", "os.app_focus_block")
        ),
        drop_p2_when_queue_over=float(
            priority_raw.get("drop_p2_when_queue_over", 0.8)
        ),
    )

    return Config(
        db_path=db_path,
        migrations_path=migrations_path,
        validation_level=str(raw.get("validation_level", "lenient")),
        wal_mode=bool(raw.get("wal_mode", True)),
        log_level=str(raw.get("log_level", "INFO")),
        privacy_rules_path=privacy_rules_path,
        ingest=ingest,
        queue=queue,
        privacy=privacy,
        priority=priority,
    )


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
