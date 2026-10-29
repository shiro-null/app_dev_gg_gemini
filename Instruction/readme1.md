# Phân tích dự án `app_dev_gg_gemini`

## 1. Tổng quan

`app_dev_gg_gemini` là một ứng dụng desktop viết bằng Python và PySide6, được xây dựng để giao tiếp với Google Gemini Cloud. Ứng dụng có giao diện trò chuyện, lưu lịch sử vào SQLite, hỗ trợ nhiều API key, gửi kèm tệp hoặc thư mục mã nguồn, và tối ưu ngữ cảnh trước khi gửi yêu cầu đến Gemini.

Phân tích này được thực hiện bằng cách đọc tĩnh mã nguồn, đối chiếu các lớp giao diện, service, provider, worker, cấu trúc cơ sở dữ liệu và các repository. Không có mã nguồn ứng dụng nào bị thay đổi trong quá trình phân tích.

## 2. Các chức năng hiện có

### 2.1. Giao diện trò chuyện

- Khởi động ứng dụng từ `main.py`.
- Hiển thị cửa sổ làm việc chính bằng PySide6.
- Cho phép người dùng nhập câu hỏi và nhận câu trả lời từ Gemini.
- Hiển thị lịch sử tin nhắn trong từng phiên trò chuyện.
- Tạo, chọn và tải lại các phiên chat đã lưu.
- Chạy yêu cầu API trong worker riêng để tránh làm treo giao diện.

### 2.2. Quản lý phiên và lịch sử

- Lưu phiên trò chuyện vào SQLite.
- Lưu tin nhắn người dùng và tin nhắn trả lời.
- Lưu thời gian tạo, cập nhật và một số thông tin token.
- Có cơ chế tìm kiếm trong dữ liệu lịch sử.
- Schema đã chuẩn bị thêm bảng cho tóm tắt phiên, tệp đính kèm, đoạn mã được ghim và tìm kiếm toàn văn.

### 2.3. Quản lý Google Gemini API key

- Cho phép lưu nhiều API key.
- Có giao diện quản lý key.
- Có cơ chế thử lần lượt nhiều key khi gửi yêu cầu.
- Có thống kê hoặc ghi log liên quan đến số lần gọi, RPM/RPD và giới hạn sử dụng.

### 2.4. Cấu hình Gemini

- Cho phép chọn model từ giao diện.
- Cho phép chọn nhiệt độ (temperature).
- Có định mức token và thông tin giới hạn theo model.
- Có cấu hình system instruction dùng chung.
- Có bộ nhớ dài hạn cho thông tin người dùng.

### 2.5. Gửi tệp và thư mục dự án

- Cho phép chọn tệp riêng lẻ.
- Cho phép chọn thư mục dự án.
- Có bộ lọc phần mở rộng tệp.
- Bỏ qua một số thư mục không cần thiết khi quét dự án.
- Đọc nội dung tệp rồi đưa vào prompt gửi tới Gemini.

### 2.6. Tối ưu ngữ cảnh mã nguồn

- Có module loại bỏ dòng trống và một phần comment.
- Giảm kích thước nội dung mã nguồn trước khi gửi.
- Có mục tiêu giảm số token sử dụng khi gửi các dự án lớn.

### 2.7. Lưu trữ và tìm kiếm dữ liệu

Schema SQLite hiện có các nhóm dữ liệu chính:

- Phiên trò chuyện.
- Tin nhắn.
- API key.
- Bộ nhớ người dùng.
- Log request.
- Tóm tắt phiên.
- Tệp đính kèm.
- Đoạn mã được ghim.
- Bảng tìm kiếm toàn văn.

Tuy nhiên, không phải tất cả bảng đã được nối hoàn chỉnh vào giao diện hoặc luồng xử lý hiện tại.

## 3. Kiến trúc và luồng xử lý chính

Luồng sử dụng chính hiện tại có thể khái quát như sau:

1. `main.py` tạo `QApplication` và mở `MainWindow`.
2. `MainWindow` nhận nội dung người dùng, lịch sử chat, model, temperature và dữ liệu tệp.
3. `ApiWorker` chạy yêu cầu ở worker riêng.
4. `GeminiApiService` xử lý lớp service trung gian.
5. `GeminiProvider` tạo client Gemini, chuẩn bị lịch sử và gửi request.
6. Kết quả được trả về giao diện.
7. Nội dung tin nhắn và request log được lưu vào SQLite thông qua `DatabaseManager`.

Ngoài luồng trên, dự án vẫn còn các repository và worker cũ sử dụng thiết kế khác. Đây là nguyên nhân chính tạo ra nhiều mâu thuẫn giữa các module.

## 4. Các lỗi logic và lỗi cơ bản

### 4.1. Lỗi nghiêm trọng: gọi sai constructor của `GeminiProvider`

`GeminiProvider` hiện nhận một đối tượng repository API key, nhưng `GeminiApiService` lại khởi tạo provider bằng các tham số `api_key` và `model_name`.

Kết quả là luồng gửi tin nhắn có thể dừng ngay trước khi gọi Gemini với lỗi `TypeError`. Đây là lỗi tích hợp nghiêm trọng nhất và khiến chức năng chính của ứng dụng không đáng tin cậy.

**Hướng sửa:**

- Chọn một thiết kế dependency duy nhất.
- Hoặc sửa service để truyền đúng `ApiKeyRepository`.
- Hoặc sửa provider để nhận trực tiếp API key và model theo một hợp đồng rõ ràng.
- Đồng bộ chữ ký constructor và các phương thức giữa service, provider, worker và UI.

### 4.2. Tên model giữa UI và provider không đồng nhất

Giao diện có các lựa chọn như `Gemma 4 26B` và `Gemma 4 31B`, trong khi provider lại ánh xạ các tên khác như `gemma 26B` và `gemma 30B`.

Khi tên không khớp, model được chọn có thể không được ánh xạ đúng và bị rơi về model mặc định Flash. Người dùng nhìn thấy một model nhưng request thực tế có thể chạy bằng model khác.

**Hướng sửa:**

- Tạo một bảng cấu hình model duy nhất.
- Dùng ID model thực tế làm giá trị nội bộ.
- Dùng label riêng cho UI.
- Không để service và provider tự định nghĩa hai bảng ánh xạ độc lập.

### 4.3. Temperature không được truyền đầy đủ

UI và `ApiWorker` có nhận giá trị temperature, nhưng `GeminiApiService.send_message()` không nhận hoặc không chuyển giá trị này xuống provider.

Do đó, dù người dùng chọn temperature khác, provider vẫn có thể sử dụng giá trị mặc định `0.7`.

**Hướng sửa:**

Truyền temperature xuyên suốt theo chuỗi:

`MainWindow -> ApiWorker -> GeminiApiService -> GeminiProvider -> GenerateContentConfig`

### 4.4. Ghi log request có thể bị trùng

Request được ghi trước khi gọi API, sau đó kết quả thành công lại được ghi thêm. Điều này có thể:

- Đếm một lần gửi thành hai request.
- Làm sai thống kê RPM/RPD.
- Làm sai tổng token.
- Gây khó khăn khi kiểm tra lịch sử lỗi.

**Hướng sửa:**

- Mỗi lần gọi API chỉ tạo một bản ghi request.
- Bản ghi được cập nhật từ trạng thái `pending` sang `success` hoặc `failed`.
- Ghi rõ thời điểm, model, key thực tế, token và lỗi.

### 4.5. Không xác định đúng API key đã thành công

Provider có thể thử nhiều API key, nhưng kết quả trả về không chứa rõ key nào đã thực sự thành công. UI vì vậy có thể ghi usage cho key ban đầu thay vì key được dùng thành công sau khi xoay vòng.

**Hướng sửa:**

Kết quả provider nên trả về một cấu trúc thống nhất, gồm tối thiểu:

- Nội dung phản hồi.
- Model thực tế.
- API key ID đã thành công.
- Token usage.
- Thời gian xử lý.

### 4.6. Fallback API key ID bằng giá trị cố định

Có đoạn xử lý dùng `api_key_id = 1` khi không xác định được key. Đây là fallback không an toàn vì:

- ID 1 có thể không tồn tại.
- Có thể ghi nhầm usage sang key khác.
- Có thể vi phạm khóa ngoại.
- Làm dữ liệu thống kê sai mà không báo rõ nguyên nhân.

**Hướng sửa:**

- Không dùng ID cố định.
- Nếu thiếu key ID thì trả lỗi rõ ràng hoặc lưu `NULL` khi schema cho phép.
- Kiểm tra trạng thái key trước khi ghi log.

### 4.7. Retry quá rộng đối với mọi exception

Provider có xu hướng thử key tiếp theo với mọi exception. Điều này không phù hợp vì các lỗi như sai model, sai request format, lỗi cấu hình hoặc lỗi lập trình không thể được giải quyết bằng cách đổi API key.

**Hướng sửa:**

- Chỉ retry với lỗi có khả năng tạm thời, chẳng hạn 429, timeout hoặc lỗi dịch vụ tạm thời.
- Dừng ngay với lỗi xác thực, sai model, sai tham số hoặc lỗi dữ liệu.
- Giữ nguyên nguyên nhân gốc trong thông báo lỗi.

### 4.8. Hai hệ thống persistence tồn tại song song

Dự án có:

- `DatabaseManager` là lớp đang được luồng UI sử dụng.
- `DatabaseConnection` cùng các repository cũ như `ApiKeyRepository`, `SessionRepository` và `UserMemoryRepository`.

Hai thiết kế này không hoàn toàn tương thích. Việc duy trì song song dễ dẫn đến sửa một nơi nhưng quên nơi còn lại.

**Hướng sửa:**

- Chọn `DatabaseManager` làm persistence layer chính và chuyển toàn bộ code sang đó; hoặc
- Giữ repository pattern nhưng viết lại `DatabaseManager` theo cùng hợp đồng.
- Sau khi chuyển đổi, loại bỏ hoặc đánh dấu rõ các module cũ không còn dùng.

### 4.9. Repository phiên dùng cột không còn tồn tại

Schema hiện dùng các cột:

- `prompt_tokens`
- `response_tokens`
- `total_tokens`

Trong khi `SessionRepository` cũ lại tham chiếu `token_count`. Nếu repository cũ được gọi, thao tác cơ sở dữ liệu có thể thất bại.

### 4.10. Worker cũ gọi các phương thức không tồn tại

`controller/worker_threads.py` có các dấu hiệu đã lỗi thời:

- Gọi `ContextOptimizer.optimize_chat_context()` nhưng phương thức này không tồn tại.
- Gọi provider với tham số `prompt` và `history`, trong khi provider hiện dùng `prompt_text` và `conversation_history`.

Nếu module này được dùng lại, worker sẽ lỗi do sai tên phương thức hoặc sai chữ ký hàm.

### 4.11. Tệp đính kèm không được lưu đầy đủ vào phiên

Nội dung tệp được chèn trực tiếp vào prompt, nhưng metadata tệp chưa được lưu đầy đủ vào bảng `session_attachments`.

Khi tải lại phiên, người dùng có thể thấy lịch sử tin nhắn nhưng không biết tệp nào đã được dùng. Việc tái hiện một request cũ cũng trở nên khó khăn.

**Hướng sửa:**

- Lưu đường dẫn, tên tệp, loại tệp, kích thước và hash nếu phù hợp.
- Liên kết attachment với session và message.
- Khi tải lại phiên, hiển thị rõ danh sách tệp đã dùng.

### 4.12. Không giới hạn tổng kích thước tệp và số token

File loader có giới hạn số lượng tệp nhưng chưa kiểm soát đầy đủ:

- Tổng số byte.
- Kích thước từng tệp.
- Số token ước tính sau khi ghép prompt.
- Giới hạn context của model.

Một thư mục lớn có thể tạo prompt vượt quá context window, khiến request thất bại hoặc làm chi phí tăng mạnh.

**Hướng sửa:**

- Đặt giới hạn kích thước từng tệp và tổng kích thước.
- Ước tính token trước khi gửi.
- Hiển thị cảnh báo và danh sách tệp bị bỏ qua.
- Ưu tiên tệp theo phần mở rộng hoặc mức độ liên quan.

### 4.13. Xóa comment bằng xử lý chuỗi đơn giản có thể làm hỏng mã

`ContextOptimizer.compress_code()` xử lý các chuỗi `//` theo cách đơn giản. Điều này có thể cắt nhầm:

- URL như `https://example.com`.
- Chuỗi ký tự.
- Nội dung regex.
- Code hợp lệ có chứa `//` không phải comment.

**Hướng sửa:**

- Dùng parser/tokenizer theo ngôn ngữ khi có thể.
- Hoặc chỉ nén ở mức an toàn: bỏ dòng trống và comment cả dòng.
- Không xóa phần còn lại của dòng nếu chưa xác định đó là comment.

### 4.14. Nội dung chat được đưa trực tiếp vào `QTextEdit.append()`

Nếu nội dung phản hồi chứa `<`, `>` hoặc `&`, Qt có thể hiểu đó là HTML. Hậu quả là:

- Nội dung hiển thị sai.
- Một phần text bị ẩn.
- Markup trong câu trả lời làm thay đổi giao diện.

**Hướng sửa:**

- Escape nội dung trước khi đưa vào HTML.
- Hoặc dùng API hiển thị plain text nếu không cần định dạng.
- Nếu cần Markdown, dùng một renderer có kiểm soát và giới hạn HTML được phép.

### 4.15. Các bảng đã chuẩn bị nhưng chưa được nối hoàn chỉnh

Schema có các tính năng có vẻ đang ở trạng thái dở dang hoặc chưa dùng đầy đủ:

- `system_prompt_templates`
- `session_attachments`
- `pinned_code_snippets`
- `session_summaries`
- `session_messages_fts`

Việc có bảng nhưng không có luồng sử dụng rõ ràng làm tăng độ phức tạp và tạo kỳ vọng sai về chức năng.

**Hướng xử lý:**

- Hoàn thiện và viết test cho từng tính năng; hoặc
- Xóa bảng chưa dùng sau khi xác nhận không còn kế hoạch sử dụng.

### 4.16. Thiếu dependency manifest và hướng dẫn cài đặt

README hiện tại chỉ mô tả rất ngắn gọn dự án dùng Google Gemini Cloud. Chưa thấy tài liệu đầy đủ về:

- Phiên bản Python.
- Cách cài PySide6.
- Cách cài `google-genai`.
- Cách cấu hình API key.
- Cách chạy ứng dụng.
- Model được hỗ trợ.
- Các giới hạn tệp và token.

Trong môi trường kiểm tra, `py -3 -m compileall` chạy thành công, nhưng import runtime bị chặn bởi lỗi thiếu package `google`/`google-genai`.

**Hướng sửa:**

- Thêm `requirements.txt` hoặc `pyproject.toml`.
- Ghi rõ phiên bản Python được hỗ trợ.
- Cập nhật README với các bước cài đặt và chạy.
- Có thể thêm file `.env.example` nếu dự án dùng biến môi trường.

## 5. Đánh giá mức độ ưu tiên

### Mức nghiêm trọng - cần sửa trước khi sử dụng

1. Sửa lỗi constructor giữa `GeminiApiService` và `GeminiProvider`.
2. Đồng bộ chữ ký hàm giữa UI, worker, service và provider.
3. Đồng bộ tên model và ID model thực tế.
4. Đảm bảo temperature được truyền đến request Gemini.
5. Sửa cơ chế ghi log để không đếm trùng.
6. Bỏ fallback API key ID cố định.

### Mức cao - cần sửa để ứng dụng ổn định

1. Chỉ retry các lỗi có thể retry.
2. Trả về đúng API key đã thành công.
3. Chọn một persistence layer duy nhất.
4. Sửa repository dùng `token_count`.
5. Sửa hoặc loại bỏ worker cũ.
6. Giới hạn tổng kích thước và token của tệp đính kèm.

### Mức trung bình - cần sửa để đảm bảo chất lượng dữ liệu và UX

1. Lưu metadata tệp vào session.
2. Sửa cách nén code để không làm hỏng nội dung hợp lệ.
3. Escape nội dung chat trước khi hiển thị.
4. Hoàn thiện hoặc loại bỏ các bảng tính năng chưa được nối.
5. Bổ sung dependency manifest và tài liệu cài đặt.

## 6. Kiểm tra đã thực hiện

- Đã kiểm tra cấu trúc và các module chính của dự án.
- Đã đối chiếu luồng `MainWindow -> ApiWorker -> GeminiApiService -> GeminiProvider`.
- Đã đối chiếu schema SQLite với các repository.
- Đã tìm các phương thức, tên tham số và model mapping không đồng nhất.
- Python source đã biên dịch cú pháp thành công bằng:

  ```powershell
  py -3 -m compileall .
  ```

- Chưa kiểm thử request Gemini thực tế vì môi trường hiện tại thiếu package `google-genai`.
- Chưa thay đổi mã nguồn ứng dụng trong quá trình phân tích.

## 7. Kết luận

Dự án đã có nền tảng tương đối đầy đủ cho một ứng dụng chat Gemini desktop: giao diện, phiên chat, SQLite, nhiều API key, file context và tối ưu prompt. Tuy nhiên, hiện trạng chưa đủ ổn định để sử dụng thường xuyên vì luồng gửi request đang có lỗi hợp đồng giữa service và provider, cùng nhiều module cũ không còn khớp với schema và API hiện tại.

Thứ tự nên thực hiện là:

1. Sửa toàn bộ hợp đồng giữa UI, worker, service và provider.
2. Chuẩn hóa model, API key rotation và request logging.
3. Chọn một kiến trúc persistence duy nhất.
4. Thêm giới hạn context và cơ chế lưu attachment.
5. Bổ sung dependency manifest, tài liệu cài đặt và test tự động.

Sau các bước này, ứng dụng mới nên được kiểm thử runtime với Gemini thật hoặc một client mock để xác nhận đầy đủ các trường hợp thành công, hết quota, sai key, sai model, timeout và prompt quá lớn.
