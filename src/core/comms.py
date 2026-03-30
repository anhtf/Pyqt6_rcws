import socket
import select
import time
import threading
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from .protocol import DcuTelemetryPacket, TunningCommandPacket, calculate_checksum
from .definitions import ProtocolHandler
import config


class UdpWorker(QThread):
    send_status = pyqtSignal(bool) 
    log_msg = pyqtSignal(str)
    data_received = pyqtSignal(dict)

    def __init__(self, ip_bind, port_bind, ip_dest, port_dest, logger=None):
        super().__init__()
        self.ip_bind = ip_bind
        self.port_bind = port_bind
        self.ip_dest = ip_dest
        self.port_dest = port_dest
        self.logger = logger
        self.running = False
        self.sock = None
        self.latest_data = {}
        self.mutex = QMutex()
        self.start_flag = False
        self.last_recv_time = 0

    # Hàm ghi log
    # Chức năng: Nếu code đang ở chế độ DEBUG thì nó sẽ bắn signal để ghi log ra màn hình hoặc file.
    def log(self, msg):
        if config.DEBUG:
            self.log_msg.emit(msg)

    # Hàm đổi IP đích
    # Chức năng: Cập nhật lại địa chỉ IP nhận dữ liệu khi người dùng thay đổi. Mình dùng mutex để đảm bảo an toàn luồng.
    def set_dest_ip(self, ip_str):
        self.mutex.lock()
        self.ip_dest = ip_str
        self.mutex.unlock()
        self.log(f"Target IP changed to: {ip_str}")

    # Hàm bắt đầu chạy luồng giao tiếp mạng
    def start_communication(self):
        if not self.isRunning():
            self.start_flag = True
            self.start()
        else:
            self.log("Worker already running")
            
    def run(self):
        if not self.start_flag: return
        
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
        
        try:
            self.sock.bind((self.ip_bind, self.port_bind))
            addr = self.sock.getsockname()
            self.log(f"Bound to {addr[0]}:{addr[1]}")
            print(f"Socket Bound to: {addr}")
        except Exception as e:
            self.log(f"Bind error: {e}")
            return

        while self.running:
            try:
                r, _, _ = select.select([self.sock], [], [], 0.01)
                if r:
                    data, _ = self.sock.recvfrom(8192)
                    #print(f"RX {len(data)}B: {data.hex()}")
                    
                    if self.logger:
                        self.logger.log_packet("RX", data)

                    # Thử parse gói tin theo chuẩn giao thức điều khiển (Standard Protocol)
                    parsed = ProtocolHandler.parse(data)
                    if parsed:
                        if self.logger: self.logger.log_text(f"RX Decoded (Std): {parsed}")
                        # Mình đã chuyển luồng in dòng này vào file log để dọn console cho gọn
                    
                    # Thử parse theo giao thức cấu hình PID (Tunning Protocol / DcuTelemetryPacket)
                    parsed_tunning = DcuTelemetryPacket.unpack(data)
                    if parsed_tunning and not parsed:
                         if self.logger: self.logger.log_text(f"RX Decoded (Tun): {parsed_tunning}")
                    
                    if parsed or parsed_tunning:
                        self.mutex.lock()
                        if parsed:
                            self.latest_data.update(parsed) # Gộp dữ liệu chuẩn vào chung
                        if parsed_tunning:
                            self.latest_data['tunning'] = parsed_tunning # Lưu nguyên object cấu hình vào
                            
                        self.last_recv_time = time.time()
                        
                        # Bắn signal báo là có dữ liệu mới cho giao diện cập nhật
                        self.data_received.emit(self.latest_data.copy())
                        self.mutex.unlock()
            except Exception as e:
                self.log(f"Recv Error: {e}")
                print(f"Recv Error: {e}")
                pass
        
        self.sock.close()
        self.log("Socket closed")

    # Hàm lôi dữ liệu nhận được ra ngoài một cách an toàn
    def get_data(self):
        self.mutex.lock()
        d = self.latest_data.copy()
        d['_timestamp'] = self.last_recv_time
        self.mutex.unlock()
        return d
    

    def send_command(self, cmd_data):
        if not self.running: return

        # 1. Bắt đầu gửi lệnh
        data = ProtocolHandler.pack_command(cmd_data)
        try:
            self.sock.sendto(data, (self.ip_dest, self.port_dest))
            
            # Ghi log gói lệnh vừa gửi ra
            if self.logger:
                self.logger.log_packet("TX", data)
                
        except Exception as e:
            print(f"Lỗi khi gửi: {e}")
            self.send_status.emit(False)
            return
        t0 = time.time()
        success = False
        while (time.time() - t0) < 0.5:
            self.mutex.lock()
            latest = self.latest_data.copy()
            self.mutex.unlock()
            
            if ProtocolHandler.verify(cmd_data, latest):
                dt = time.time() - t0
                print(f"COMMAND ECHO LATENCY: {dt*1000:.2f} ms")
                success = True
                break
            
            time.sleep(0.01)
        
        if not success:
            print("DEBUG: Hết thời gian chờ phản hồi (Timeout) hoặc hàm Verify check tạch!")

        self.send_status.emit(success)


    def send_tunning_command(self, data_bytes):
        if not self.running: return
        try:
            self.sock.sendto(data_bytes, (self.ip_dest, self.port_dest))
            if self.logger:
                self.logger.log_packet("TX_TUN", data_bytes)
        except Exception as e:
            print(f"Error sending tunning: {e}") 


    def stop(self):
        self.running = False
        self.wait()