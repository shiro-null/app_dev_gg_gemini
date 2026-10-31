PRAGMA foreign_keys = ON;

-- 1. Quản lý danh sách API Keys
CREATE TABLE IF NOT EXISTS project_api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key TEXT UNIQUE NOT NULL,
    note TEXT,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP
);

-- 2. Lưu cài đặt chung của ứng dụng (Theme, Font, Option mặc định)
CREATE TABLE IF NOT EXISTS app_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL
);

-- 3. Bộ nhớ dài hạn / Context riêng của người dùng
CREATE TABLE IF NOT EXISTS user_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_category TEXT NOT NULL,
    memory_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Quản lý Mẫu System Prompt (Vai diễn AI)
CREATE TABLE IF NOT EXISTS system_prompt_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Quản lý Phiên Hội thoại (Lưu cấu hình riêng từng tab chat)
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_name TEXT NOT NULL,
    selected_model TEXT DEFAULT 'Gemma 4 26B',
    temperature REAL DEFAULT 0.7,
    system_prompt TEXT,
    is_pinned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Quản lý Chi tiết Tin nhắn (Lưu Token, Model và Key đã dùng cho prompt này)
CREATE TABLE IF NOT EXISTS session_messages (
    session_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    role TEXT NOT NULL,                          -- 'user' hoặc 'model'
    content TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,             -- Token lượt hỏi
    response_tokens INTEGER DEFAULT 0,           -- Token lượt đáp
    total_tokens INTEGER DEFAULT 0,              -- Tổng token
    model_name TEXT,                             -- Model thực tế xử lý
    api_key_id INTEGER,                          -- ID của API Key đã xài
    temperature REAL,                            -- Nhiệt độ thiết lập
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, message_id),
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (api_key_id) REFERENCES project_api_keys(id) ON DELETE SET NULL
) WITHOUT ROWID;

-- 7. Quản lý File & Folder đính kèm theo từng tin nhắn
CREATE TABLE IF NOT EXISTS session_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT,
    file_extension TEXT,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id, message_id) REFERENCES session_messages(session_id, message_id) ON DELETE CASCADE
);

-- 8. Lịch sử Log Request phục vụ khôi phục Rate Limit (RPM, TPM, RPD)
CREATE TABLE IF NOT EXISTS model_request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL,                 -- Key chịu limit
    model_name TEXT NOT NULL,                    -- Model chịu limit
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    is_agent_request INTEGER DEFAULT 0,          -- 1 nếu là Agent (không đếm request), 0 nếu là model thường
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_key_id) REFERENCES project_api_keys(id) ON DELETE CASCADE
);

-- 9. Kho lưu trữ Code Snippet ghim lại
CREATE TABLE IF NOT EXISTS pinned_code_snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    title TEXT NOT NULL,
    language TEXT NOT NULL,                      -- 'cpp', 'python', 'sql', 'bash'...
    code_content TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(id) ON DELETE SET NULL
);

-- 10. Tóm tắt Session (Nén context)
CREATE TABLE IF NOT EXISTS session_summaries (
    session_id INTEGER PRIMARY KEY,
    summary_text TEXT NOT NULL,
    last_summarized_message_id INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(id) ON DELETE CASCADE
);

-- 11. Bảng Tìm kiếm toàn văn (Full-Text Search FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS session_messages_fts USING fts5(
    session_id UNINDEXED,
    message_id UNINDEXED,
    content
);

-- 12. Quản lý danh sách File Context Picker theo Session (Kế bên khung Chat)
CREATE TABLE IF NOT EXISTS session_file_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(id) ON DELETE CASCADE
);

-- Triggers tự động đồng bộ Full-Text Search
CREATE TRIGGER IF NOT EXISTS trg_session_messages_after_insert
AFTER INSERT ON session_messages
BEGIN
    INSERT INTO session_messages_fts(session_id, message_id, content)
    VALUES (NEW.session_id, NEW.message_id, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS trg_session_messages_after_delete
AFTER DELETE ON session_messages
BEGIN
    DELETE FROM session_messages_fts
    WHERE session_id = OLD.session_id AND message_id = OLD.message_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_conversation_sessions_after_delete
AFTER DELETE ON conversation_sessions
BEGIN
    DELETE FROM session_messages_fts WHERE session_id = OLD.id;
END;