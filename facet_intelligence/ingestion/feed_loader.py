"""Load raw listing rows from CSV or JSON feeds."""

import csv
import json
import logging
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Mapping

logger = logging.getLogger(__name__)

SUPPORTED_SOURCES = frozenset({"csv", "json"})

__all__ = [
    "load_csv_rows",
    "load_feed",
    "load_json_rows",
    "parse_feed_payload",
]


def load_csv_rows(content: str) -> list[dict[str, Any]]:
    """Parse CSV text with a header row into dict rows."""
    reader = csv.DictReader(StringIO(content))
    if reader.fieldnames is None:
        return []
    return [dict(row) for row in reader]


def load_json_rows(content: str) -> list[dict[str, Any]]:
    """Parse JSON feed: top-level array or ``{"listings": [...]}``."""
    payload = json.loads(content)
    return list(parse_feed_payload(payload))


def parse_feed_payload(payload: Any) -> Iterable[dict[str, Any]]:
    """Normalise API-style sync bodies and bare arrays to listing dicts."""
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, Mapping):
                yield dict(item)
            else:
                logger.warning("Skipping non-object JSON listing entry: %r", item)
        return

    if isinstance(payload, Mapping):
        listings = payload.get("listings")
        if listings is None:
            raise ValueError("JSON object must contain a 'listings' array")
        if not isinstance(listings, list):
            raise ValueError("'listings' must be an array")
        for item in listings:
            if isinstance(item, Mapping):
                yield dict(item)
            else:
                logger.warning("Skipping non-object listings entry: %r", item)
        return

    raise ValueError(f"Unsupported JSON payload type: {type(payload).__name__}")


def load_feed(source: str, path: Path | str) -> list[dict[str, Any]]:
    """Load raw rows from a CSV or JSON file on disk."""
    source_type = source.strip().lower()
    if source_type not in SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported feed source {source!r}; expected csv or json")

    text = Path(path).read_text(encoding="utf-8")
    if source_type == "csv":
        return load_csv_rows(text)
    return load_json_rows(text)
