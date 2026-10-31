from typing import Dict, Any, Tuple
from config.model_limits import MODEL_LIMITS
from model.database_manager import DatabaseManager


class RateLimitManager:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager: DatabaseManager = database_manager

    def check_rate_limit_exceeded(
        self, 
        api_key_identifier: int, 
        model_mode: str,
        is_agent_request: bool = False,
        is_summary_request: bool = False
    ) -> Tuple[bool, str]:
        """
        Kiểm tra hạn mức RPM, TPM, RPD cho Model thường, Agent lặp ngầm và lượt Tóm tắt.
        """
        model_configuration = MODEL_LIMITS.get(model_mode)
        if not model_configuration:
            return False, ""

        limit_rpm = model_configuration.get("rpm", 0)
        limit_tpm = model_configuration.get("tpm", 0)
        limit_rpd = model_configuration.get("rpd", 0)
        should_skip_request_count = model_configuration.get("skip_request_count", False)

        current_rpm, current_tpm, current_rpd = self.database_manager.get_current_rate_limits(
            api_key_id=api_key_identifier,
            model_name=model_mode
        )

        # 1. Kiểm tra TPM (Token Per Minute) - Áp dụng cho TẤT CẢ các loại Request
        if limit_tpm > 0 and current_tpm >= limit_tpm:
            request_type_label = "AI Tóm tắt" if is_summary_request else ("Agent" if is_agent_request else "Model")
            return True, f"{request_type_label} đã chạm trần Token/phút (TPM: {current_tpm:,}/{limit_tpm:,}). Vui lòng chờ ít giây!"

        # 2. Kiểm tra RPD (Request Per Day)
        if limit_rpd > 0 and current_rpd >= limit_rpd:
            return True, f"API Key đã vượt quá giới hạn Request/ngày (RPD: {current_rpd:,}/{limit_rpd:,}). Vui lòng đổi API Key!"

        # 3. Kiểm tra RPM (Request Per Minute)
        if not is_agent_request and not should_skip_request_count:
            if limit_rpm > 0 and current_rpm >= limit_rpm:
                return True, f"Đã chạm trần Request/phút (RPM: {current_rpm}/{limit_rpm}). Vui lòng chờ ít giây!"

        return False, ""

    def check_token_capacity_threshold(
        self, 
        current_token_count: int, 
        model_mode: str, 
        threshold_ratio: float = 0.8
    ) -> Tuple[bool, str]:
        """
        Kiểm tra xem tổng Token của Session đã đạt ngưỡng 80% giới hạn cửa sổ Token hay chưa.
        """
        model_configuration = MODEL_LIMITS.get(model_mode, {})
        limit_tpm = model_configuration.get("tpm", 100000)

        maximum_capacity = limit_tpm
        warning_threshold = int(maximum_capacity * threshold_ratio)

        if current_token_count >= warning_threshold:
            percentage_value = int((current_token_count / maximum_capacity) * 100)
            warning_message = (
                f"Session này đã chiếm {percentage_value}% giới hạn Token ({current_token_count:,}/{maximum_capacity:,})! "
                f"Bạn nên di cư sang Session mới."
            )
            return True, warning_message

        return False, ""

    def log_request_usage(
        self,
        api_key_identifier: int,
        model_mode: str,
        input_token_count: int = 0,
        output_token_count: int = 0,
        total_token_count: int = 0,
        is_agent_request: bool = False
    ) -> None:
        """Lưu vết lượt gọi API vào cơ sở dữ liệu."""
        self.database_manager.log_model_request(
            api_key_id=api_key_identifier,
            model_name=model_mode,
            input_tokens=input_token_count,
            output_tokens=output_token_count,
            total_tokens=total_token_count,
            is_agent_request=is_agent_request
        )

    def get_realtime_metrics(self, api_key_identifier: int, model_mode: str) -> Dict[str, Any]:
        """Trả về thông số thực tế RPM, TPM, RPD để cập nhật ngầm lên UI."""
        model_configuration = MODEL_LIMITS.get(model_mode, {})
        current_rpm, current_tpm, current_rpd = self.database_manager.get_current_rate_limits(
            api_key_id=api_key_identifier,
            model_name=model_mode
        )
        return {
            "current_rpm": current_rpm,
            "limit_rpm": model_configuration.get("rpm", 0),
            "current_tpm": current_tpm,
            "limit_tpm": model_configuration.get("tpm", 0),
            "current_rpd": current_rpd,
            "limit_rpd": model_configuration.get("rpd", 0),
            "skip_request_count": model_configuration.get("skip_request_count", False)
        }