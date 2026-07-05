"""
Canonical date helper for batch jobs and inventory snapshots.

Use pipeline_today() instead of date.today() or datetime.now().date().
Timezone: Australia/Brisbane (AEST, UTC+10).
"""

import argparse
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

PIPELINE_TZ = ZoneInfo("Australia/Brisbane")


def pipeline_today() -> date:
    """Return today's date in the pipeline's canonical timezone (AEST)."""
    return datetime.now(PIPELINE_TZ).date()


def parse_date_arg(raw: Optional[str] = None) -> date:
    """Parse an ISO-format date string, falling back to pipeline_today()."""
    if raw is None:
        return pipeline_today()
    return date.fromisoformat(raw)


def add_date_argument(parser: argparse.ArgumentParser) -> None:
    """Add a standard --date YYYY-MM-DD argument to a parser."""
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Override the pipeline date (ISO format). Defaults to today in AEST.",
    )
