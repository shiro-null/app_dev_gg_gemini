import sqlite3
from typing import List, Dict, Any, Optional
from model.database_connection import DatabaseConnection


class SessionRepository:
    def __init__(self, database_connection: DatabaseConnection) -> None:
        self.database_connection: DatabaseConnection = database_connection

    def create_session(self, session_name: str, selected_model: str = "Gemma 4 26B") -> int:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "INSERT INTO conversation_sessions (session_name, selected_model) VALUES (?, ?)",
                (session_name, selected_model)
            )
            created_session_id = database_cursor.lastrowid
            database_connection.commit()
            return created_session_id
        finally:
            database_connection.close()

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "SELECT id, session_name, selected_model, temperature, created_at FROM conversation_sessions ORDER BY id DESC"
            )
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()

    def delete_session(self, session_identifier: int) -> None:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "DELETE FROM conversation_sessions WHERE id = ?",
                (session_identifier,)
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def add_message(
        self,
        session_identifier: int,
        role_name: str,
        message_content: str,
        prompt_tokens: int = 0,
        response_tokens: int = 0,
        total_tokens: int = 0,
        model_name: Optional[str] = None,
        api_key_id: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> None:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "SELECT COALESCE(MAX(message_id), 0) + 1 FROM session_messages WHERE session_id = ?",
                (session_identifier,)
            )
            next_message_identifier = database_cursor.fetchone()[0]

            database_cursor.execute(
                """
                INSERT INTO session_messages 
                (session_id, message_id, role, content, prompt_tokens, response_tokens, total_tokens, model_name, api_key_id, temperature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_identifier,
                    next_message_identifier,
                    role_name,
                    message_content,
                    prompt_tokens,
                    response_tokens,
                    total_tokens,
                    model_name,
                    api_key_id,
                    temperature
                )
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def get_session_messages(self, session_identifier: int) -> List[Dict[str, Any]]:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                """
                SELECT session_id, message_id, role, content, prompt_tokens, response_tokens, total_tokens, model_name, api_key_id, temperature, timestamp
                FROM session_messages
                WHERE session_id = ?
                ORDER BY message_id ASC
                """,
                (session_identifier,)
            )
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()

    def get_session_summary(self, session_identifier: int) -> Optional[Dict[str, Any]]:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                """
                SELECT session_id, summary_text, last_summarized_message_id, updated_at
                FROM session_summaries
                WHERE session_id = ?
                """,
                (session_identifier,)
            )
            result_row = database_cursor.fetchone()
            if result_row:
                return dict(result_row)
            return None
        finally:
            database_connection.close()

    def save_or_update_session_summary(
        self,
        session_identifier: int,
        summary_text: str,
        last_summarized_message_id: int
    ) -> None:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                """
                INSERT INTO session_summaries (session_id, summary_text, last_summarized_message_id, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    summary_text = excluded.summary_text,
                    last_summarized_message_id = excluded.last_summarized_message_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (session_identifier, summary_text.strip(), last_summarized_message_id)
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def search_messages_by_keyword(self, search_keyword: str) -> List[Dict[str, Any]]:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            cleaned_search_keyword = search_keyword.strip().replace('"', '""')
            if not cleaned_search_keyword:
                return []

            formatted_fts_query = f'"{cleaned_search_keyword}"'

            database_cursor.execute(
                """
                SELECT 
                    full_text_search.session_id,
                    full_text_search.message_id,
                    full_text_search.content,
                    session_record.session_name
                FROM session_messages_fts full_text_search
                JOIN conversation_sessions session_record ON full_text_search.session_id = session_record.id
                WHERE session_messages_fts MATCH ?
                ORDER BY full_text_search.session_id DESC, full_text_search.message_id ASC
                """,
                (formatted_fts_query,)
            )
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()

    # --- CÁC HÀM XỬ LÝ BẢNG 12 (session_file_references) ---

    def get_session_files(self, session_identifier: int) -> List[Dict[str, Any]]:
        """Lấy danh sách file và folder context thuộc về một Session từ bảng session_file_references."""
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                """
                SELECT id, session_id, file_name, file_path, is_active, added_at
                FROM session_file_references
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_identifier,)
            )
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()

    def add_session_file(self, session_identifier: int, file_path_value: str, is_active_status: int = 1) -> None:
        """Thêm file hoặc folder mới vào bảng session_file_references."""
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            cleaned_file_path = file_path_value.strip()
            extracted_file_name = cleaned_file_path.replace("\\", "/").split("/")[-1]

            database_cursor.execute(
                """
                INSERT INTO session_file_references (session_id, file_name, file_path, is_active)
                VALUES (?, ?, ?, ?)
                """,
                (session_identifier, extracted_file_name, cleaned_file_path, is_active_status)
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def update_session_file_status(self, session_identifier: int, file_path_value: str, is_active_status: bool) -> None:
        """Cập nhật trạng thái tick chọn (is_active) của file trong bảng session_file_references."""
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            integer_active_flag = 1 if is_active_status else 0
            database_cursor.execute(
                """
                UPDATE session_file_references
                SET is_active = ?
                WHERE session_id = ? AND file_path = ?
                """,
                (integer_active_flag, session_identifier, file_path_value.strip())
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def delete_session_file(self, session_identifier: int, file_path_value: str) -> None:
        """Xóa một file khỏi danh sách ngữ cảnh của Session trong bảng session_file_references."""
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                """
                DELETE FROM session_file_references
                WHERE session_id = ? AND file_path = ?
                """,
                (session_identifier, file_path_value.strip())
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def copy_session_files(self, source_session_identifier: int, target_session_identifier: int) -> None:
        """Sao chép toàn bộ danh sách file context từ Session cũ sang Session mới khi di cư."""
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                """
                INSERT INTO session_file_references (session_id, file_name, file_path, is_active)
                SELECT ?, file_name, file_path, is_active
                FROM session_file_references
                WHERE session_id = ?
                """,
                (target_session_identifier, source_session_identifier)
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def get_formatted_global_context_for_session(self, session_identifier: Optional[int] = None) -> str:
        summary_text = None
        if session_identifier is not None:
            summary_record = self.session_repository.get_session_summary(session_identifier)
            if summary_record:
                summary_text = summary_record.get("summary_text")
                
        return self.user_memory_repository.get_formatted_global_context(summary_text=summary_text)