from typing import List, Dict, Any, Optional
from PySide6.QtCore import QThread, Signal
from controller.services.gemini_api_service import GeminiApiService


class ApiWorker(QThread):
    finished_signal = Signal(str, str, int, int, str)
    error_signal = Signal(str)

    def __init__(
        self, 
        api_service: GeminiApiService, 
        prompt_text: str, 
        conversation_history: List[Dict[str, Any]], 
        model_mode: str,
        session_identifier: Optional[int] = None,
        active_file_paths: Optional[List[str]] = None,
        summary_mode: str = "Rolling Summary",
        temperature: float = 0.7
    ) -> None:
        super().__init__()
        self.api_service: GeminiApiService = api_service
        self.prompt_text: str = prompt_text
        self.conversation_history: List[Dict[str, Any]] = conversation_history
        self.model_mode: str = model_mode
        self.session_identifier: Optional[int] = session_identifier
        self.active_file_paths: Optional[List[str]] = active_file_paths
        self.summary_mode: str = summary_mode
        self.temperature: float = temperature

    def run(self) -> None:
        try:
            response_text, used_model, token_count, api_key_identifier, warning_message = self.api_service.send_message(
                prompt_text=self.prompt_text,
                conversation_history=self.conversation_history,
                model_mode=self.model_mode,
                session_identifier=self.session_identifier,
                active_file_paths=self.active_file_paths,
                summary_mode=self.summary_mode,
                temperature=self.temperature
            )
            self.finished_signal.emit(response_text, used_model, token_count, api_key_identifier, warning_message)
        except Exception as exception_error:
            self.error_signal.emit(str(exception_error))