import os
from typing import Tuple


class FileValidator:
    @staticmethod
    def validate_attachment_file(file_path_string: str, max_size_mb: float = 20.0) -> Tuple[bool, str]:
        if not os.path.exists(file_path_string):
            return False, f"Tệp không tồn tại trên hệ thống: {file_path_string}"
        
        file_size_in_bytes = os.path.getsize(file_path_string)
        file_size_in_mb = file_size_in_bytes / (1024 * 1024)
        
        if file_size_in_mb > max_size_mb:
            return False, f"Tệp vượt quá dung lượng giới hạn ({file_size_in_mb:.2f} MB > {max_size_mb} MB)"
        
        return True, "Tệp hợp lệ"