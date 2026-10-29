import sqlite3
import datetime
from typing import List, Dict, Any, Optional

from model.database_connection import DatabaseConnection


class ApiKeyRepository:
    def __init__(self, database_connection: DatabaseConnection) -> None:
        self.database_connection: DatabaseConnection = database_connection

    def add_api_key(self, api_key_value: str, note_text: str = "") -> bool:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "INSERT INTO project_api_keys (api_key, note) VALUES (?, ?)",
                (api_key_value.strip(), note_text.strip())
            )
            database_connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            database_connection.close()

    def get_all_api_keys(self) -> List[Dict[str, Any]]:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "SELECT id, api_key, note, usage_count, last_used FROM project_api_keys ORDER BY id ASC"
            )
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()

    def delete_api_key(self, key_identifier: int) -> None:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "DELETE FROM project_api_keys WHERE id = ?",
                (key_identifier,)
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def get_available_api_key(self) -> Optional[str]:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "SELECT api_key FROM project_api_keys ORDER BY usage_count ASC, id ASC LIMIT 1"
            )
            result_row = database_cursor.fetchone()
            if result_row:
                return result_row["api_key"]
            return None
        finally:
            database_connection.close()

    def increment_api_key_usage(self, api_key_value: str) -> None:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            current_timestamp_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            database_cursor.execute(
                "UPDATE project_api_keys SET usage_count = usage_count + 1, last_used = ? WHERE api_key = ?",
                (current_timestamp_string, api_key_value)
            )
            database_connection.commit()
        finally:
            database_connection.close()