import os
from typing import List, Tuple


class FileLoader:
    # Các thư mục cần bỏ qua khi quét folder
    IGNORED_DIRECTORIES = {
        ".git", ".svn", ".hg", "venv", ".venv", "__pycache__", 
        "node_modules", ".idea", ".vscode", "build", "dist", "bin", "obj"
    }

    # Các đuôi file văn bản/mã nguồn chấp nhận đọc
    ALLOWED_EXTENSIONS = {
        ".py", ".c", ".cpp", ".h", ".hpp", ".cs", ".java", ".js", ".ts",
        ".html", ".css", ".sql", ".json", ".xml", ".yaml", ".yml", ".md",
        ".txt", ".sh", ".bat", ".ps1", ".ini", ".cfg"
    }

    @staticmethod
    def read_single_file(file_path: str) -> str:
        """Đọc nội dung của một file văn bản."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as file_pointer:
                return file_pointer.read()
        except Exception as exception_error:
            return f"[Lỗi không thể đọc file {file_path}: {str(exception_error)}]"

    @classmethod
    def load_files_list(cls, file_paths: List[str], max_files: int = 15) -> Tuple[str, int]:
        """
        Đọc danh sách tối đa max_files file lẻ và đóng gói thành chuỗi Markdown.
        """
        selected_paths = file_paths[:max_files]
        combined_content = []
        loaded_count = 0

        for file_path in selected_paths:
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in cls.ALLOWED_EXTENSIONS or not file_extension:
                content = cls.read_single_file(file_path)
                relative_name = os.path.basename(file_path)
                combined_content.append(f"--- START FILE: {relative_name} ---\n{content}\n--- END FILE: {relative_name} ---\n")
                loaded_count += 1

        return "\n".join(combined_content), loaded_count

    @classmethod
    def load_directory_recursive(cls, directory_path: str, max_files: int = 200) -> Tuple[str, int]:
        """
        Quét đệ quy toàn bộ thư mục, lọc bỏ file rác/binary và đóng gói thành chuỗi Markdown.
        """
        combined_content = []
        loaded_count = 0

        for root_path, directory_names, file_names in os.walk(directory_path):
            # Bỏ qua các thư mục nằm trong danh sách IGNORED_DIRECTORIES
            directory_names[:] = [
                directory for directory in directory_names 
                if directory not in cls.IGNORED_DIRECTORIES
            ]

            for file_name in file_names:
                if loaded_count >= max_files:
                    break

                file_extension = os.path.splitext(file_name)[1].lower()
                if file_extension in cls.ALLOWED_EXTENSIONS:
                    full_file_path = os.path.join(root_path, file_name)
                    relative_file_path = os.path.relpath(full_file_path, directory_path)
                    
                    file_content = cls.read_single_file(full_file_path)
                    combined_content.append(
                        f"--- START FILE: {relative_file_path} ---\n{file_content}\n--- END FILE: {relative_file_path} ---\n"
                    )
                    loaded_count += 1

            if loaded_count >= max_files:
                break

        return "\n".join(combined_content), loaded_count