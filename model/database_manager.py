from typing import List, Dict, Any, Optional

from model.database_connection import DatabaseConnection
from model.api_key_repository import ApiKeyRepository
from model.session_repository import SessionRepository
from model.user_memory_repository import UserMemoryRepository


class DatabaseManager:
    def __init__(self, database_path: Optional[str] = None) -> None:
        self.database_connection = DatabaseConnection(database_path=database_path)
        self.api_key_repository = ApiKeyRepository(self.database_connection)
        self.session_repository = SessionRepository(self.database_connection)
        self.user_memory_repository = UserMemoryRepository(self.database_connection)

    # --- API KEY REPOSITORY METHODS ---
    def add_api_key(self, api_key_value: str, note_text: str = "") -> bool:
        return self.api_key_repository.add_api_key(api_key_value, note_text)

    def get_all_api_keys(self) -> List[Dict[str, Any]]:
        return self.api_key_repository.get_all_api_keys()

    def delete_api_key(self, key_identifier: int) -> None:
        self.api_key_repository.delete_api_key(key_identifier)

    def get_available_api_key(self) -> Optional[Dict[str, Any]]:
        return self.api_key_repository.get_available_api_key()

    def increment_api_key_usage(self, api_key_value: str) -> None:
        self.api_key_repository.increment_api_key_usage(api_key_value)

    # --- SESSION REPOSITORY METHODS ---
    def create_session(self, session_name: str, selected_model: str = "Gemma 4 26B") -> int:
        return self.session_repository.create_session(session_name, selected_model)

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        return self.session_repository.get_all_sessions()

    def delete_session(self, session_identifier: int) -> None:
        self.session_repository.delete_session(session_identifier)

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
        self.session_repository.add_message(
            session_identifier, role_name, message_content,
            prompt_tokens, response_tokens, total_tokens,
            model_name, api_key_id, temperature
        )

    def get_session_messages(self, session_identifier: int) -> List[Dict[str, Any]]:
        return self.session_repository.get_session_messages(session_identifier)

    def get_session_summary(self, session_identifier: int) -> Optional[Dict[str, Any]]:
        return self.session_repository.get_session_summary(session_identifier)

    def save_or_update_session_summary(
        self,
        session_identifier: int,
        summary_text: str,
        last_summarized_message_id: int
    ) -> None:
        self.session_repository.save_or_update_session_summary(
            session_identifier, summary_text, last_summarized_message_id
        )

    def search_messages_by_keyword(self, search_keyword: str) -> List[Dict[str, Any]]:
        return self.session_repository.search_messages_by_keyword(search_keyword)

    # --- SESSION FILE CONTEXTS METHODS (BẢNG 12) ---
    def get_session_files(self, session_identifier: int) -> List[Dict[str, Any]]:
        return self.session_repository.get_session_files(session_identifier)

    def add_session_file(self, session_identifier: int, file_path_value: str, is_active_status: int = 1) -> None:
        self.session_repository.add_session_file(session_identifier, file_path_value, is_active_status)

    def update_session_file_status(self, session_identifier: int, file_path_value: str, is_active_status: bool) -> None:
        self.session_repository.update_session_file_status(session_identifier, file_path_value, is_active_status)

    def delete_session_file(self, session_identifier: int, file_path_value: str) -> None:
        self.session_repository.delete_session_file(session_identifier, file_path_value)

    def copy_session_files(self, source_session_identifier: int, target_session_identifier: int) -> None:
        self.session_repository.copy_session_files(source_session_identifier, target_session_identifier)

    # --- USER MEMORY REPOSITORY METHODS ---
    def get_system_instruction(self) -> str:
        return self.user_memory_repository.get_system_instruction()

    def update_system_instruction(self, new_instruction_text: str) -> None:
        self.user_memory_repository.update_system_instruction(new_instruction_text)

    def add_user_memory(self, memory_category_text: str, memory_content_text: str) -> None:
        self.user_memory_repository.add_user_memory(memory_category_text, memory_content_text)

    def get_all_user_memories(self) -> List[Dict[str, Any]]:
        return self.user_memory_repository.get_all_user_memories()

    def delete_user_memory(self, memory_identifier: int) -> None:
        self.user_memory_repository.delete_user_memory(memory_identifier)

    def get_formatted_global_context(self) -> str:
        return self.user_memory_repository.get_formatted_global_context()