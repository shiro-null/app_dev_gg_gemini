from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from model.database_manager import DatabaseManager


class ApiKeyManagerDialog(QDialog):
    def __init__(self, database_manager: DatabaseManager, parent=None) -> None:
        super().__init__(parent)
        self.database_manager = database_manager
        self.setWindowTitle("Quản Lý Danh Sách API Key")
        self.resize(600, 400)
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "API Key", "Ghi chú", "Số lượt dùng"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        input_layout = QHBoxLayout()
        self.key_input = QTextEdit()
        self.key_input.setPlaceholderText("Dán API Key vào đây...")
        self.key_input.setMaximumHeight(40)
        
        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Ghi chú Project...")
        self.note_input.setMaximumHeight(40)

        add_button = QPushButton("Thêm Key")
        add_button.clicked.connect(self.add_key)

        input_layout.addWidget(self.key_input)
        input_layout.addWidget(self.note_input)
        input_layout.addWidget(add_button)
        layout.addLayout(input_layout)

        delete_button = QPushButton("Xóa Key Đang Chọn")
        delete_button.clicked.connect(self.delete_key)
        layout.addWidget(delete_button)

        self.load_keys()

    def load_keys(self) -> None:
        self.table.setRowCount(0)
        keys = self.database_manager.get_all_api_keys()
        for row_index, data in enumerate(keys):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(data["id"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(data["api_key"]))
            self.table.setItem(row_index, 2, QTableWidgetItem(data["note"]))
            self.table.setItem(row_index, 3, QTableWidgetItem(str(data["usage_count"])))

    def add_key(self) -> None:
        key_text = self.key_input.toPlainText().strip()
        note_text = self.note_input.toPlainText().strip()
        if not key_text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập API Key!")
            return
            
        if self.database_manager.add_api_key(key_text, note_text):
            self.key_input.clear()
            self.note_input.clear()
            self.load_keys()
        else:
            QMessageBox.warning(self, "Lỗi", "API Key này đã tồn tại trong CSDL!")

    def delete_key(self) -> None:
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Lỗi", "Hãy chọn một dòng để xóa!")
            return
            
        key_id = int(self.table.item(current_row, 0).text())
        self.database_manager.delete_api_key(key_id)
        self.load_keys()