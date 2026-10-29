from typing import List, Dict, Any
from PySide6.QtCore import QThread, Signal
from controller.gemini_api_service import GeminiApiService


class ApiWorker(QThread):
    finished_signal = Signal(str, str, int)
    error_signal = Signal(str)

    def __init__(
        self, 
        api_service: GeminiApiService, 
        prompt: str, 
        history: List[Dict[str, Any]], 
        mode: str,
        temperature: float
    ) -> None:
        super().__init__()
        self.api_service = api_service
        self.prompt = prompt
        self.history = history
        self.mode = mode
        self.temperature = temperature

    def run(self) -> None:
        try:
            response_text, used_model, token_count = self.api_service.send_message(
                self.prompt, self.history, self.mode
            )
            self.finished_signal.emit(response_text, used_model, token_count)
        except Exception as exception_error:
            self.error_signal.emit(str(exception_error))