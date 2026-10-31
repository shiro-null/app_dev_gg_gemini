import os
import sqlite3
from pathlib import Path
from typing import Optional


class DatabaseConnection:
    def __init__(
        self,
        database_path: Optional[str] = None,
        schema_file_path: Optional[str] = None
    ) -> None:
        base_directory = Path(__file__).resolve().parent

        if database_path is None:
            self.database_path: str = str(base_directory / "app_data.db")
        else:
            self.database_path: str = database_path

        if schema_file_path is None:
            self.schema_file_path: str = str(base_directory / "schema.sql")
        else:
            self.schema_file_path: str = schema_file_path

        self.initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        database_connection = sqlite3.connect(self.database_path)
        database_connection.row_factory = sqlite3.Row
        database_connection.execute("PRAGMA foreign_keys = ON;")
        database_connection.execute("PRAGMA journal_mode = WAL;")  # Bật WAL Mode tăng tốc đọc ghi
        database_connection.execute("PRAGMA synchronous = NORMAL;")
        return database_connection

    def initialize_database(self) -> None:
        # Chỉ thực thi script khởi tạo khi file DB thực sự chưa được tạo ra
        if not os.path.exists(self.database_path):
            if not os.path.exists(self.schema_file_path):
                raise FileNotFoundError(
                    f"Không tìm thấy file schema tại đường dẫn: {self.schema_file_path}"
                )

            with open(self.schema_file_path, "r", encoding="utf-8") as schema_file_stream:
                sql_script_content = schema_file_stream.read()

            database_connection = self.get_connection()
            try:
                database_cursor = database_connection.cursor()
                database_cursor.executescript(sql_script_content)
                database_connection.commit()
            finally:
                database_connection.close()