from PyQt5.QtCore import QThread, pyqtSignal
import time
import subprocess
import platform

class IpScannerThread(QThread):
    ip_detected = pyqtSignal(str)

    def __init__(self, target_ip):
        super().__init__()
        self.target_ip = target_ip
        self.running = True

    def run(self):
        # Cấu hình tham số Ping:
        # -c 1: số lượng gói tin là 1
        # -W 1: chờ phản hồi tối đa 1 giây (Linux)
        # Windows dùng biến đổi tương ứng cờ -n 1 và -w 1000 (ms)
        is_win = platform.system().lower() == 'windows'
        cmd_param = ['ping', '-n', '1', '-w', '1000', self.target_ip] if is_win else ['ping', '-c', '1', '-W', '1', self.target_ip]

        while self.running:
            try:
                # Chạy lệnh ping
                # Lệnh bị giữ ở đây tối đa 1 giây do có đặt cờ timeout
                result = subprocess.call(cmd_param, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if result == 0:
                    self.ip_detected.emit(self.target_ip)
                    # Tìm thấy mạng, tạm dừng báo 5 giây, nhưng luôn kiểm tra cờ tắt cập nhật mỗi 0.1 giây
                    self.smart_sleep(5.0)
                else:
                    # Rớt mạng, thử quét lại sau 2 giây
                    self.smart_sleep(2.0)
            except Exception as e:
                print(f"Scanner Error: {e}")
                self.smart_sleep(5.0)

    def smart_sleep(self, duration):
        # Ngủ trễ hệ thống trong khoảng `duration` giây, nhưng ưu tiên kiểm tra xem luồng đang phải tắt hay không mỗi 100ms
        steps = int(duration / 0.1)
        for _ in range(steps):
            if not self.running: break
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.wait()
