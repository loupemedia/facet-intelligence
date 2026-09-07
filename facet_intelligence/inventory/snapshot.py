"""Daily per-tenant listing snapshots."""

import logging
from datetime import date
from typing import Optional

from facet_intelligence.inventory.models import ListingState
from shared.db import DatabasePool

logger = logging.getLogger(__name__)

SNAPSHOT_COLUMNS = (
    "tenant_id",
    "snapshot_date",
    "listing_id",
    "stone_key",
    "retailer_code",
    "price",
    "currency",
    "availability",
    "cert_lab",
    "cert_number",
    "product_url",
)


class SnapshotStore:
    """Capture and read tenant listing snapshots."""

    def __init__(self, db_pool: Optional[DatabasePool] = None) -> None:
        self._db_pool = db_pool

    def _pool(self) -> DatabasePool:
        if self._db_pool is None:
            self._db_pool = DatabasePool()
        return self._db_pool

    def capture_snapshot(self, tenant_id: str, snapshot_date: date) -> int:
        """Copy live tenant_listings into tenant_listing_snapshots for snapshot_date."""
        delete_sql = """
            DELETE FROM tenant_listing_snapshots
            WHERE tenant_id = %s AND snapshot_date = %s
        """
        insert_sql = f"""
            INSERT INTO tenant_listing_snapshots ({", ".join(SNAPSHOT_COLUMNS)})
            SELECT
                tenant_id,
                %s AS snapshot_date,
                listing_id,
                stone_key,
                retailer_code,
                price,
                currency,
                availability,
                cert_lab,
                cert_number,
                product_url
            FROM tenant_listings
            WHERE tenant_id = %s
        """
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(delete_sql, (tenant_id, snapshot_date))
            cursor.execute(insert_sql, (snapshot_date, tenant_id))
            row_count = cursor.rowcount
            conn.commit()
            logger.info(
                "Captured snapshot for %s on %s (%d rows)",
                tenant_id,
                snapshot_date.isoformat(),
                row_count,
            )
            return row_count
        except Exception:
            conn.rollback()
            logger.error(
                "Failed snapshot for %s on %s",
                tenant_id,
                snapshot_date.isoformat(),
                exc_info=True,
            )
            raise
        finally:
            cursor.close()
            pool.return_connection(conn)

    def fetch_snapshot(
        self,
        tenant_id: str,
        snapshot_date: date,
    ) -> dict[str, ListingState]:
        query = """
            SELECT
                listing_id, stone_key, retailer_code, price, currency,
                availability, cert_lab, cert_number, product_url
            FROM tenant_listing_snapshots
            WHERE tenant_id = %s AND snapshot_date = %s
        """
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (tenant_id, snapshot_date))
            rows = cursor.fetchall()
        finally:
            cursor.close()
            pool.return_connection(conn)

        listings: dict[str, ListingState] = {}
        for row in rows:
            listing_id = row[0]
            listings[listing_id] = ListingState(
                listing_id=listing_id,
                stone_key=row[1],
                retailer_code=row[2],
                price=float(row[3]) if row[3] is not None else None,
                currency=row[4],
                availability=row[5],
                cert_lab=row[6],
                cert_number=row[7],
                product_url=row[8],
            )
        return listings

    def fetch_live_listings(self, tenant_id: str) -> dict[str, ListingState]:
        """Read current tenant_listings as ListingState map (pre-snapshot diff source)."""
        query = """
            SELECT
                listing_id, stone_key, retailer_code, price, currency,
                availability, cert_lab, cert_number, product_url
            FROM tenant_listings
            WHERE tenant_id = %s
        """
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (tenant_id,))
            rows = cursor.fetchall()
        finally:
            cursor.close()
            pool.return_connection(conn)

        listings: dict[str, ListingState] = {}
        for row in rows:
            listing_id = row[0]
            listings[listing_id] = ListingState(
                listing_id=listing_id,
                stone_key=row[1],
                retailer_code=row[2],
                price=float(row[3]) if row[3] is not None else None,
                currency=row[4],
                availability=row[5],
                cert_lab=row[6],
                cert_number=row[7],
                product_url=row[8],
            )
        return listings
