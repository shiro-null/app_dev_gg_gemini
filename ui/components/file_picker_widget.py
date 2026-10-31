from typing import List, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from model.database_manager import DatabaseManager
from controller.managers.file_loader import FileLoader


class FilePickerWidget(QWidget):
    def __init__(self, database_manager: DatabaseManager, parent=None) -> None:
        super().__init__(parent)
        self.database_manager: DatabaseManager = database_manager
        self.current_session_identifier: Optional[int] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>VS Code File Context Picker</b>"))

        self.file_picker_list = QListWidget()
        self.file_picker_list.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.file_picker_list)

        action_layout = QHBoxLayout()
        add_file_button = QPushButton("+ Thêm Files")
        add_file_button.clicked.connect(self.add_files)
        action_layout.addWidget(add_file_button)

        self.add_folder_button = QPushButton("+ Chọn Folder (Agent)")
        self.add_folder_button.clicked.connect(self.add_folder)
        action_layout.addWidget(self.add_folder_button)

        layout.addLayout(action_layout)

    def set_session(self, session_identifier: Optional[int]) -> None:
        self.current_session_identifier = session_identifier
        self.load_session_files()

    def set_agent_mode_enabled(self, is_enabled: bool) -> None:
        self.add_folder_button.setEnabled(is_enabled)
        tooltip_text = "Quét đệ quy toàn bộ thư mục dự án" if is_enabled else "Tính năng đọc Folder chỉ dành cho Agent Antigravity!"
        self.add_folder_button.setToolTip(tooltip_text)

    def load_session_files(self) -> None:
        self.file_picker_list.blockSignals(True)
        self.file_picker_list.clear()

        if self.current_session_identifier:
            saved_files = self.database_manager.get_session_files(self.current_session_identifier)
            for file_data in saved_files:
                single_file_path = file_data["file_path"]
                is_active_status = file_data.get("is_active", 1)
                file_name = single_file_path.replace("\\", "/").split("/")[-1]

                list_item = QListWidgetItem(f"📄 {file_name}")
                list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                list_item.setCheckState(Qt.Checked if is_active_status == 1 else Qt.Unchecked)
                list_item.setData(Qt.UserRole, single_file_path)
                self.file_picker_list.addItem(list_item)

        self.file_picker_list.blockSignals(False)

    def add_files(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Chọn file mã nguồn đưa vào Context Picker", "", "All Files (*)")
        if not file_paths:
            return

        for single_file_path in file_paths:
            file_name = single_file_path.replace("\\", "/").split("/")[-1]
            list_item = QListWidgetItem(f"📄 {file_name}")
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked)
            list_item.setData(Qt.UserRole, single_file_path)
            self.file_picker_list.addItem(list_item)

            if self.current_session_identifier:
                self.database_manager.add_session_file(self.current_session_identifier, single_file_path, 1)

    def add_folder(self) -> None:
        directory_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục dự án")
        if not directory_path:
            return

        formatted_text, loaded_count = FileLoader.load_directory_recursive(directory_path, max_files=200)
        folder_name = directory_path.replace("\\", "/").split("/")[-1]
        
        list_item = QListWidgetItem(f"📁 Folder: {folder_name}")
        list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
        list_item.setCheckState(Qt.Checked)
        list_item.setData(Qt.UserRole, directory_path)
        self.file_picker_list.addItem(list_item)

        if self.current_session_identifier:
            self.database_manager.add_session_file(self.current_session_identifier, directory_path, 1)

    def on_item_changed(self, list_item: QListWidgetItem) -> None:
        single_file_path = list_item.data(Qt.UserRole)
        is_checked_boolean = (list_item.checkState() == Qt.Checked)
        if self.current_session_identifier and single_file_path:
            self.database_manager.update_session_file_status(
                self.current_session_identifier, single_file_path, is_checked_boolean
            )

    def get_active_file_paths(self) -> List[str]:
        active_paths: List[str] = []
        for index_number in range(self.file_picker_list.count()):
            item_widget = self.file_picker_list.item(index_number)
            if item_widget.checkState() == Qt.Checked:
                active_paths.append(item_widget.data(Qt.UserRole))
        return active_paths