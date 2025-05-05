from app_lib import base_repository


class Repository(base_repository.BaseRepository):
    def list_items(self):
        """List items."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, item_name FROM items")
            return cursor.fetchall()
