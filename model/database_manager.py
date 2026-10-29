import os
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class DatabaseManager:
    def __init__(self, database_path: Optional[str] = None, schema_file_path: Optional[str] = None) -> None:
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
        # Chạy tự động dọn dẹp log rác quá 7 ngày để chống phình DB
        self.cleanup_expired_request_logs(days_to_keep=7)

    def get_connection(self) -> sqlite3.Connection:
        database_connection = sqlite3.connect(self.database_path)
        database_connection.row_factory = sqlite3.Row
        database_connection.execute("PRAGMA foreign_keys = ON;")
        return database_connection

    def initialize_database(self) -> None:
        database_file_exists = os.path.exists(self.database_path)

        if not database_file_exists:
            if not os.path.exists(self.schema_file_path):
                raise FileNotFoundError(f"Không tìm thấy file schema tại đường dẫn: {self.schema_file_path}")

            with open(self.schema_file_path, "r", encoding="utf-8") as schema_file_stream:
                sql_script_content = schema_file_stream.read()

            database_connection = self.get_connection()
            try:
                database_cursor = database_connection.cursor()
                database_cursor.executescript(sql_script_content)
                database_connection.commit()
            finally:
                database_connection.close()

    # --- CHỐNG PHÌNH DATABASE & QUẢN LÝ LOG REQUEST ---

    def cleanup_expired_request_logs(self, days_to_keep: int = 7) -> None:
        """
        Xóa các bản ghi log cũ hơn `days_to_keep` ngày trong bảng model_request_logs.
        Giúp CSDL luôn nhỏ gọn, không phình to dù dùng thời gian dài.
        """
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "DELETE FROM model_request_logs WHERE request_timestamp < datetime('now', '-' || ? || ' days')",
                (days_to_keep,)
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def log_model_request(
        self,
        api_key_id: int,
        model_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        is_agent_request: bool = False
    ) -> None:
        """Lưu vết đợt gửi API phục vụ tính toán RPM, TPM, RPD."""
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                """
                INSERT INTO model_request_logs 
                (api_key_id, model_name, input_tokens, output_tokens, total_tokens, is_agent_request)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    api_key_id,
                    model_name,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    1 if is_agent_request else 0
                )
            )
            database_connection.commit()
        finally:
            database_connection.close()

    def get_current_rate_limits(self, api_key_id: int, model_name: str) -> Tuple[int, int, int]:
        """
        Truy vấn chính xác thông số RPM, TPM trong 60s qua và RPD trong ngày
        cho ĐÚNG `api_key_id` và `model_name` từ CSDL.
        Trả về Tuple: (current_rpm, current_tpm, current_rpd)
        """
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()

            # 1. Tính RPM (Số request trong 60 giây gần nhất)
            database_cursor.execute(
                """
                SELECT COUNT(*) FROM model_request_logs
                WHERE api_key_id = ? AND model_name = ? AND is_agent_request = 0
                AND request_timestamp >= datetime('now', '-1 minute')
                """,
                (api_key_id, model_name)
            )
            current_rpm = database_cursor.fetchone()[0]

            # 2. Tính TPM (Số token trong 60 giây gần nhất)
            database_cursor.execute(
                """
                SELECT COALESCE(SUM(total_tokens), 0) FROM model_request_logs
                WHERE api_key_id = ? AND model_name = ?
                AND request_timestamp >= datetime('now', '-1 minute')
                """,
                (api_key_id, model_name)
            )
            current_tpm = database_cursor.fetchone()[0]

            # 3. Tính RPD (Số request trong ngày hôm nay)
            database_cursor.execute(
                """
                SELECT COUNT(*) FROM model_request_logs
                WHERE api_key_id = ? AND model_name = ? AND is_agent_request = 0
                AND date(request_timestamp) = date('now')
                """,
                (api_key_id, model_name)
            )
            current_rpd = database_cursor.fetchone()[0]

            return current_rpm, current_tpm, current_rpd
        finally:
            database_connection.close()

    # --- QUẢN LÝ CẤU HÌNH VÀ TRÍ NHỚ ---

    def get_system_instruction(self) -> str:
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute("SELECT setting_value FROM app_settings WHERE setting_key = 'system_instruction'")
            result_row = database_cursor.fetchone()
            if result_row:
                return result_row["setting_value"]
            return ""
        finally:
            database_connection.close()

    def update_system_instruction(self, new_instruction_text: str) -> None:
        database_connection = self.get_connection()
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
        database_connection = self.get_connection()
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
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute("SELECT id, memory_category, memory_content, created_at FROM user_memories ORDER BY id ASC")
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()

    def delete_user_memory(self, memory_identifier: int) -> None:
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute("DELETE FROM user_memories WHERE id = ?", (memory_identifier,))
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

    # --- QUẢN LÝ API KEYS ---

    def add_api_key(self, api_key_value: str, note_text: str = "") -> bool:
        database_connection = self.get_connection()
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
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute("SELECT id, api_key, note, usage_count, last_used FROM project_api_keys ORDER BY id ASC")
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()

    def delete_api_key(self, key_identifier: int) -> None:
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute("DELETE FROM project_api_keys WHERE id = ?", (key_identifier,))
            database_connection.commit()
        finally:
            database_connection.close()

    def get_available_api_key(self) -> Optional[Dict[str, Any]]:
        """Lấy API Key có số lượt sử dụng ít nhất, trả về dict gồm id và api_key."""
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute("SELECT id, api_key FROM project_api_keys ORDER BY usage_count ASC, id ASC LIMIT 1")
            result_row = database_cursor.fetchone()
            if result_row:
                return dict(result_row)
            return None
        finally:
            database_connection.close()

    def increment_api_key_usage(self, api_key_value: str) -> None:
        database_connection = self.get_connection()
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

    # --- QUẢN LÝ SESSION VÀ TIN NHẮN ---

    def create_session(self, session_name: str, selected_model: str = 'Gemma 4 26B') -> int:
        database_connection = self.get_connection()
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
        database_connection = self.get_connection()
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
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute("DELETE FROM conversation_sessions WHERE id = ?", (session_identifier,))
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
        """Lưu tin nhắn chi tiết kèm số token, model, api_key_id và temperature."""
        database_connection = self.get_connection()
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
        database_connection = self.get_connection()
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

    # --- TÌM KIẾM BẢNG ẢO FTS5 ---

    def search_messages_by_keyword(self, search_keyword: str) -> List[Dict[str, Any]]:
        database_connection = self.get_connection()
        try:
            database_cursor = database_connection.cursor()
            cleaned_search_keyword = search_keyword.strip().replace('"', '""')
            if not cleaned_search_keyword:
                return []

            formatted_full_text_search_query = f'"{cleaned_search_keyword}"'

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
                (formatted_full_text_search_query,)
            )
            fetched_rows = database_cursor.fetchall()
            return [dict(row_item) for row_item in fetched_rows]
        finally:
            database_connection.close()