"""Daily inventory signals batch job (Epic 2.1)."""

import argparse
import logging
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.tenants import DEFAULT_TENANTS  # noqa: E402
from facet_intelligence.inventory.signals import run_daily_inventory_signals  # noqa: E402
from shared.pipeline_date import add_date_argument, parse_date_arg  # noqa: E402

logger = logging.getLogger(__name__)

SCRIPT_ID = "F1_daily_inventory_signals"


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main() -> int:
    _configure_logging()
    parser = argparse.ArgumentParser(description="Run daily inventory signal detection")
    add_date_argument(parser)
    parser.add_argument(
        "--tenant",
        action="append",
        dest="tenants",
        help="Tenant id (repeatable). Defaults to all configured tenants.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect signals but do not deliver webhooks",
    )
    args = parser.parse_args()

    as_of = parse_date_arg(args.date)
    tenant_ids = args.tenants or sorted(DEFAULT_TENANTS.keys())
    exit_code = 0

    for tenant_id in tenant_ids:
        try:
            result = run_daily_inventory_signals(
                tenant_id,
                as_of,
                deliver_webhooks=not args.dry_run,
            )
            logger.info(
                "%s %s: snapshot=%d drops=%d disappeared=%d events=%d",
                SCRIPT_ID,
                tenant_id,
                result.snapshot_rows,
                result.price_drops,
                result.disappearances,
                result.events_delivered,
            )
        except KeyError:
            logger.error("Unknown tenant: %s", tenant_id)
            exit_code = 1
        except Exception:
            logger.error("Signal run failed for %s", tenant_id, exc_info=True)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
