from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_response(
        self,
        prompt_text: str,
        conversation_history: List[Dict[str, Any]],
        system_instruction: str = ""
    ) -> str:
        pass

    @abstractmethod
    def count_tokens(self, text_content: str) -> int:
        pass