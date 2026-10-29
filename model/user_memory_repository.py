from typing import List, Dict, Any

from model.database_connection import DatabaseConnection


class UserMemoryRepository:
    def __init__(self, database_connection: DatabaseConnection) -> None:
        self.database_connection: DatabaseConnection = database_connection

    def get_system_instruction(self) -> str:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "SELECT setting_value FROM app_settings WHERE setting_key = 'system_instruction'"
            )
            result_row = database_cursor.fetchone()
            if result_row:
                return result_row["setting_value"]
            return ""
        finally:
            database_connection.close()

    def update_system_instruction(self, new_instruction_text: str) -> None:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "INSERT OR REPLACE INTO app_settings (setting_key, setting_value) VALUES ('system_instruction', ?)",
                (new_instruction_text.strip(),)
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def add_user_memory(self, memory_category_text: str, memory_content_text: str) -> None:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "INSERT INTO user_memories (memory_category, memory_content) VALUES (?, ?)",
                (memory_category_text.strip(), memory_content_text.strip())
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def get_all_user_memories(self) -> List[Dict[str, Any]]:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "SELECT id, memory_category, memory_content, created_at FROM user_memories ORDER BY id ASC"
            )
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()

    def delete_user_memory(self, memory_identifier: int) -> None:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "DELETE FROM user_memories WHERE id = ?",
                (memory_identifier,)
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def get_formatted_global_context(self) -> str:
        system_instruction_text = self.get_system_instruction()
        user_memory_records = self.get_all_user_memories()

        context_lines: List[str] = []

        if system_instruction_text:
            context_lines.append(f"CẤU HÌNH HỆ THỐNG:\n{system_instruction_text}\n")

        if user_memory_records:
            context_lines.append("TRÍ NHỚ VỀ NGƯỜI DÙNG:")
            for memory_item in user_memory_records:
                category_name = memory_item.get("memory_category", "")
                content_text = memory_item.get("memory_content", "")
                context_lines.append(f"- [{category_name}]: {content_text}")

        return "\n".join(context_lines)