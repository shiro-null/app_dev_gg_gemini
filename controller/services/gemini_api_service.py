from typing import Tuple, List, Dict, Any, Optional
from model.database_manager import DatabaseManager
from controller.providers.gemini_provider import GeminiProvider
from controller.managers.rate_limit_manager import RateLimitManager
from controller.managers.file_loader import FileLoader
from controller.services.summary_service import SummaryService


class GeminiApiService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager: DatabaseManager = database_manager

        if hasattr(self.database_manager, "api_key_repository"):
            repository_target = self.database_manager.api_key_repository
        else:
            repository_target = self.database_manager

        self.gemini_provider: GeminiProvider = GeminiProvider(api_key_repository=repository_target)
        self.rate_limit_manager: RateLimitManager = RateLimitManager(database_manager=database_manager)
        self.summary_service: SummaryService = SummaryService(
            database_manager=database_manager, 
            rate_limit_manager=self.rate_limit_manager
        )

    def send_message(
        self, 
        prompt_text: str, 
        conversation_history: List[Dict[str, Any]], 
        model_mode: str,
        session_identifier: Optional[int] = None,
        active_file_paths: Optional[List[str]] = None,
        summary_mode: str = "Rolling Summary",
        temperature: float = 0.7,
        use_local_summary: bool = False
    ) -> Tuple[str, str, int, int, str]:
        available_key_data = self.database_manager.get_available_api_key()
        if not available_key_data:
            raise ValueError("Chưa có API Key nào trong cơ sở dữ liệu!")

        current_api_key_identifier = available_key_data.get("id", 0)

        is_exceeded, warning_message = self.rate_limit_manager.check_rate_limit_exceeded(
            api_key_identifier=current_api_key_identifier,
            model_mode=model_mode
        )
        if is_exceeded:
            raise RuntimeError(warning_message)

        # Sử dụng FileLoader thay vì open thủ công
        file_context_block = ""
        if active_file_paths:
            file_contents, loaded_count = FileLoader.load_files_list(
                file_paths=active_file_paths, 
                max_files=len(active_file_paths)
            )
            if loaded_count > 0:
                file_context_block = f"\n{file_contents}"

        final_prompt_text = prompt_text + file_context_block

        global_context_text = self.database_manager.get_formatted_global_context_for_session(
            session_identifier=session_identifier
        )

        response_text, used_model_identifier, token_count, actual_api_key_identifier = self.gemini_provider.send_message(
            prompt_text=final_prompt_text,
            conversation_history=conversation_history,
            model_mode=model_mode,
            system_instruction=global_context_text,
            temperature=temperature
        )

        self.rate_limit_manager.log_request_usage(
            api_key_identifier=actual_api_key_identifier,
            model_mode=model_mode,
            total_token_count=token_count
        )

        if session_identifier is not None and summary_mode != "Tắt tóm tắt":
            self.summary_service.process_session_summarization(
                session_identifier=session_identifier,
                summary_mode=summary_mode,
                api_key_identifier=actual_api_key_identifier,
                use_local_provider=use_local_summary
            )

        has_capacity_warning, capacity_warning_message = self.rate_limit_manager.check_token_capacity_threshold(
            current_token_count=token_count,
            model_mode=model_mode,
            threshold_ratio=0.8
        )

        return response_text, used_model_identifier, token_count, actual_api_key_identifier, capacity_warning_message