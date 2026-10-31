from typing import List, Dict, Any, Optional
from model.database_manager import DatabaseManager
from controller.providers.gemini_provider import GeminiProvider
from controller.providers.local_summary_provider import LocalSummaryProvider
from controller.managers.rate_limit_manager import RateLimitManager


class SummaryService:
    def __init__(
        self, 
        database_manager: DatabaseManager, 
        rate_limit_manager: RateLimitManager
    ) -> None:
        self.database_manager: DatabaseManager = database_manager
        self.rate_limit_manager: RateLimitManager = rate_limit_manager

    def process_session_summarization(
        self, 
        session_identifier: int, 
        summary_mode: str, 
        api_key_identifier: int,
        use_local_provider: bool = False
    ) -> None:
        messages_list = self.database_manager.get_session_messages(session_identifier)
        if len(messages_list) < 10:
            return

        if not use_local_provider:
            is_exceeded, _ = self.rate_limit_manager.check_rate_limit_exceeded(
                api_key_identifier=api_key_identifier,
                model_mode="Gemma 26B",
                is_summary_request=True
            )
            if is_exceeded:
                return

        existing_summary_record = self.database_manager.get_session_summary(session_identifier)
        last_summarized_identifier = 0
        existing_summary_text = ""
        if existing_summary_record:
            last_summarized_identifier = existing_summary_record.get("last_summarized_message_id", 0)
            existing_summary_text = existing_summary_record.get("summary_text", "")

        unsummarized_messages = [
            message_item for message_item in messages_list 
            if message_item.get("message_id", 0) > last_summarized_identifier
        ]

        if len(unsummarized_messages) < 6:
            return

        conversation_text_block = "\n".join([
            f"{message_item.get('role', 'user')}: {message_item.get('content', '')}"
            for message_item in unsummarized_messages
        ])

        if summary_mode == "Rolling Summary":
            summary_prompt = (
                f"Tóm tắt ghi đè kết hợp tóm tắt cũ và câu thoại mới thành danh sách Fact-List ngắn gọn:\n"
                f"Tóm tắt cũ:\n{existing_summary_text}\n\n"
                f"Nội dung mới:\n{conversation_text_block}"
            )
        else:
            summary_prompt = (
                f"Tóm tắt cộng dồn nội dung hội thoại mới sau thành 1 block ngắn gọn dạng danh sách:\n"
                f"{conversation_text_block}"
            )

        try:
            if use_local_provider:
                local_provider = LocalSummaryProvider()
                summary_response_text = local_provider.generate_response(
                    prompt_text=summary_prompt,
                    conversation_history=[],
                    system_instruction="Bạn là trợ lý tóm tắt trích xuất dữ kiện kỹ thuật chính xác."
                )
            else:
                repository_target = (
                    self.database_manager.api_key_repository 
                    if hasattr(self.database_manager, "api_key_repository") 
                    else self.database_manager
                )
                gemini_provider = GeminiProvider(api_key_repository=repository_target)
                summary_response_text, _, summary_token_count, _ = gemini_provider.send_message(
                    prompt_text=summary_prompt,
                    conversation_history=[],
                    model_mode="Gemma 26B",
                    system_instruction="Bạn là trợ lý tóm tắt trích xuất dữ kiện kỹ thuật chính xác.",
                    temperature=0.3
                )

                self.rate_limit_manager.log_request_usage(
                    api_key_identifier=api_key_identifier,
                    model_mode="Gemma 26B",
                    total_token_count=summary_token_count,
                    is_agent_request=True
                )

            new_last_message_identifier = unsummarized_messages[-1].get("message_id", 0)
            
            if summary_mode == "Incremental Summary" and existing_summary_text:
                final_summary_text = f"{existing_summary_text}\n---\n{summary_response_text}"
            else:
                final_summary_text = summary_response_text

            self.database_manager.save_or_update_session_summary(
                session_identifier=session_identifier,
                summary_text=final_summary_text,
                last_summarized_message_id=new_last_message_identifier
            )
        except Exception:
            pass