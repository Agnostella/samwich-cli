import logging
import sqlite3

logger = logging.getLogger(__name__)


class BaseRepository:
    _connection: sqlite3.Connection | None = None

    def __init__(self, config: dict):
        self._config = config

    def connect(self):
        if not self._connection:
            self._connection = sqlite3.connect(self._config["db_path"])
        return self._connection

    def get_health(self):
        """Get health status."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"
                )
                if cursor.fetchone() is not None:
                    return {"status": "healthy"}
            logger.error("Failed to perform health check query")
        except Exception:
            logger.exception("Database connection error")

        return {"status": "unhealthy"}
