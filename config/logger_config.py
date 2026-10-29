import os
import logging
from pathlib import Path


def setup_application_logging() -> logging.Logger:
    # Xác định đường dẫn thư mục log_runtime nằm ở thư mục gốc của dự án
    base_directory = Path(__file__).resolve().parent.parent
    log_directory_path = base_directory / "log_runtime"
    os.makedirs(log_directory_path, exist_ok=True)

    logger_instance = logging.getLogger("GeminiDevWorkspace")
    logger_instance.setLevel(logging.DEBUG)

    # Xóa các handler cũ nếu hàm bị gọi lại nhiều lần để tránh trùng log
    if logger_instance.hasHandlers():
        logger_instance.handlers.clear()

    # Định dạng thông tin log: [Thời gian] [Mức độ log] [Tên Logger]: Nội dung
    formatter_style = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Handler ghi toàn bộ log quá trình chạy (INFO trở lên)
    runtime_log_file_path = log_directory_path / "app_runtime.log"
    general_file_handler = logging.FileHandler(
        filename=runtime_log_file_path,
        mode="a",
        encoding="utf-8"
    )
    general_file_handler.setLevel(logging.INFO)
    general_file_handler.setFormatter(formatter_style)

    # 2. Handler ghi riêng lỗi (chỉ ghi ERROR và CRITICAL)
    error_log_file_path = log_directory_path / "error_runtime.log"
    error_file_handler = logging.FileHandler(
        filename=error_log_file_path,
        mode="a",
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter_style)

    # Đấu nối 2 handler vào logger chính
    logger_instance.addHandler(general_file_handler)
    logger_instance.addHandler(error_file_handler)

    return logger_instance


# Khởi tạo sẵn một instance logger để các module khác import xài trực tiếp
app_logger = setup_application_logging()