Mày nghĩ ra cái hướng này quá chuẩn luôn! Đúng chất làm tool cho dân kỹ thuật: **trao quyền kiểm soát tuyệt đối cho người dùng, minh bạch rủi ro và không tự ý đưa ra quyết định thay họ.**

---

### 1. Giải pháp Tóm tắt: Cho chọn Chế độ + Cảnh báo Ngưỡng + Nút Di cư

Tạo thẳng trong Cài đặt (Settings) hoặc Cấu hình Session 3 lựa chọn tóm tắt rõ ràng:

* **Chế độ 1: Tóm tắt ghi đè (Rolling Summary)**
* *Cơ chế:* Cứ quá $N$ prompt thì gom `[Tóm tắt cũ + Tin nhắn mới]` thành 1 bản tóm tắt mới duy nhất.
* *Cảnh báo hậu quả:* "Có nguy cơ làm mờ/mất chi tiết kỹ thuật sâu (tên biến, edge case) sau nhiều lần tóm tắt. Nếu câu thoại quá dài, request tóm tắt có thể xịt do vượt giới hạn Input Token của model tóm tắt."


* **Chế độ 2: Tóm tắt cộng dồn (Incremental Summary)**
* *Cơ chế:* Cứ $N$ prompt thì tạo thêm 1 block tóm tắt mới và nối chuỗi dồn lại.
* *Cảnh báo hậu quả:* "Không làm mất chi tiết cũ nhưng sẽ làm phình dung lượng Token theo thời gian. Đến một lúc nào đó Session sẽ vượt quá trần Token của model chat và không thể gửi thêm tin nhắn."


* **Chế độ 3: Tắt tóm tắt (Chỉ dùng Cửa sổ trượt - Sliding Window)**
* *Cơ chế:* Chỉ gửi $N$ tin nhắn gần nhất lên API.
* *Cảnh báo hậu quả:* "Giữ nguyên 100% độ chính xác ngữ cảnh gần nhất, nhưng AI sẽ hoàn toàn 'quên' các tin nhắn nằm ngoài cửa sổ trượt."



**Biện pháp Báo trước & Di cư (Migration System):**

* **Cảnh báo ngưỡng token:** Lượt chat nào cũng tính tổng Token (Prompt + History). Khi số Token đạt mức 80% limit của Model, UI hiển thị một banner màu vàng: *"Session này đã chiếm 80% giới hạn Token! Bạn nên di cư sang Session mới."*
* **Nút "Nhân bản / Di cư Session" (Clone to New Session):** Người dùng bấm một cái, hệ thống tự động tạo Session mới, trích xuất lại các thông tin quan trọng nhất hoặc cho người dùng chọn câu thoại muốn giữ lại để mang sang nhà mới làm việc tiếp.

---

### 2. Quản lý File kiểu VS Code / Cursor: File Context Picker

Ý tưởng này giải quyết dứt điểm 100% bài toán lạm phát token và khỏi cần tóm tắt file lan man.

* **Tầng Cơ sở dữ liệu (SQLite):**
Tạo một bảng cực nhẹ `session_file_references` chỉ lưu đường dẫn và thông tin cơ bản:
* `id`: Khóa chính
* `session_id`: ID của session
* `file_path`: Đường dẫn tuyệt đối của file trên máy người dùng
* `file_name`: Tên file hiển thị
* `added_at`: Thời gian thêm file


* **Giao diện UI (File Panel bên cạnh khung Chat):**
* Khi người dùng kéo thả hoặc đính kèm file vào session, đường dẫn được lưu vào bảng `session_file_references`.
* Nằm kế bên hoặc phía trên khung nhập tin nhắn là một danh sách các file đã từng xài trong session này (kèm nút tích Checkbox hoặc dạng thẻ Tag `@file_name`).
* Mặc định khi đính kèm file mới: File đó được tích chọn **[Active]** cho prompt hiện tại.
* Sau khi gửi xong: Tùy người dùng chọn giữ tích hay bỏ tích.


* **Luồng gửi Request API:**
* Khi người dùng bấm Gửi, hệ thống chỉ đọc đống file đang được tích **[Active]** tại thời điểm đó, rút nội dung file ra nhét vào prompt gửi lên API.
* Những file bỏ tích sẽ bị bỏ qua hoàn toàn, không tốn dù chỉ 1 token ngữ cảnh.



Cách này đẩy quyền quyết định và trách nhiệm về phía người dùng, code hệ thống lại cực kỳ sạch, không phải chạy các tác vụ tóm tắt ngầm phức tạp tốn tài nguyên.