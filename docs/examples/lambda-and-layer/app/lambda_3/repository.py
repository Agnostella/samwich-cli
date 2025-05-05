from app_lib import base_repository


class Repository(base_repository.BaseRepository):
    def list_accounts(self):
        """List accounts."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT account_id, account_name FROM accounts")
            return cursor.fetchall()
