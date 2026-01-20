from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

import yaml

from .models import EventEnvelope, PrivacyMetadata, ResourceRef
from .utils.hashing import hmac_sha256
from .utils.masking import mask_patterns, sanitize_url, truncate


@dataclass
class PrivacyRules:
    mask_keys: Set[str] = field(default_factory=set)
    hash_keys: Set[str] = field(default_factory=set)
    length_limits: Dict[str, int] = field(default_factory=dict)
    url_policy: Dict[str, Any] = field(default_factory=dict)
    redaction_patterns: List[re.Pattern[str]] = field(default_factory=list)
    drop_payload_keys: Set[str] = field(default_factory=set)
    allowlist_apps: Set[str] = field(default_factory=set)
    denylist_apps: Set[str] = field(default_factory=set)
    denylist_action: str = "drop"


class PrivacyGuard:
    def __init__(self, rules: PrivacyRules, hash_salt: str) -> None:
        self._rules = rules
        self._hash_salt = hash_salt

    def apply(self, envelope: EventEnvelope) -> Optional[EventEnvelope]:
        app_key = (envelope.app or "").lower()
        if self._rules.allowlist_apps and app_key not in self._rules.allowlist_apps:
            return None
        if self._rules.denylist_apps and app_key in self._rules.denylist_apps:
            if self._rules.denylist_action == "strip":
                envelope.payload = {}
                envelope.privacy.redaction = _dedupe(
                    envelope.privacy.redaction + ["denylist_stripped"]
                )
                return envelope
            return None

        redactions = list(envelope.privacy.redaction)

        if envelope.window_id:
            envelope.window_id = _hash_value(str(envelope.window_id), self._hash_salt)
            redactions.append("window_id_hashed")

        if envelope.resource and envelope.resource.id and envelope.resource.id != "unknown":
            envelope.resource = ResourceRef(
                type=envelope.resource.type,
                id=_hash_value(str(envelope.resource.id), self._hash_salt),
            )
            redactions.append("resource_id_hashed")

        sanitized: Dict[str, Any] = {}
        for key, value in envelope.payload.items():
            key_norm = key.lower()
            if key_norm in self._rules.drop_payload_keys:
                redactions.append(f"drop:{key_norm}")
                continue
            sanitized[key] = self._sanitize_payload_value(key, value, redactions)

        envelope.payload = sanitized
        envelope.privacy = PrivacyMetadata(
            pii_level=envelope.privacy.pii_level,
            redaction=_dedupe(redactions),
        )
        return envelope

    def _sanitize_payload_value(
        self, key: str, value: Any, redactions: List[str]
    ) -> Any:
        key_norm = key.lower()

        if key_norm in self._rules.hash_keys:
            redactions.append(f"hash:{key_norm}")
            return _hash_value(str(value), self._hash_salt)

        if isinstance(value, str):
            if key_norm == "url":
                allow_full = bool(self._rules.url_policy.get("allow_full_url", False))
                keep_domain_only = bool(
                    self._rules.url_policy.get("keep_domain_only", True)
                )
                if not allow_full:
                    value = sanitize_url(value, keep_domain_only=keep_domain_only)
                    redactions.append("url_sanitized")

            if key_norm in self._rules.mask_keys:
                value = mask_patterns(value, self._rules.redaction_patterns)
                redactions.append(f"mask:{key_norm}")

            max_len = self._rules.length_limits.get(key_norm)
            if max_len:
                value = truncate(value, max_len)

        return value


def load_privacy_rules(path: str | Path) -> PrivacyRules:
    path = Path(path)
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError("privacy rules must be a mapping")

    mask_keys = _lower_set(raw.get("mask_keys"))
    hash_keys = _lower_set(raw.get("hash_keys"))
    drop_payload_keys = _lower_set(raw.get("drop_payload_keys"))
    allowlist_apps = _lower_set(raw.get("allowlist_apps"))
    denylist_apps = _lower_set(raw.get("denylist_apps"))
    denylist_action = str(raw.get("denylist_action", "drop")).lower()

    length_limits = {
        str(k).lower(): int(v)
        for k, v in _as_dict(raw.get("length_limits")).items()
        if v is not None
    }

    url_policy = _as_dict(raw.get("url_policy"))

    redaction_patterns = []
    for pattern in raw.get("redaction_patterns", []) or []:
        if isinstance(pattern, dict):
            regex = pattern.get("regex")
        else:
            regex = pattern
        if not regex:
            continue
        redaction_patterns.append(re.compile(str(regex)))

    return PrivacyRules(
        mask_keys=mask_keys,
        hash_keys=hash_keys,
        length_limits=length_limits,
        url_policy=url_policy,
        redaction_patterns=redaction_patterns,
        drop_payload_keys=drop_payload_keys,
        allowlist_apps=allowlist_apps,
        denylist_apps=denylist_apps,
        denylist_action=denylist_action,
    )


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _lower_set(value: Any) -> Set[str]:
    if not value:
        return set()
    if isinstance(value, (list, set, tuple)):
        return {str(item).lower() for item in value}
    return {str(value).lower()}


def _hash_value(value: str, salt: str) -> str:
    return hmac_sha256(value, salt)


def _dedupe(values: Iterable[str]) -> List[str]:
    seen = set()
    output = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
