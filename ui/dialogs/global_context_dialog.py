from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QWidget, QLabel, QLineEdit
)
from model.database_manager import DatabaseManager


class GlobalContextDialog(QDialog):
    def __init__(self, database_manager: DatabaseManager, parent=None) -> None:
        super().__init__(parent)
        self.database_manager = database_manager
        self.setWindowTitle("Quản Lý Ngữ Cảnh Chung (Global Context)")
        self.resize(650, 480)
        self.setup_ui()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()

        system_tab_widget = QWidget()
        system_layout = QVBoxLayout(system_tab_widget)

        system_label = QLabel("Chỉ thị hệ thống (System Instruction chung cho mọi Session):")
        self.system_instruction_input = QTextEdit()
        self.system_instruction_input.setPlaceholderText(
            "Ví dụ: Bạn là trợ lý lập trình chuyên nghiệp. Hãy trả lời ngắn gọn, ưu tiên code C++ và Python..."
        )
        
        save_system_button = QPushButton("Lưu System Instruction")
        save_system_button.clicked.connect(self.save_system_instruction)

        system_layout.addWidget(system_label)
        system_layout.addWidget(self.system_instruction_input)
        system_layout.addWidget(save_system_button)
        self.tab_widget.addTab(system_tab_widget, "System Instruction")

        memory_tab_widget = QWidget()
        memory_layout = QVBoxLayout(memory_tab_widget)

        self.memory_table = QTableWidget()
        self.memory_table.setColumnCount(4)
        self.memory_table.setHorizontalHeaderLabels(["ID", "Phân loại", "Nội dung ghi nhớ", "Ngày tạo"])
        self.memory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        memory_layout.addWidget(self.memory_table)

        memory_input_layout = QHBoxLayout()
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Phân loại (vd: Phong cách, Quy tắc)...")

        self.memory_content_input = QLineEdit()
        self.memory_content_input.setPlaceholderText("Nội dung cần ghi nhớ...")

        add_memory_button = QPushButton("Thêm Trí Nhớ")
        add_memory_button.clicked.connect(self.add_user_memory)

        memory_input_layout.addWidget(self.category_input)
        memory_input_layout.addWidget(self.memory_content_input)
        memory_input_layout.addWidget(add_memory_button)
        memory_layout.addLayout(memory_input_layout)

        delete_memory_button = QPushButton("Xóa Trí Nhớ Đang Chọn")
        delete_memory_button.clicked.connect(self.delete_user_memory)
        memory_layout.addWidget(delete_memory_button)

        self.tab_widget.addTab(memory_tab_widget, "Bộ Nhớ Dài Hạn (User Memories)")
        main_layout.addWidget(self.tab_widget)

        self.load_system_instruction()
        self.load_user_memories()

    def load_system_instruction(self) -> None:
        instruction_text = self.database_manager.get_system_instruction()
        self.system_instruction_input.setPlainText(instruction_text)

    def save_system_instruction(self) -> None:
        instruction_text = self.system_instruction_input.toPlainText().strip()
        self.database_manager.update_system_instruction(instruction_text)
        QMessageBox.information(self, "Thông báo", "Đã lưu System Instruction thành công!")

    def load_user_memories(self) -> None:
        self.memory_table.setRowCount(0)
        memories = self.database_manager.get_all_user_memories()
        for row_index, data in enumerate(memories):
            self.memory_table.insertRow(row_index)
            self.memory_table.setItem(row_index, 0, QTableWidgetItem(str(data["id"])))
            self.memory_table.setItem(row_index, 1, QTableWidgetItem(data["memory_category"]))
            self.memory_table.setItem(row_index, 2, QTableWidgetItem(data["memory_content"]))
            self.memory_table.setItem(row_index, 3, QTableWidgetItem(str(data["created_at"])))

    def add_user_memory(self) -> None:
        category_text = self.category_input.text().strip()
        content_text = self.memory_content_input.text().strip()

        if not category_text or not content_text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ phân loại và nội dung!")
            return

        self.database_manager.add_user_memory(category_text, content_text)
        self.category_input.clear()
        self.memory_content_input.clear()
        self.load_user_memories()

    def delete_user_memory(self) -> None:
        current_row = self.memory_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Lỗi", "Hãy chọn một dòng để xóa!")
            return

        memory_id = int(self.memory_table.item(current_row, 0).text())
        self.database_manager.delete_user_memory(memory_id)
        self.load_user_memories()