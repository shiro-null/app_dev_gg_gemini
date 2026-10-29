from typing import List, Dict, Any, Optional

from model.database_connection import DatabaseConnection


class SessionRepository:
    def __init__(self, database_connection: DatabaseConnection) -> None:
        self.database_connection: DatabaseConnection = database_connection

    def create_session(self, session_name: str) -> int:
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            database_cursor.execute(
                "INSERT INTO conversation_sessions (session_name) VALUES (?)",
                (session_name,)
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
                "SELECT id, session_name, created_at FROM conversation_sessions ORDER BY id DESC"
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
        token_count: int = 0
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
                INSERT INTO session_messages (session_id, message_id, role, content, token_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_identifier,
                    next_message_identifier,
                    role_name,
                    message_content,
                    token_count
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
                SELECT session_id, message_id, role, content, token_count, timestamp
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

    # --- QUẢN LÝ BẢNG TÓM TẮT SESSION ---

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