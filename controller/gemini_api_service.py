from typing import Tuple, List, Dict, Any
from model.database_manager import DatabaseManager
from controller.providers.gemini_provider import GeminiProvider


class GeminiApiService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager = database_manager

    def send_message(
        self, 
        prompt: str, 
        history: List[Dict[str, Any]], 
        mode: str
    ) -> Tuple[str, str, int]:
        # 1. TỔNG HỢP NGỮ CẢNH CHUNG (System Instruction + User Memories từ CSDL)
        global_context_text = self.database_manager.get_formatted_global_context()

        # 2. GHÉP TẤT CẢ THÀNH PROMPT HOÀN CHỈNH
        # Nếu prompt có kèm theo context file/folder từ UI thì prompt gốc đã chứa sẵn đoạn [CONTEXT TỪ FILE]
        final_system_instruction = global_context_text

        # 3. LẤY API KEY VÀ MAP TÊN MODEL
        available_key_info = self.database_manager.get_available_api_key()
        if not available_key_info:
            raise ValueError("Chưa có API Key nào trong CSDL!")

        api_key_value = available_key_info["api_key"]

        # Map tên hiển thị trên UI thành Model ID chính thức của Google
        model_id_map = {
            "Agent Antigravity": "gemini-1.5-pro",
            "Gemma 4 26B": "gemma-2-27b-it",
            "Gemma 4 31B": "gemma-2-27b-it",
            "Gemini 3.8 Flash TTS": "gemini-1.5-flash"
        }
        target_model_id = model_id_map.get(mode, "gemini-1.5-flash")

        # 4. TRUYỀN SANG PROVIDER ĐỂ ĐÓNG GÓI PAYLOAD VÀ GỬI
        provider = GeminiProvider(api_key=api_key_value, model_name=target_model_id)
        response_text, token_count = provider.generate_response(
            prompt=prompt,
            history=history,
            system_instruction=final_system_instruction
        )

        return response_text, target_model_id, token_count