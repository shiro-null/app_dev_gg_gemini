import re


class ContextOptimizer:
    @staticmethod
    def compress_code(code_text: str) -> str:
        if not code_text:
            return ""

        # 1. Xóa comment khối /* ... */ (C, C++, Java, JS)
        processed_text = re.sub(r'/\*.*?\*/', '', code_text, flags=re.DOTALL)

        lines = processed_text.splitlines()
        cleaned_lines = []

        cpp_directives = (
            "#include", "#define", "#ifndef", "#ifdef", 
            "#pragma", "#endif", "#else", "#elif"
        )

        for line in lines:
            stripped_line = line.strip()

            # Bỏ qua dòng trống
            if not stripped_line:
                continue

            # 2. Xóa comment dòng // (C, C++, Java, JS)
            if stripped_line.startswith("//"):
                continue

            # 3. Xóa comment dòng -- (SQL)
            if stripped_line.startswith("--"):
                continue

            # 4. Xóa comment dòng # (Python, Shell, Bash)
            # Ngoại trừ các preprocessor directive của C/C++
            if stripped_line.startswith("#") and not stripped_line.startswith(cpp_directives):
                continue

            # Xóa comment inline cuối dòng nếu có (dành cho //)
            if "//" in line:
                line = line.split("//")[0]

            cleaned_lines.append(line.rstrip())

        # Lọc lại lần cuối để xóa toàn bộ dòng rỗng dư thừa
        final_code = "\n".join([line for line in cleaned_lines if line.strip()])
        return final_code