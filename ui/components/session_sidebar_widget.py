from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem
from PySide6.QtCore import Signal, Qt
from model.database_manager import DatabaseManager


class SessionSidebarWidget(QWidget):
    session_selected_signal = Signal(int)
    create_session_signal = Signal()
    open_global_context_signal = Signal()
    open_key_manager_signal = Signal()

    def __init__(self, database_manager: DatabaseManager, parent=None) -> None:
        super().__init__(parent)
        self.database_manager: DatabaseManager = database_manager
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        new_session_button = QPushButton("+ Session Mới")
        new_session_button.clicked.connect(self.create_session_signal.emit)
        layout.addWidget(new_session_button)

        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.session_list)

        global_context_button = QPushButton("Cấu Hình Ngữ Cảnh Chung")
        global_context_button.clicked.connect(self.open_global_context_signal.emit)
        layout.addWidget(global_context_button)

        manage_keys_button = QPushButton("Quản Lý API Keys")
        manage_keys_button.clicked.connect(self.open_key_manager_signal.emit)
        layout.addWidget(manage_keys_button)

    def load_sessions(self, current_session_identifier: Optional[int] = None) -> Optional[int]:
        self.session_list.clear()
        sessions = self.database_manager.get_all_sessions()
        target_session_identifier = current_session_identifier

        for session_item in sessions:
            list_item = QListWidgetItem(session_item["session_name"])
            list_item.setData(Qt.UserRole, session_item["id"])
            self.session_list.addItem(list_item)

        if sessions and target_session_identifier is None:
            target_session_identifier = sessions[0]["id"]

        return target_session_identifier

    def on_item_clicked(self, item: QListWidgetItem) -> None:
        session_identifier = item.data(Qt.UserRole)
        self.session_selected_signal.emit(session_identifier)