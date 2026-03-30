import csv
import time
import queue
import threading
import os
from datetime import datetime
from ctypes import * 
from .definitions import sMessageFromAppTTDD, sMessageSendtoApp

# Lớp LoggerWorker chạy nền để ghi dữ liệu ra file CSV
class LoggerWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.running = False
        self.session_id = None
        
        # Cấu hình các file CSV (quản lý file handle)
        self.csv_files = {}    # Key: direction (chiều gửi/nhận), Value: file handle
        self.csv_writers = {}  # Key: direction, Value: object csv.writer
        self.file_metrics = {} # Key: direction, Value: {'bytes': 0, 'index': 1}
        
        # Giới hạn mỗi file log tối đa 20MB để cho dễ mở, không bị treo máy
        self.MAX_FILE_SIZE = 20 * 1024 * 1024 
        
        if not os.path.exists("logs"):
            os.makedirs("logs")

    def log_packet(self, direction, raw_data):
        # Chỉ đẩy vào hàng đợi nếu logger đang chạy (có session_id cụ thể)
        if self.session_id:
            self.queue.put((time.time(), direction, bytes(raw_data)))

    def log_text(self, msg):
        """(Đã bỏ qua) Mình tạm tắt logic ghi log text để tối ưu hiệu năng."""
        pass

    def start_session(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"[LOGGER] Session Started: {self.session_id}")

    def stop_session(self):
        print("[LOGGER] Yêu cầu dừng ghi log Session...")
        self.session_id = None
        self._close_all_files()

    def _close_all_files(self):
        directions = list(self.csv_files.keys())
        for d in directions:
            f = self.csv_files.pop(d, None)
            if f:
                try: f.close()
                except: pass
            self.csv_writers.pop(d, None)
            self.file_metrics.pop(d, None)

    def _get_csv_writer(self, direction, headers):
        # Khởi tạo thông số đếm nếu chiều dữ liệu này là lần đầu xuất hiện
        if direction not in self.file_metrics:
            self.file_metrics[direction] = {'bytes': 0, 'index': 1}

        # Lấy kích thước hiện tại của file (tính bằng byte)
        current_bytes = self.file_metrics[direction]['bytes']
        
        # Mình quyết định xoay vòng file (tạo file mới) nếu:
        # File chứa hướng dữ liệu này chưa được mở HOẶC file hiện tại đã phình to quá giới hạn
        if direction not in self.csv_files or current_bytes > self.MAX_FILE_SIZE:
            # Đóng file cũ (nếu có)
            if direction in self.csv_files:
                try: self.csv_files[direction].close()
                except: pass
                self.file_metrics[direction]['index'] += 1
                self.file_metrics[direction]['bytes'] = 0
            
            # Bắt đầu mở file mới và đánh số thứ tự (index) tăng dần
            idx = self.file_metrics[direction]['index']
            fname = f"logs/Session_{self.session_id}_{direction}_{idx:03d}.csv"
            
            try:
                f = open(fname, 'w', newline='', encoding='utf-8')
                writer = csv.writer(f)
                
                # Ghi ngay dòng tiêu đề trước (Gồm Timestamp + Tất cả các trường dữ liệu)
                full_header = ['timestamp'] + headers
                writer.writerow(full_header)
                f.flush()
                
                self.csv_files[direction] = f
                self.csv_writers[direction] = writer
                self.file_metrics[direction]['bytes'] = f.tell()
                print(f"[LOGGER] Created: {fname}")
                
            except Exception as e:
                print(f"[LOGGER ERROR] Failed to create {fname}: {e}")
                return None, None

        return self.csv_files[direction], self.csv_writers[direction]

    def _flatten_struct(self, obj, prefix=""):
        fields = {}
        for field_desc in obj._fields_:
            field_name = field_desc[0]
            field_type = field_desc[1]
            val = getattr(obj, field_name)
            key = f"{prefix}{field_name}"
            
            if issubclass(field_type, Structure):
                fields.update(self._flatten_struct(val, prefix=f"{key}_"))
            elif issubclass(field_type, Array):
                try:
                    str_val = ",".join([f"{x:.2f}" if isinstance(x, float) else str(x) for x in val])
                    fields[key] = str_val
                except:
                    fields[key] = str(val)
            else:
                fields[key] = val
        return fields

    def run(self):
        self.running = True
        
        while self.running:
            try:
                # Đợi 0.1 giây để lấy dữ liệu, nếu không có thì nhường CPU chứ đừng treo luồng (yield)
                item = self.queue.get(timeout=0.1)
                self._process_single_item(item)
            except queue.Empty:
                pass
            except Exception as e:
                print(f"[LOGGER CRIT ERROR]: {e}")

        # Dọn dẹp: Đóng hết file khi thoát để tránh thất thoát dữ liệu
        self._close_all_files()

    def _process_single_item(self, item):
        # Kiểm tra an toàn: Đề phòng trường hợp luồng bị dừng ngang hông, không có session_id
        if not self.session_id:
            return

        ts, direction, bytes_data = item
        dt_object = datetime.fromtimestamp(ts)
        ts_readable = dt_object.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Logic giải mã dữ liệu bytes thành Struct
        struct_type = None
        if direction == "TX":
            struct_type = sMessageFromAppTTDD
        elif direction == "RX":
            struct_type = sMessageSendtoApp
        
        if not struct_type:
            return

        struct_size = sizeof(struct_type)
        if len(bytes_data) >= struct_size:
            valid_bytes = bytes_data[:struct_size]
        else:
            valid_bytes = bytes_data + b'\x00' * (struct_size - len(bytes_data))

        buff = create_string_buffer(valid_bytes, struct_size)
        struct_obj = cast(buff, POINTER(struct_type)).contents
        
        flat_data = self._flatten_struct(struct_obj)
        if not flat_data: return

        headers = list(flat_data.keys())
        values = list(flat_data.values())

        _, writer = self._get_csv_writer(direction, headers)
        
        if writer:
            try:
                writer.writerow([ts_readable] + values)
                
                f = self.csv_files[direction]
                # Hiện tại mình update dung lượng sau mỗi lần ghi, hơi tốn I/O xíu nhưng chắc cốp
                self.file_metrics[direction]['bytes'] = f.tell() 
                
            except Exception as e:
                 print(f"[LOGGER WRITE ERROR] {direction}: {e}")

    def stop(self):
        self.running = False
        self.join()