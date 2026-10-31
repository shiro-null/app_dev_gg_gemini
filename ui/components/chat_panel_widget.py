from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QComboBox, QCheckBox, QDoubleSpinBox, QGroupBox, QMessageBox
)
from model.database_manager import DatabaseManager
from controller.services.gemini_api_service import GeminiApiService
from controller.utils.code_cleaner import CodeCleaner
from config.model_limits import MODEL_LIMITS
from ui.api_worker import ApiWorker


class ChatPanelWidget(QWidget):
    def __init__(self, database_manager: DatabaseManager, api_service: GeminiApiService, parent=None) -> None:
        super().__init__(parent)
        self.database_manager: DatabaseManager = database_manager
        self.api_service: GeminiApiService = api_service
        self.current_session_identifier: Optional[int] = None
        self.active_file_paths_provider = None
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Warning Banner
        self.warning_banner = QWidget()
        self.warning_banner.setStyleSheet("background-color: #FFF3CD; border: 1px solid #FFEEBA; padding: 5px; border-radius: 4px;")
        banner_layout = QHBoxLayout(self.warning_banner)
        self.warning_label = QLabel("⚠️ Session này đã chiếm 80% giới hạn Token!")
        self.warning_label.setStyleSheet("color: #856404; font-weight: bold;")
        banner_layout.addWidget(self.warning_label)
        self.warning_banner.hide()
        layout.addWidget(self.warning_banner)

        # Top Bar Cấu hình Model
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(list(MODEL_LIMITS.keys()))
        top_bar.addWidget(self.model_combo)

        top_bar.addWidget(QLabel("Tóm tắt:"))
        self.summary_combo = QComboBox()
        self.summary_combo.addItems(["Rolling Summary", "Incremental Summary", "Tắt tóm tắt"])
        top_bar.addWidget(self.summary_combo)

        top_bar.addWidget(QLabel("Temp:"))
        self.temp_spinbox = QDoubleSpinBox()
        self.temp_spinbox.setRange(0.0, 2.0)
        self.temp_spinbox.setValue(0.7)
        top_bar.addWidget(self.temp_spinbox)

        self.compress_checkbox = QCheckBox("Tối ưu code")
        top_bar.addWidget(self.compress_checkbox)
        layout.addLayout(top_bar)

        # Metrics Rate Limit
        metrics_group = QGroupBox("Thống Kê Rate Limit Thích Ứng")
        metrics_layout = QHBoxLayout(metrics_group)
        self.label_rpd = QLabel("RPD: 0 / 0")
        self.label_rpm = QLabel("RPM: 0 / 0")
        self.label_tpm = QLabel("TPM: 0 / 0")
        self.label_input_tokens = QLabel("Đang nhập: 0 tokens")
        metrics_layout.addWidget(self.label_rpd)
        metrics_layout.addWidget(self.label_rpm)
        metrics_layout.addWidget(self.label_tpm)
        metrics_layout.addWidget(self.label_input_tokens)
        layout.addWidget(metrics_group)

        # Khung chat
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Input Bar
        input_bar = QHBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(100)
        self.input_text.textChanged.connect(self.on_input_text_changed)
        
        self.send_button = QPushButton("Gửi")
        self.send_button.clicked.connect(self.send_message)
        input_bar.addWidget(self.input_text)
        input_bar.addWidget(self.send_button)
        layout.addLayout(input_bar)

        self.status_label = QLabel("Trạng thái: Sẵn sàng")
        layout.addWidget(self.status_label)

    def set_session(self, session_identifier: Optional[int]) -> None:
        self.current_session_identifier = session_identifier
        self.warning_banner.hide()
        self.load_messages()

    def load_messages(self) -> None:
        self.chat_display.clear()
        if not self.current_session_identifier:
            return
        messages = self.database_manager.get_session_messages(self.current_session_identifier)
        for message_item in messages:
            sender_label = "MÀY" if message_item["role"] == "user" else "BOT"
            self.chat_display.append(f"<b>[{sender_label}]:</b>\n{message_item['content']}\n")

    def on_input_text_changed(self) -> None:
        text_content = self.input_text.toPlainText()
        estimated_count = max(1, len(text_content) // 3) if text_content else 0
        selected_model = self.model_combo.currentText()
        limit_tpm = MODEL_LIMITS[selected_model]["tpm"]
        self.label_input_tokens.setText(f"Đang nhập: {estimated_count:,} / {limit_tpm:,} tokens")

    def update_metrics_display(self) -> None:
        selected_model = self.model_combo.currentText()
        available_key_info = self.database_manager.get_available_api_key()
        if not available_key_info:
            return

        metrics_data = self.api_service.rate_limit_manager.get_realtime_metrics(
            api_key_identifier=available_key_info["id"],
            model_mode=selected_model
        )
        if metrics_data["skip_request_count"]:
            self.label_rpd.setText("RPD: Agent Mode")
            self.label_rpm.setText("RPM: N/A")
        else:
            self.label_rpd.setText(f"RPD: {metrics_data['current_rpd']:,} / {metrics_data['limit_rpd']:,}")
            self.label_rpm.setText(f"RPM: {metrics_data['current_rpm']} / {metrics_data['limit_rpm']}")

        self.label_tpm.setText(f"TPM: {metrics_data['current_tpm']:,} / {metrics_data['limit_tpm']:,}")

    def send_message(self) -> None:
        raw_text = self.input_text.toPlainText().strip()
        if not raw_text or not self.current_session_identifier:
            return

        # Sửa dứt điểm lỗi gọi class cũ ở đây
        prompt_text = CodeCleaner.compress_code(raw_text) if self.compress_checkbox.isChecked() else raw_text
        active_files = self.active_file_paths_provider() if self.active_file_paths_provider else []

        self.chat_display.append(f"<b>[MÀY]:</b>\n{prompt_text}\n")
        self.input_text.clear()

        history_messages = self.database_manager.get_session_messages(self.current_session_identifier)
        self.send_button.setEnabled(False)
        self.status_label.setText("Trạng thái: Đang xử lý ngầm...")

        self.worker_thread = ApiWorker(
            api_service=self.api_service,
            prompt_text=prompt_text,
            conversation_history=history_messages[:-1],
            model_mode=self.model_combo.currentText(),
            session_identifier=self.current_session_identifier,
            active_file_paths=active_files,
            summary_mode=self.summary_combo.currentText(),
            temperature=self.temp_spinbox.value()
        )
        self.worker_thread.finished_signal.connect(self.on_api_success)
        self.worker_thread.error_signal.connect(self.on_api_error)
        self.worker_thread.start()

    def on_api_success(self, response_text: str, used_model: str, token_count: int, api_key_identifier: int, capacity_warning_message: str) -> None:
        self.chat_display.append(f"<b>[BOT ({used_model})]:</b>\n{response_text}\n")
        self.status_label.setText(f"Trạng thái: Hoàn thành | Tokens: {token_count}")
        self.send_button.setEnabled(True)
        self.update_metrics_display()

        if capacity_warning_message:
            self.warning_label.setText(f"⚠️ {capacity_warning_message}")
            self.warning_banner.show()

    def on_api_error(self, error_message: str) -> None:
        QMessageBox.critical(self, "Lỗi API", error_message)
        self.status_label.setText("Trạng thái: Lỗi API!")
        self.send_button.setEnabled(True)
        self.update_metrics_display()