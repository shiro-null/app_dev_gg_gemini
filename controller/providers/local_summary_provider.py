import urllib.request
import json
from typing import List, Dict, Any

from controller.providers.base_provider import BaseLLMProvider


class LocalSummaryProvider(BaseLLMProvider):
    def __init__(self, endpoint_url: str = "http://localhost:11434/api/generate", model_name: str = "qwen2.5-coder:3b") -> None:
        self.endpoint_url: str = endpoint_url
        self.model_name: str = model_name

    def count_tokens(self, text_content: str) -> int:
        return len(text_content) // 4

    def generate_response(
        self,
        prompt_text: str,
        conversation_history: List[Dict[str, Any]],
        system_instruction: str = ""
    ) -> str:
        full_prompt = f"{system_instruction}\n\n{prompt_text}".strip()
        
        request_payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False
        }

        json_data = json.dumps(request_payload).encode("utf-8")
        http_request = urllib.request.Request(
            self.endpoint_url,
            data=json_data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(http_request, timeout=60) as response_stream:
                response_json = json.loads(response_stream.read().decode("utf-8"))
                return response_json.get("response", "")
        except Exception as error_exception:
            raise RuntimeError(f"Lỗi khi gọi AI Local tóm tắt: {str(error_exception)}")

    def summarize_conversation_history(self, old_messages: List[Dict[str, Any]]) -> str:
        if not old_messages:
            return ""

        formatted_history_text = ""
        for message_item in old_messages:
            role_name = message_item.get("role", "user")
            content_text = message_item.get("content", "")
            formatted_history_text += f"{role_name.upper()}: {content_text}\n"

        summary_prompt = (
            "Hãy tóm tắt ngắn gọn các ý chính, thông số kỹ thuật và yêu cầu cốt lõi "
            "trong đoạn chat sau đây để làm ngữ cảnh lưu trữ:\n\n"
            f"{formatted_history_text}"
        )

        return self.generate_response(
            prompt_text=summary_prompt,
            conversation_history=[],
            system_instruction="Mày là bộ tóm tắt dữ liệu kỹ thuật ngắn gọn, chính xác."
        )