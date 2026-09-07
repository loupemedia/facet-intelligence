"""Persist canonical listings per tenant (idempotent upsert on listing_id)."""

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

from psycopg2.extras import execute_values

from facet_intelligence.ingestion.models import CanonicalListing
from shared.db import DatabasePool

logger = logging.getLogger(__name__)

UPSERT_BATCH_SIZE = 500

LISTING_COLUMNS = (
    "tenant_id",
    "listing_id",
    "stone_key",
    "retailer_code",
    "item_type",
    "cert_lab",
    "cert_number",
    "retailer_diamond_id",
    "diamond_type",
    "shape",
    "carat",
    "color",
    "clarity",
    "cut",
    "length_mm",
    "width_mm",
    "depth_mm",
    "price",
    "currency",
    "availability",
    "product_url",
    "image_url",
)

UPDATE_COLUMNS = tuple(
    column for column in LISTING_COLUMNS if column not in ("tenant_id", "listing_id")
)


@dataclass(frozen=True, slots=True)
class SyncStats:
    tenant_id: str
    listing_count: int
    rows_upserted: int


def listing_to_row(tenant_id: str, listing: CanonicalListing) -> tuple:
    return (
        tenant_id,
        listing.listing_id,
        listing.stone_key,
        listing.retailer_code,
        listing.item_type,
        listing.cert_lab,
        listing.cert_number,
        listing.retailer_diamond_id,
        listing.diamond_type,
        listing.shape,
        listing.carat,
        listing.color,
        listing.clarity,
        listing.cut,
        listing.length_mm,
        listing.width_mm,
        listing.depth_mm,
        listing.price,
        listing.currency,
        listing.availability,
        listing.product_url,
        listing.image_url,
    )


class ListingStore:
    """Upsert tenant listings into PostgreSQL."""

    def __init__(self, db_pool: Optional[DatabasePool] = None) -> None:
        self._db_pool = db_pool

    def _pool(self) -> DatabasePool:
        if self._db_pool is None:
            self._db_pool = DatabasePool()
        return self._db_pool

    def upsert_listings(
        self,
        tenant_id: str,
        listings: Iterable[CanonicalListing],
    ) -> SyncStats:
        rows = [listing_to_row(tenant_id, listing) for listing in listings]
        if not rows:
            return SyncStats(tenant_id=tenant_id, listing_count=0, rows_upserted=0)

        update_assignments = ", ".join(
            f"{column} = EXCLUDED.{column}" for column in UPDATE_COLUMNS
        )
        query = f"""
            INSERT INTO tenant_listings ({", ".join(LISTING_COLUMNS)})
            VALUES %s
            ON CONFLICT (tenant_id, listing_id) DO UPDATE SET
                {update_assignments},
                last_synced_at = NOW()
        """

        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        committed = 0
        try:
            for offset in range(0, len(rows), UPSERT_BATCH_SIZE):
                batch = rows[offset : offset + UPSERT_BATCH_SIZE]
                execute_values(cursor, query, batch, page_size=UPSERT_BATCH_SIZE)
                committed += len(batch)
            conn.commit()
            logger.info(
                "Upserted %d listing(s) for tenant %s",
                committed,
                tenant_id,
            )
        except Exception:
            conn.rollback()
            logger.error(
                "Failed to upsert listings for tenant %s",
                tenant_id,
                exc_info=True,
            )
            raise
        finally:
            cursor.close()
            pool.return_connection(conn)

        return SyncStats(
            tenant_id=tenant_id,
            listing_count=len(rows),
            rows_upserted=committed,
        )

    def _row_to_listing(self, row: tuple) -> CanonicalListing:
        return CanonicalListing(
            listing_id=row[0],
            stone_key=row[1],
            retailer_code=row[2],
            item_type=row[3],
            cert_lab=row[4],
            cert_number=row[5],
            retailer_diamond_id=row[6],
            diamond_type=row[7],
            shape=row[8],
            carat=float(row[9]) if row[9] is not None else None,
            color=row[10],
            clarity=row[11],
            cut=row[12],
            length_mm=float(row[13]) if row[13] is not None else None,
            width_mm=float(row[14]) if row[14] is not None else None,
            depth_mm=float(row[15]) if row[15] is not None else None,
            price=float(row[16]) if row[16] is not None else None,
            currency=row[17],
            availability=row[18],
            product_url=row[19],
            image_url=row[20],
        )

    _SELECT_LISTING = """
        SELECT
            listing_id, stone_key, retailer_code, item_type,
            cert_lab, cert_number, retailer_diamond_id, diamond_type,
            shape, carat, color, clarity, cut,
            length_mm, width_mm, depth_mm, price, currency,
            availability, product_url, image_url
        FROM tenant_listings
        WHERE tenant_id = %s
    """

    def fetch_listings(
        self,
        tenant_id: str,
        *,
        in_stock_only: bool = True,
    ) -> list[CanonicalListing]:
        query = self._SELECT_LISTING
        params: list = [tenant_id]
        if in_stock_only:
            query += " AND availability = 'in_stock'"
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return [self._row_to_listing(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
            pool.return_connection(conn)

    def fetch_listing_by_id(self, tenant_id: str, listing_id: str) -> CanonicalListing | None:
        query = self._SELECT_LISTING + " AND listing_id = %s"
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (tenant_id, listing_id))
            row = cursor.fetchone()
            return self._row_to_listing(row) if row else None
        finally:
            cursor.close()
            pool.return_connection(conn)

    def fetch_listing_by_cert(
        self,
        tenant_id: str,
        cert_number: str,
        *,
        cert_lab: str | None = None,
    ) -> CanonicalListing | None:
        query = self._SELECT_LISTING + " AND cert_number = %s"
        params: list = [tenant_id, cert_number]
        if cert_lab:
            query += " AND cert_lab = %s"
            params.append(cert_lab)
        query += " ORDER BY last_synced_at DESC LIMIT 1"
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return self._row_to_listing(row) if row else None
        finally:
            cursor.close()
            pool.return_connection(conn)
