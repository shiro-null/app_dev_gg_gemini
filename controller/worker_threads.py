from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Any

from controller.providers.gemini_provider import GeminiProvider
from controller.context_optimizer import ContextOptimizer


class ApiWorkerThread(QThread):
    finished_signal = Signal(str, str, int)
    error_signal = Signal(str)

    def __init__(
        self,
        gemini_provider: GeminiProvider,
        context_optimizer: ContextOptimizer,
        prompt_text: str,
        history_messages: List[Dict[str, Any]],
        mode_name: str,
        should_compress_code: bool = False
    ) -> None:
        super().__init__()
        self.gemini_provider: GeminiProvider = gemini_provider
        self.context_optimizer: ContextOptimizer = context_optimizer
        self.prompt_text: str = prompt_text
        self.history_messages: List[Dict[str, Any]] = history_messages
        self.mode_name: str = mode_name
        self.should_compress_code: bool = should_compress_code

    def run(self) -> None:
        try:
            processed_prompt = self.prompt_text
            if self.should_compress_code:
                processed_prompt = self.context_optimizer.compress_code(self.prompt_text)

            optimized_history = self.context_optimizer.optimize_chat_context(
                full_history=self.history_messages
            )

            response_text, used_model, token_count = self.gemini_provider.send_message(
                prompt_text=processed_prompt,
                conversation_history=optimized_history,
                mode=self.mode_name
            )

            self.finished_signal.emit(response_text, used_model, token_count)
        except Exception as error_exception:
            self.error_signal.emit(str(error_exception))