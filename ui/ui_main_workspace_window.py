import sys
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QComboBox, QSplitter, QMessageBox, QCheckBox, QFileDialog, QDoubleSpinBox,
    QGroupBox
)
from PySide6.QtCore import Qt

from model.database_manager import DatabaseManager
from controller.context_optimizer import ContextOptimizer
from controller.gemini_api_service import GeminiApiService
from controller.file_loader import FileLoader

from config.model_limits import MODEL_LIMITS
from config.logger_config import app_logger  # LOG INTEGRATION
from ui.api_worker import ApiWorker
from ui.dialogs.api_key_manager_dialog import ApiKeyManagerDialog
from ui.dialogs.global_context_dialog import GlobalContextDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gemini Dev Workspace Local")
        self.resize(1150, 800)

        app_logger.info("Khởi động ứng dụng Gemini Dev Workspace Local...")

        try:
            self.database_manager = DatabaseManager()
            self.api_service = GeminiApiService(self.database_manager)
            app_logger.info("Khởi tạo DatabaseManager và GeminiApiService thành công.")
        except Exception as init_err:
            app_logger.error(f"Khởi tạo hệ thống thất bại: {str(init_err)}", exc_info=True)

        self.current_session_id = None

        self.setup_ui()
        self.load_sessions()
        self.on_model_changed()

    def setup_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Cột bên trái: Quản lý Session
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        new_session_button = QPushButton("+ Session Mới")
        new_session_button.clicked.connect(self.create_new_session)
        left_layout.addWidget(new_session_button)

        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self.on_session_selected)
        left_layout.addWidget(self.session_list)

        global_context_button = QPushButton("Cấu Hình Ngữ Cảnh Chung")
        global_context_button.clicked.connect(self.open_global_context_manager)
        left_layout.addWidget(global_context_button)

        manage_keys_button = QPushButton("Quản Lý API Keys")
        manage_keys_button.clicked.connect(self.open_key_manager)
        left_layout.addWidget(manage_keys_button)

        splitter.addWidget(left_widget)

        # Cột bên phải: Khung Chat & Bảng thông số
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        top_bar = QHBoxLayout()
        
        top_bar.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(list(MODEL_LIMITS.keys()))
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        top_bar.addWidget(self.model_combo)

        top_bar.addWidget(QLabel("Nhiệt độ (Temp):"))
        self.temp_spinbox = QDoubleSpinBox()
        self.temp_spinbox.setRange(0.0, 2.0)
        self.temp_spinbox.setSingleStep(0.1)
        self.temp_spinbox.setValue(0.7)
        top_bar.addWidget(self.temp_spinbox)

        self.compress_checkbox = QCheckBox("Tự động tối ưu code")
        top_bar.addWidget(self.compress_checkbox)

        right_layout.addLayout(top_bar)

        metrics_group = QGroupBox("Thống Kê Rate Limit & Token Limit")
        metrics_layout = QHBoxLayout(metrics_group)

        self.label_rpd = QLabel("RPD (Request/Ngày): 0 / 0")
        self.label_rpm = QLabel("RPM (Request/Phút): 0 / 0")
        self.label_tpm = QLabel("TPM (Tokens/Phút): 0 / 0")
        self.label_input_tokens = QLabel("Đang nhập: 0 tokens")

        metrics_layout.addWidget(self.label_rpd)
        metrics_layout.addWidget(self.label_rpm)
        metrics_layout.addWidget(self.label_tpm)
        metrics_layout.addWidget(self.label_input_tokens)

        right_layout.addWidget(metrics_group)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        right_layout.addWidget(self.chat_display)

        input_bar = QHBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(100)
        self.input_text.setPlaceholderText("Nhập câu hỏi hoặc dán code vào đây...")
        self.input_text.textChanged.connect(self.on_input_text_changed)

        button_file_layout = QVBoxLayout()
        self.attach_files_button = QPushButton("Chọn Files (Max 15)")
        self.attach_files_button.clicked.connect(self.attach_files_action)

        self.attach_folder_button = QPushButton("Chọn Folder Project")
        self.attach_folder_button.clicked.connect(self.attach_folder_action)

        self.send_button = QPushButton("Gửi")
        self.send_button.clicked.connect(self.send_message)

        button_file_layout.addWidget(self.attach_files_button)
        button_file_layout.addWidget(self.attach_folder_button)
        button_file_layout.addWidget(self.send_button)

        input_bar.addWidget(self.input_text)
        input_bar.addLayout(button_file_layout)
        right_layout.addLayout(input_bar)

        self.status_label = QLabel("Trạng thái: Sẵn sàng | Token lượt trước: 0")
        right_layout.addWidget(self.status_label)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 900])

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 3)

    def on_input_text_changed(self) -> None:
        text = self.input_text.toPlainText()
        estimated_count = self.estimate_tokens(text)
        selected_model = self.model_combo.currentText()
        limit_tpm = MODEL_LIMITS[selected_model]["tpm"]
        
        self.label_input_tokens.setText(f"Đang nhập: {estimated_count:,} / {limit_tpm:,} tokens (ước tính)")

    def on_model_changed(self) -> None:
        selected_model = self.model_combo.currentText()
        is_agent_mode = (selected_model == "Agent Antigravity")
        self.attach_folder_button.setEnabled(is_agent_mode)
        
        if not is_agent_mode:
            self.attach_folder_button.setToolTip("Chỉ dành riêng cho Agent Antigravity!")
        else:
            self.attach_folder_button.setToolTip("Quét toàn bộ thư mục dự án")

        app_logger.info(f"Đã chuyển model chế độ làm việc sang: {selected_model}")
        self.update_metrics_display()
        self.on_input_text_changed()

    def update_metrics_display(self) -> None:
        selected_model = self.model_combo.currentText()
        config = MODEL_LIMITS[selected_model]
        
        available_key_info = self.database_manager.get_available_api_key()
        if not available_key_info:
            self.label_rpd.setText("RPD (Ngày): Chưa có Key")
            self.label_rpm.setText("RPM (Phút): Chưa có Key")
            self.label_tpm.setText("TPM (Phút): Chưa có Key")
            return

        api_key_id = available_key_info["id"]
        current_rpm, current_tpm, current_rpd = self.database_manager.get_current_rate_limits(
            api_key_id=api_key_id,
            model_name=selected_model
        )

        if config["skip_request_count"]:
            self.label_rpd.setText("RPD (Ngày): Bỏ qua (Agent)")
            self.label_rpm.setText(f"RPM (Phút): N/A (Limit {config['rpm']})")
        else:
            self.label_rpd.setText(f"RPD (Ngày): {current_rpd:,} / {config['rpd']:,}")
            self.label_rpm.setText(f"RPM (Phút): {current_rpm} / {config['rpm']}")

        self.label_tpm.setText(f"TPM (Phút): {current_tpm:,} / {config['tpm']:,}")

    def load_sessions(self) -> None:
        self.session_list.clear()
        sessions = self.database_manager.get_all_sessions()
        for session_item in sessions:
            list_item = QListWidgetItem(session_item["session_name"])
            list_item.setData(Qt.UserRole, session_item["id"])
            self.session_list.addItem(list_item)

        if sessions and self.current_session_id is None:
            self.current_session_id = sessions[0]["id"]
            self.load_current_session_messages()
        
        app_logger.info(f"Đã nạp {len(sessions)} session từ CSDL.")

    def create_new_session(self) -> None:
        session_name = f"Session {self.session_list.count() + 1}"
        session_id = self.database_manager.create_session(session_name)
        self.current_session_id = session_id
        app_logger.info(f"Tạo session mới thành công. ID: {session_id}, Tên: '{session_name}'")
        self.load_sessions()
        self.load_current_session_messages()

    def on_session_selected(self, item: QListWidgetItem) -> None:
        self.current_session_id = item.data(Qt.UserRole)
        app_logger.info(f"Người dùng chọn Session ID: {self.current_session_id}")
        self.load_current_session_messages()

    def load_current_session_messages(self) -> None:
        self.chat_display.clear()
        if not self.current_session_id:
            return
        messages = self.database_manager.get_session_messages(self.current_session_id)
        for message_item in messages:
            sender_label = "MÀY" if message_item["role"] == "user" else "BOT"
            self.chat_display.append(f"<b>[{sender_label}]:</b>\n{message_item['content']}\n")

    def open_key_manager(self) -> None:
        app_logger.info("Mở cửa sổ Quản lý API Key.")
        dialog = ApiKeyManagerDialog(self.database_manager, self)
        dialog.exec()
        self.update_metrics_display()

    def open_global_context_manager(self) -> None:
        app_logger.info("Mở cửa sổ Quản lý Ngữ cảnh chung (Global Context).")
        dialog = GlobalContextDialog(self.database_manager, self)
        dialog.exec()

    def send_message(self) -> None:
        if not self.current_session_id:
            self.create_new_session()

        raw_text = self.input_text.toPlainText().strip()
        if not raw_text:
            return

        selected_mode = self.model_combo.currentText()
        config = MODEL_LIMITS[selected_mode]

        available_key_info = self.database_manager.get_available_api_key()
        if not available_key_info:
            app_logger.error("Không thể gửi tin nhắn: Chưa cấu hình API Key trong CSDL.")
            QMessageBox.warning(self, "Lỗi", "Vui lòng thêm ít nhất một API Key trong phần Quản Lý API Keys!")
            return

        api_key_id = available_key_info["id"]

        if self.compress_checkbox.isChecked():
            prompt_text = ContextOptimizer.compress_code(raw_text)
            app_logger.info("Đã áp dụng tối ưu nén code (xóa comment & dòng trống).")
        else:
            prompt_text = raw_text

        input_token_estimate = self.estimate_tokens(prompt_text)
        app_logger.info(
            f"Chuẩn bị gửi prompt đến Model '{selected_mode}' | Session ID: {self.current_session_id} | "
            f"Ước tính Input Tokens: {input_token_estimate}"
        )

        self.database_manager.log_model_request(
            api_key_id=api_key_id,
            model_name=selected_mode,
            input_tokens=input_token_estimate,
            output_tokens=0,
            total_tokens=input_token_estimate,
            is_agent_request=config["skip_request_count"]
        )

        temperature_val = self.temp_spinbox.value()
        self.database_manager.add_message(
            session_identifier=self.current_session_id,
            role_name="user",
            message_content=prompt_text,
            prompt_tokens=input_token_estimate,
            response_tokens=0,
            total_tokens=input_token_estimate,
            model_name=selected_mode,
            api_key_id=api_key_id,
            temperature=temperature_val
        )

        self.chat_display.append(f"<b>[MÀY]:</b>\n{prompt_text}\n")
        self.input_text.clear()

        history_messages = self.database_manager.get_session_messages(self.current_session_id)

        self.send_button.setEnabled(False)
        self.status_label.setText("Trạng thái: Đang gửi API và xử lý...")
        self.update_metrics_display()

        self.worker_thread = ApiWorker(
            self.api_service, 
            prompt_text, 
            history_messages[:-1], 
            selected_mode,
            temperature_val
        )
        self.worker_thread.finished_signal.connect(self.on_api_success)
        self.worker_thread.error_signal.connect(self.on_api_error)
        self.worker_thread.start()

    def on_api_success(self, response_text: str, used_model: str, token_count: int) -> None:
        selected_mode = self.model_combo.currentText()
        config = MODEL_LIMITS[selected_mode]
        available_key_info = self.database_manager.get_available_api_key()
        api_key_id = available_key_info["id"] if available_key_info else 1
        temperature_val = self.temp_spinbox.value()

        app_logger.info(
            f"Gọi API thành công | Model thực tế: {used_model} | Output Tokens: {token_count}"
        )

        if token_count > 0:
            self.database_manager.log_model_request(
                api_key_id=api_key_id,
                model_name=selected_mode,
                input_tokens=0,
                output_tokens=token_count,
                total_tokens=token_count,
                is_agent_request=config["skip_request_count"]
            )

        self.database_manager.add_message(
            session_identifier=self.current_session_id,
            role_name="model",
            message_content=response_text,
            prompt_tokens=0,
            response_tokens=token_count,
            total_tokens=token_count,
            model_name=used_model,
            api_key_id=api_key_id,
            temperature=temperature_val
        )

        self.chat_display.append(f"<b>[BOT ({used_model})]:</b>\n{response_text}\n")
        self.status_label.setText(
            f"Trạng thái: Hoàn thành | Model: {used_model} | Tokens lượt này: {token_count}"
        )
        self.send_button.setEnabled(True)
        self.update_metrics_display()

    def on_api_error(self, error_message: str) -> None:
        app_logger.error(f"Xảy ra lỗi API trong quá trình xử lý: {error_message}")
        QMessageBox.critical(self, "Lỗi API", error_message)
        self.status_label.setText("Trạng thái: Lỗi khi gọi API!")
        self.send_button.setEnabled(True)
        self.update_metrics_display()

    def attach_files_action(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn tối đa 15 file mã nguồn",
            "",
            "All Files (*);;Python (*.py);;C/C++ (*.c *.cpp *.h *.hpp)"
        )
        if not file_paths:
            return

        if len(file_paths) > 15:
            app_logger.info(f"Người dùng chọn {len(file_paths)} file (>15 file). Cắt lấy 15 file đầu.")
            QMessageBox.information(
                self, 
                "Thông báo", 
                "Mày chọn quá 15 file. Chương trình sẽ chỉ lấy đúng 15 file đầu tiên."
            )

        formatted_text, loaded_count = FileLoader.load_files_list(file_paths, max_files=15)
        current_input = self.input_text.toPlainText()
        
        new_input_text = f"{current_input}\n\n[CONTEXT TỪ {loaded_count} FILE ĐƯỢC ĐÍNH KÈM]:\n{formatted_text}"
        self.input_text.setPlainText(new_input_text.strip())
        app_logger.info(f"Đã đính kèm {loaded_count} file mã nguồn vào khung nhập.")
        self.status_label.setText(f"Trạng thái: Đã đính kèm {loaded_count} file vào khung nhập.")

    def attach_folder_action(self) -> None:
        selected_mode = self.model_combo.currentText()
        if selected_mode != "Agent Antigravity":
            app_logger.error(f"Cố gắng đọc Folder Project ở mode không cho phép: '{selected_mode}'. Từ chối.")
            QMessageBox.warning(
                self, 
                "Không cho phép", 
                "Tính năng đọc toàn bộ Folder Project chỉ dành riêng cho Agent Antigravity để tránh tràn token limit của model thường!"
            )
            return

        directory_path = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục dự án (Dành cho Agent Antigravity)"
        )
        if not directory_path:
            return

        formatted_text, loaded_count = FileLoader.load_directory_recursive(directory_path, max_files=200)
        current_input = self.input_text.toPlainText()

        new_input_text = f"{current_input}\n\n[CONTEXT TOÀN BỘ FOLDER PROJECT ({loaded_count} files)]:\n{formatted_text}"
        self.input_text.setPlainText(new_input_text.strip())
        app_logger.info(f"Đã quét đệ quy thành công {loaded_count} file từ thư mục '{directory_path}'.")
        self.status_label.setText(f"Trạng thái: Đã quét và đính kèm {loaded_count} file từ folder.")