# TÀI LIỆU KỸ THUẬT: PHẦN MỀM ĐIỀU KHIỂN HỆ THỐNG RCWS (VRW-V12)

---

## 1. GIỚI THIỆU CHUNG
Phần mềm Điều khiển Hỏa lực (FCS) cho hệ thống RCWS VRW-V12 là ứng dụng giao diện người dùng (GUI) được phát triển trên nền tảng **Python** và **PyQt5**. Phần mềm đóng vai trò trung tâm điều khiển, giám sát và tham số hóa cho Trạm Vũ Khí (Weapon Station).

### Chức năng chính:
- **Điều khiển**: Gửi lệnh quay tầm/hướng, ổn định, bắn (Laser/Cò) tới phần cứng.
- **Giám sát**: Hiển thị thời gian thực các thông số từ cảm biến (Encoder, Gyro, Cảm biến khí tượng, Đạn còn lại).
- **Tham số hóa**: Cài đặt các tham số đạn đạo, lượng sửa, zeroing và cấu hình hệ thống.
- **Mô phỏng**: Tích hợp sẵn Server giả lập (Mock) để phục vụ phát triển và kiểm thử mà không cần phần cứng thật.

---

## 2. YÊU CẦU VÀ CÀI ĐẶT

### Yêu cầu hệ thống
- **Hệ điều hành**: Linux (Ubuntu 20.04 trở lên) hoặc Windows 10/11.
- **Môi trường**: Python 3.8+.
- **Thư viện C++**: GCC/G++ (để biên dịch Mock).

### Cài đặt tự động (Khuyến nghị cho Linux)
Hệ thống đi kèm script tự động cài đặt toàn bộ thư viện và biên dịch các module C++ cần thiết.

1. Mở Terminal tại thư mục dự án.
2. Cấp quyền thực thi và chạy script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   Script sẽ tự động:
   - Cài đặt thư viện Python (`pyqt5`, ...).
   - Biên dịch Server Giả lập (`RCWS_MOCK/mock`).
   - Biên dịch công cụ kiểm tra cấu trúc (`helpers/check_size`).

---

## 3. HƯỚNG DẪN VẬN HÀNH

### Khởi động phần mềm
Chạy lệnh sau tại thư mục gốc:
```bash
python3 main.py
```

### Quy trình kết nối
1. **Nhập địa chỉ IP**:
   - Nhập IP của Trạm vũ khí thật hoặc `127.0.0.1` nếu chạy mô phỏng.
2. **Bấm nút "KẾT NỐI"**:
   - Nút sẽ chuyển sang màu **ĐỎ** (trạng thái chờ/đang kết nối).
   - Phần mềm sẽ gửi gói tin `HANDSHAKE` liên tục để chào tay với thiết bị.
3. **Trạng thái kết nối**:
   - Khi nhận được dữ liệu phản hồi hợp lệ:
     - Đèn trạng thái UDP sẽ chuyển **XANH**.
     - Đèn trạng thái GCU sẽ chuyển **XANH** (nếu bit kết nối GCU = 1) hoặc **ĐỎ** (nếu GCU báo lỗi/chưa sẵn sàng).
   - **Đồng bộ tự động**: Ngay khi kết nối thành công, tất cả các ô nhập liệu (Lượng sửa, Tham số đạn...) trên giao diện sẽ tự động được điền giá trị hiện tại của hệ thống.

### Giám sát độ trễ (Latency)
- Hệ thống tự động đo thời gian phản hồi từ lúc gửi lệnh đến lúc nhận Echo.
- Kết quả hiển thị trên Console: `COMMAND ECHO LATENCY: 25.40 ms`.

### Nhật ký hoạt động (Logs)
- **Nơi lưu trữ**: Thư mục `logs/`.
- **Database (`.db`)**: Lưu toàn bộ lịch sử gói tin dạng SQLite để tra cứu sau.
- **Text Log (`log_time_....txt`)**: Ghi chi tiết nội dung từng gói tin TX/RX dạng văn bản để debug.

---

## 4. CẤU TRÚC DỰ ÁN

| Đường dẫn | Mô tả chức năng |
| :--- | :--- |
| **main.py** | Điểm khởi chạy chính của chương trình. |
| **setup.sh** | Script cài đặt môi trường và biên dịch module C++. |
| **config.py** | Chứa các hằng số cấu hình (IP, Port, Màu sắc UI, Timeout). |
| **core/** | **Module Xử lý Logic lõi**: |
| ├── comms.py | `UdpWorker`: Quản lý luồng gửi/nhận UDP, đo độ trễ. |
| ├── definitions.py | Định nghĩa cấu trúc dữ liệu `ctypes` (tương thích C++). |
| ├── logger.py | Module ghi nhật ký vào SQLite và file Text. |
| **ui/** | **Module Giao diện**: |
| ├── app_window.py | Cửa sổ chính, menu sidebar. |
| ├── tabs/ | Logic xử lý từng tab chức năng (Điều khiển, Login). |
| ├── components.py | Các Widget tùy biến (Ô nhập liệu, Hàng hiển thị). |
| **helpers/** | **Công cụ hỗ trợ**: |
| ├── check_size.c | Mã nguồn C để kiểm tra kích thước cấu trúc (Struct alignment). |
| **RCWS_MOCK/** | **Server Giả lập**: |
| ├── mock.cpp | Mã nguồn C++ mô phỏng hành vi của Trạm vũ khí. |
| ├── config.h | File cấu hình struct dùng chung cho Mock. |

---

## 5. GIAO THỨC TRUYỀN THÔNG (PROTOCOL)

### Cơ chế UDP
- **Cổng Giao diện (App Port)**: Ngẫu nhiên (Ephemeral Port).
- **Cổng Thiết bị (Station Port)**: 12345 (Cấu hình trong `config.py`).
- **Tần suất**:
  - Gửi lệnh (TX): Gửi khi người dùng thao tác hoặc định kỳ (Heartbeat).
  - Nhận dữ liệu (RX): Liên tục (~10-50Hz tùy thiết bị).

### Cấu trúc gói tin
Dữ liệu được đóng gói dạng **Binary Struct** (C-style structure) với căn chỉnh 1-byte (`pack=1`).

1. **Gói tin Điều khiển (App -> Station)**:
   - Bao gồm: Thông số bắn, Trạng thái nút bấm, Tham số GCU.
   - Kèm theo trường `Alpha` (4 bytes) và `Checksum` (1 byte) ở cuối.

2. **Gói tin Trạng thái (Station -> App)**:
   - Bao gồm: Toàn bộ trạng thái thiết bị, giá trị Echo của lệnh vừa nhận.

### Cơ chế An toàn
- **Checksum**: Byte cuối cùng của mỗi gói tin là tổng (Sum) của toàn bộ các byte trước đó. Gói tin sai Checksum sẽ bị loại bỏ.
- **Handshake**: Đảm bảo thiết bị nhận diện đúng địa chỉ IP/Port của máy điều khiển trước khi gửi dữ liệu về.
- **Watchdog UI**: Nếu không nhận được dữ liệu quá 1 giây, giao diện sẽ báo "Mất kết nối".

---

## 6. HƯỚNG DẪN PHÁT TRIỂN & MỞ RỘNG

### Thêm một tham số mới vào hệ thống
Quy trình chuẩn để thêm một trường dữ liệu (ví dụ: `float new_param`):

1. **Phía Firmware/Mock (C++)**:
   - Thêm `float new_param;` vào struct tương ứng trong `config.h`.
   - Biên dịch lại Mock (chạy `./setup.sh`).

2. **Kiểm tra Kích thước (Alignment)**:
   - Cập nhật `helpers/check_size.c` để in ra kích thước struct mới.
   - Chạy `./helpers/check_size` để lấy tổng số byte.

3. **Phía Python (Core)**:
   - Mở `core/definitions.py`.
   - Thêm `("new_param", c_float)` vào class `Structure` tương ứng.
   - **Lưu ý**: Thứ tự và kiểu dữ liệu phải khớp tuyệt đối 100% với C++.

4. **Phía Giao diện (UI)**:
   - Mở `ui/tabs/control_tab.py`.
   - Thêm hiển thị: dùng `self.lbl_row(...)`.
   - Thêm điều khiển: dùng `self.add_inp_grid(...)`.
   - Map dữ liệu: Thêm key mapping vào `update_ui` hoặc `sync_inputs`.

### Debugging
- Kiểm tra file log tại `logs/log_time_....txt` để xem nội dung hex/giải mã của gói tin.
- Nếu thấy hiện tượng lệch dữ liệu (Mismatch), hãy dùng tool `check_size` để so sánh kích thước struct giữa Python và C++.