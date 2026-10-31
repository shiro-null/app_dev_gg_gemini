from typing import List, Dict, Any, Tuple
from google import genai
from google.genai import types
from google.genai.errors import APIError

from config.model_limits import MODEL_IDENTIFIER_MAPPING
from controller.providers.base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key_repository: Any) -> None:
        self.api_key_repository: Any = api_key_repository

    def count_tokens(self, text_content: str, model_mode: str = "Tự động") -> int:
        """Thực thi phương thức ảo count_tokens bắt buộc từ BaseLLMProvider."""
        if not text_content or not text_content.strip():
            return 0

        if hasattr(self.api_key_repository, "get_available_api_key"):
            api_key_data = self.api_key_repository.get_available_api_key()
            if api_key_data and isinstance(api_key_data, dict) and api_key_data.get("api_key"):
                try:
                    target_model_identifier = MODEL_IDENTIFIER_MAPPING.get(model_mode, "gemini-2.5-flash")
                    client_instance = genai.Client(api_key=api_key_data["api_key"])
                    token_count_response = client_instance.models.count_tokens(
                        model=target_model_identifier,
                        contents=text_content
                    )
                    if hasattr(token_count_response, "total_tokens") and token_count_response.total_tokens:
                        return token_count_response.total_tokens
                except Exception:
                    pass

        return max(1, len(text_content) // 3)

    def generate_response(
        self,
        prompt_text: str,
        conversation_history: List[Dict[str, Any]],
        system_instruction: str = ""
    ) -> str:
        response_text, _, _, _ = self.send_message(
            prompt_text=prompt_text,
            conversation_history=conversation_history,
            model_mode="Tự động",
            system_instruction=system_instruction,
            temperature=0.7
        )
        return response_text

    def send_message(
        self,
        prompt_text: str,
        conversation_history: List[Dict[str, Any]],
        model_mode: str = "Tự động",
        system_instruction: str = "",
        temperature: float = 0.7
    ) -> Tuple[str, str, int, int]:
        if hasattr(self.api_key_repository, "get_all_api_keys"):
            all_api_keys = self.api_key_repository.get_all_api_keys()
        else:
            all_api_keys = []

        if not all_api_keys:
            raise ValueError("Chưa có API Key nào trong cơ sở dữ liệu! Vui lòng thêm API Key trong cài đặt.")

        target_model_identifier = MODEL_IDENTIFIER_MAPPING.get(model_mode, "gemini-2.5-flash")

        contents_payload: List[Dict[str, Any]] = []
        for message_item in conversation_history:
            role_name = "user" if message_item.get("role") == "user" else "model"
            contents_payload.append({
                "role": role_name,
                "parts": [{"text": message_item.get("content", "")}]
            })
        
        contents_payload.append({
            "role": "user",
            "parts": [{"text": prompt_text}]
        })

        request_configuration = types.GenerateContentConfig(
            system_instruction=system_instruction.strip() if system_instruction and system_instruction.strip() else None,
            temperature=temperature
        )

        last_captured_exception: Exception | None = None

        for api_key_data in all_api_keys:
            if isinstance(api_key_data, dict):
                current_api_key_value = api_key_data.get("api_key", "")
                current_api_key_identifier = api_key_data.get("id", api_key_data.get("api_key_id", 0))
            else:
                current_api_key_value = str(api_key_data)
                current_api_key_identifier = 0

            if not current_api_key_value:
                continue

            try:
                client_instance = genai.Client(api_key=current_api_key_value)
                
                api_response = client_instance.models.generate_content(
                    model=target_model_identifier,
                    contents=contents_payload,
                    config=request_configuration
                )

                if hasattr(self.api_key_repository, "increment_api_key_usage"):
                    self.api_key_repository.increment_api_key_usage(current_api_key_value)

                response_text = api_response.text if api_response.text else "Không nhận được phản hồi từ hệ thống."

                total_token_count = 0
                if api_response.usage_metadata:
                    if api_response.usage_metadata.total_token_count:
                        total_token_count = api_response.usage_metadata.total_token_count
                    elif api_response.usage_metadata.candidates_token_count:
                        total_token_count = api_response.usage_metadata.candidates_token_count

                return response_text, target_model_identifier, total_token_count, current_api_key_identifier

            except APIError as api_error:
                last_captured_exception = api_error
                if api_error.code == 429:
                    continue
                continue
            except Exception as system_error:
                last_captured_exception = system_error
                continue

        raise RuntimeError(f"Tất cả API Key đều không thể kết nối! Lỗi chi tiết: {str(last_captured_exception)}")