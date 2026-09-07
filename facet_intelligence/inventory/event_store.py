"""Miss-tracking and emitted-event dedupe persistence."""

import json
import logging
from datetime import date
from typing import Any, Optional

from shared.db import DatabasePool

logger = logging.getLogger(__name__)


class MissTrackingStore:
    def __init__(self, db_pool: Optional[DatabasePool] = None) -> None:
        self._db_pool = db_pool

    def _pool(self) -> DatabasePool:
        if self._db_pool is None:
            self._db_pool = DatabasePool()
        return self._db_pool

    def load(self, tenant_id: str) -> dict[str, date]:
        query = """
            SELECT listing_id, first_missing_date
            FROM tenant_listing_miss_tracking
            WHERE tenant_id = %s
        """
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (tenant_id,))
            return {row[0]: row[1] for row in cursor.fetchall()}
        finally:
            cursor.close()
            pool.return_connection(conn)

    def save(self, tenant_id: str, tracking: dict[str, date]) -> None:
        delete_sql = """
            DELETE FROM tenant_listing_miss_tracking WHERE tenant_id = %s
        """
        insert_sql = """
            INSERT INTO tenant_listing_miss_tracking (tenant_id, listing_id, first_missing_date)
            VALUES (%s, %s, %s)
        """
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(delete_sql, (tenant_id,))
            for listing_id, first_missing in tracking.items():
                cursor.execute(insert_sql, (tenant_id, listing_id, first_missing))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            pool.return_connection(conn)


class EmittedEventStore:
    def __init__(self, db_pool: Optional[DatabasePool] = None) -> None:
        self._db_pool = db_pool

    def _pool(self) -> DatabasePool:
        if self._db_pool is None:
            self._db_pool = DatabasePool()
        return self._db_pool

    def record_if_new(self, tenant_id: str, event: dict[str, Any]) -> bool:
        """Persist event when event_id is new. Returns False if already emitted."""
        query = """
            INSERT INTO tenant_emitted_events (tenant_id, event_id, event_type, payload)
            VALUES (%s, %s, %s, %s::jsonb)
            ON CONFLICT (tenant_id, event_id) DO NOTHING
            RETURNING event_id
        """
        pool = self._pool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                query,
                (
                    tenant_id,
                    event["event_id"],
                    event["event_type"],
                    json.dumps(event),
                ),
            )
            inserted = cursor.fetchone() is not None
            conn.commit()
            return inserted
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            pool.return_connection(conn)
