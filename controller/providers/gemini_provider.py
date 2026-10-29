from typing import List, Dict, Any, Tuple
from google import genai
from google.genai import types
from google.genai.errors import APIError

from model.api_key_repository import ApiKeyRepository
from controller.providers.base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key_repository: ApiKeyRepository) -> None:
        self.api_key_repository: ApiKeyRepository = api_key_repository

    def generate_response(
        self,
        prompt_text: str,
        conversation_history: List[Dict[str, Any]],
        system_instruction: str = ""
    ) -> str:
        response_text, _, _ = self.send_message(
            prompt_text=prompt_text,
            conversation_history=conversation_history,
            mode="Tự động",
            system_instruction=system_instruction,
            temperature=0.7
        )
        return response_text

    def send_message(
        self,
        prompt_text: str,
        conversation_history: List[Dict[str, Any]],
        mode: str = "Tự động",
        system_instruction: str = "",
        temperature: float = 0.7
    ) -> Tuple[str, str, int]:
        all_keys = self.api_key_repository.get_all_api_keys()
        if not all_keys:
            raise Exception("Chưa có API Key nào trong CSDL! Hãy thêm API Key ở cài đặt.")

        keys_queue = [item["api_key"] for item in all_keys]

        # 1. MAP TÊN MODEL TỪ UI SANG MODEL ID CHUẨN CỦA GOOGLE API
        model_map = {
            "Agent Antigravity": "gemini-2.5-pro",
            "gemma 26B": "gemma-2-27b-it",
            "gemma 30B": "gemma-2-27b-it",
            "Gemini 3.8 Flash TTS": "gemini-2.5-flash",
            "Tự động": "gemini-2.5-flash"
        }
        chosen_model = model_map.get(mode, "gemini-2.5-flash")

        # 2. DỰNG NỘI DUNG CHAT HISTORY + PROMPT
        contents_payload = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents_payload.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents_payload.append({"role": "user", "parts": [{"text": prompt_text}]})

        # 3. ĐÓNG GÓI CONFIG (SYSTEM INSTRUCTION + TEMPERATURE)
        request_config = types.GenerateContentConfig(
            system_instruction=system_instruction if system_instruction.strip() else None,
            temperature=temperature
        )

        last_exception = None
        for current_key in keys_queue:
            try:
                client = genai.Client(api_key=current_key)
                
                # GỬI ĐẦY ĐỦ CONTENT + CONFIG LÊN SERVER GOOGLE
                response = client.models.generate_content(
                    model=chosen_model,
                    contents=contents_payload,
                    config=request_config
                )

                self.api_key_repository.increment_api_key_usage(current_key)
                response_text = response.text if response.text else "Không nhận được phản hồi."

                # 4. LẤY TOKEN TRỰC TIẾP TỪ METADATA (KHÔNG CẦN GỌI API ĐẾM LẠI)
                token_count = 0
                if response.usage_metadata:
                    token_count = response.usage_metadata.candidates_token_count or response.usage_metadata.total_token_count or 0

                return response_text, chosen_model, token_count

            except APIError as api_err:
                if api_err.code == 429:
                    last_exception = api_err
                    continue
                raise api_err
            except Exception as err:
                last_exception = err
                continue

        raise Exception(f"Tất cả API Key đều bị lỗi! Chi tiết: {str(last_exception)}")