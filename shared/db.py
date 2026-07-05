"""PostgreSQL connection pool for Facet Intelligence."""

import logging
import os

import psycopg2
from psycopg2 import pool as pg_pool

logger = logging.getLogger(__name__)


class DatabasePool:
    def __init__(self) -> None:
        try:
            self.pool = pg_pool.SimpleConnectionPool(
                1,
                20,
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                host=os.environ["DB_HOST"],
                port=os.environ["DB_PORT"],
                database=os.environ["DB_NAME"],
                sslmode=os.environ.get("DB_SSLMODE", "require"),
                connect_timeout=10,
            )
            logger.info("Database connection pool created successfully.")
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("Error connecting to PostgreSQL: %s", error, exc_info=True)
            raise

    def get_connection(self):
        try:
            return self.pool.getconn()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("Error getting connection from pool: %s", error, exc_info=True)
            raise

    def return_connection(self, conn) -> None:
        try:
            self.pool.putconn(conn)
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("Error returning connection to pool: %s", error, exc_info=True)
            raise

    def close_all(self) -> None:
        try:
            self.pool.closeall()
            logger.info("All database connections closed.")
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("Error closing connection pool: %s", error, exc_info=True)
            raise
