"""Shared by producer, worker and tools: message schema, JSON logs, .env loading."""

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ---------- Pub/Sub message: a pointer to the image, never the image itself ----------

class InvalidMessage(ValueError):
    """Message cannot be parsed. Retrying will not help."""


@dataclass(frozen=True)
class FrameMessage:
    frame_id: str
    camera_id: str
    gcs_uri: str
    published_at: str  # ISO 8601 UTC

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self), separators=(",", ":")).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> FrameMessage:
        try:
            raw = json.loads(data)
            return cls(**{k: str(raw[k]) for k in ("frame_id", "camera_id", "gcs_uri", "published_at")})
        except (ValueError, TypeError, KeyError) as e:
            raise InvalidMessage(f"bad message: {e!r}") from e


def split_gcs_uri(uri: str) -> tuple[str, str]:
    """'gs://bucket/a/b.jpg' -> ('bucket', 'a/b.jpg')"""
    bucket, _, name = uri.removeprefix("gs://").partition("/")
    if not uri.startswith("gs://") or not bucket or not name:
        raise InvalidMessage(f"bad gs:// uri: {uri!r}")
    return bucket, name


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ---------- Logs: one JSON line per event; Cloud Logging turns keys into searchable fields ----------

class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {"severity": record.levelname, "message": record.getMessage(), **getattr(record, "fields", {})}
        return json.dumps(entry, ensure_ascii=False, default=str)


def setup_logging() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
    return logging.getLogger("app")


def log(logger: logging.Logger, message: str, level: int = logging.INFO, **fields) -> None:
    logger.log(level, message, extra={"fields": fields})


# ---------- Config ----------

def load_env() -> None:
    """Load .env (same file the infra scripts use). Existing environment variables win."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and not key.startswith("#"):
            os.environ.setdefault(key.strip(), os.path.expandvars(value.strip().strip("\"'")))


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        raise SystemExit(f"missing environment variable {name} (set it in .env)")
    return value
