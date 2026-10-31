from typing import Optional
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt, QTimer 

from model.database_manager import DatabaseManager
from controller.services.gemini_api_service import GeminiApiService
from ui.components.session_sidebar_widget import SessionSidebarWidget
from ui.components.file_picker_widget import FilePickerWidget
from ui.components.chat_panel_widget import ChatPanelWidget
from ui.dialogs.api_key_manager_dialog import ApiKeyManagerDialog
from ui.dialogs.global_context_dialog import GlobalContextDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gemini Dev Workspace Local")
        self.resize(1250, 850)

        self.database_manager = DatabaseManager()
        self.api_service = GeminiApiService(self.database_manager)
        self.current_session_identifier: Optional[int] = None

        # 1. Dựng khung giao diện thôi, chưa đụng gì tới CSDL hết
        self.setup_ui()
        self.bind_events()

        # 2. Lazy Load: Hoãn việc đọc DB lại 50ms để UI kịp hiện lên màn hình trước
        QTimer.singleShot(50, self.initialize_state)

    def setup_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        self.sidebar_widget = SessionSidebarWidget(self.database_manager)
        self.chat_widget = ChatPanelWidget(self.database_manager, self.api_service)
        self.file_picker_widget = FilePickerWidget(self.database_manager)

        splitter.addWidget(self.sidebar_widget)
        splitter.addWidget(self.chat_widget)
        splitter.addWidget(self.file_picker_widget)
        splitter.setSizes([200, 750, 300])

    def bind_events(self) -> None:
        self.sidebar_widget.session_selected_signal.connect(self.on_session_changed)
        self.sidebar_widget.create_session_signal.connect(self.create_new_session)
        self.sidebar_widget.open_global_context_signal.connect(self.open_global_context_dialog)
        self.sidebar_widget.open_key_manager_signal.connect(self.open_key_manager_dialog)

        self.chat_widget.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.chat_widget.active_file_paths_provider = self.file_picker_widget.get_active_file_paths

    def initialize_state(self) -> None:
        self.current_session_identifier = self.sidebar_widget.load_sessions(self.current_session_identifier)
        self.chat_widget.set_session(self.current_session_identifier)
        self.file_picker_widget.set_session(self.current_session_identifier)
        self.on_model_changed()

    def on_session_changed(self, session_identifier: int) -> None:
        self.current_session_identifier = session_identifier
        self.chat_widget.set_session(session_identifier)
        self.file_picker_widget.set_session(session_identifier)

    def create_new_session(self) -> None:
        session_name = f"Session {self.sidebar_widget.session_list.count() + 1}"
        session_identifier = self.database_manager.create_session(session_name)
        self.current_session_identifier = session_identifier
        self.initialize_state()

    def on_model_changed(self) -> None:
        selected_model = self.chat_widget.model_combo.currentText()
        is_agent_mode = (selected_model == "Agent Antigravity")
        self.file_picker_widget.set_agent_mode_enabled(is_agent_mode)
        self.chat_widget.update_metrics_display()

    def open_key_manager_dialog(self) -> None:
        dialog = ApiKeyManagerDialog(self.database_manager, self)
        dialog.exec()
        self.chat_widget.update_metrics_display()

    def open_global_context_dialog(self) -> None:
        dialog = GlobalContextDialog(self.database_manager, self)
        dialog.exec()