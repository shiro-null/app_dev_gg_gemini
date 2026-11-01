import sqlite3
from typing import Tuple
from model.database_connection import DatabaseConnection


class RateLimitRepository:
    def __init__(self, database_connection: DatabaseConnection) -> None:
        self.database_connection: DatabaseConnection = database_connection

    def log_model_request(
        self,
        api_key_id: int,
        model_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        is_agent_request: bool = False
    ) -> None:
        database_connection = self.database_connection.get_connection()
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
        database_connection = self.database_connection.get_connection()
        try:
            database_cursor = database_connection.cursor()
            
            # 1. Tính RPM: Số request thường trong 1 phút qua
            database_cursor.execute(
                """
                SELECT COUNT(*) 
                FROM model_request_logs 
                WHERE api_key_id = ? 
                  AND model_name = ? 
                  AND is_agent_request = 0 
                  AND request_timestamp >= datetime('now', '-1 minute')
                """,
                (api_key_id, model_name)
            )
            rpm_row = database_cursor.fetchone()
            current_rpm = rpm_row[0] if rpm_row else 0

            # 2. Tính TPM: Tổng token trong 1 phút qua
            database_cursor.execute(
                """
                SELECT COALESCE(SUM(total_tokens), 0) 
                FROM model_request_logs 
                WHERE api_key_id = ? 
                  AND model_name = ? 
                  AND request_timestamp >= datetime('now', '-1 minute')
                """,
                (api_key_id, model_name)
            )
            tpm_row = database_cursor.fetchone()
            current_tpm = tpm_row[0] if tpm_row else 0

            # 3. Tính RPD: Số request trong 24 giờ qua
            database_cursor.execute(
                """
                SELECT COUNT(*) 
                FROM model_request_logs 
                WHERE api_key_id = ? 
                  AND model_name = ? 
                  AND request_timestamp >= datetime('now', '-1 day')
                """,
                (api_key_id, model_name)
            )
            rpd_row = database_cursor.fetchone()
            current_rpd = rpd_row[0] if rpd_row else 0

            return current_rpm, current_tpm, current_rpd
        finally:
            database_connection.close()