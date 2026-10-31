from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Any, Optional

from controller.services.gemini_api_service import GeminiApiService
from controller.utils.code_cleaner import CodeCleaner


class ApiWorkerThread(QThread):
    finished_signal = Signal(str, str, int, int, str)
    error_signal = Signal(str)

    def __init__(
        self,
        gemini_api_service: GeminiApiService,
        prompt_text: str,
        history_messages: List[Dict[str, Any]],
        mode_name: str,
        session_identifier: Optional[int] = None,
        active_file_paths: Optional[List[str]] = None,
        summary_mode: str = "Rolling Summary",
        should_compress_code: bool = False,
        temperature: float = 0.7
    ) -> None:
        super().__init__()
        self.gemini_api_service: GeminiApiService = gemini_api_service
        self.prompt_text: str = prompt_text
        self.history_messages: List[Dict[str, Any]] = history_messages
        self.mode_name: str = mode_name
        self.session_identifier: Optional[int] = session_identifier
        self.active_file_paths: Optional[List[str]] = active_file_paths
        self.summary_mode: str = summary_mode
        self.should_compress_code: bool = should_compress_code
        self.temperature: float = temperature

    def run(self) -> None:
        try:
            processed_prompt_text = self.prompt_text
            if self.should_compress_code:
                processed_prompt_text = CodeCleaner.compress_code(self.prompt_text)

            optimized_history_messages = self.history_messages[-20:] if len(self.history_messages) > 20 else self.history_messages

            response_text, used_model_identifier, token_count, api_key_identifier, capacity_warning_message = (
                self.gemini_api_service.send_message(
                    prompt_text=processed_prompt_text,
                    conversation_history=optimized_history_messages,
                    model_mode=self.mode_name,
                    session_identifier=self.session_identifier,
                    active_file_paths=self.active_file_paths,
                    summary_mode=self.summary_mode,
                    temperature=self.temperature
                )
            )

            self.finished_signal.emit(
                response_text, 
                used_model_identifier, 
                token_count, 
                api_key_identifier, 
                capacity_warning_message
            )
        except Exception as error_exception:
            self.error_signal.emit(str(error_exception))