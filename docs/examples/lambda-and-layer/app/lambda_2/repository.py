from app_lib import base_repository


class Repository(base_repository.BaseRepository):
    def list_orders(self):
        """List orders."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, order_id FROM orders")
            return cursor.fetchall()
