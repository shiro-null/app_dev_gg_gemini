import re


class CodeCleaner:
    @staticmethod
    def compress_code(code_text: str) -> str:
        if not code_text:
            return ""

        processed_text = re.sub(r'/\*.*?\*/', '', code_text, flags=re.DOTALL)
        lines = processed_text.splitlines()
        cleaned_lines = []

        cpp_directives = (
            "#include", "#define", "#ifndef", "#ifdef", 
            "#pragma", "#endif", "#else", "#elif"
        )

        for line in lines:
            stripped_line = line.strip()

            if not stripped_line:
                continue

            if stripped_line.startswith("//") or stripped_line.startswith("--"):
                continue

            if stripped_line.startswith("#") and not stripped_line.startswith(cpp_directives):
                continue

            if "//" in line:
                is_contained_url = "http://" in line or "https://" in line
                if not is_contained_url:
                    line_parts = line.split("//")
                    first_part = line_parts[0]
                    double_quotes_count = first_part.count('"')
                    single_quotes_count = first_part.count("'")
                    if double_quotes_count % 2 == 0 and single_quotes_count % 2 == 0:
                        line = first_part

            cleaned_lines.append(line.rstrip())

        return "\n".join([single_line for single_line in cleaned_lines if single_line.strip()])