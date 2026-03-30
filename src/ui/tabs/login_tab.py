from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit, QPushButton)
from PyQt5.QtCore import QTimer, Qt, QPointF, QRectF, QTime
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont
import config
import random
import math
import os

import re
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# HIỆU ỨNG ĐỒ HỌA MÀN HÌNH CHỜ (MÔ PHỎNG QUÉT MẠNG HUD)
# ==========================================
class WeaponHUD:
    def __init__(self, parent):
        self.parent = parent
        self.angle = 0
        self.targets = []
        self.found_buffer = [] # Bộ đệm (Buffer) để cập nhật hiển thị mượt mà mà không dính lỗi đa luồng
        self.scanning = True
        self.offline_mode = False
        
        # Khởi chạy luồng quét mạng xử lý ngầm dưới nền
        self.scan_thread = threading.Thread(target=self.run_scan)
        self.scan_thread.daemon = True
        self.scan_thread.start()

    def run_scan(self):
        # 1. Tìm lấy dải IP nội bộ hiện tại một cách chính xác nhất
        local_ip = "127.0.0.1"
        try:
            # Try to connect to a public DNS first
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            # Nếu không có mạng internet, kết nối thử tới gateway nội bộ quen thuộc để fallback
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("192.168.1.1", 80)) # Doesn't need to be reachable
                local_ip = s.getsockname()[0]
                s.close()
            except:
                pass

        if local_ip == "127.0.0.1" or local_ip.startswith("127."):
            self.scanning = False
            self.offline_mode = True
            return

        self.offline_mode = False
        base_ip = ".".join(local_ip.split(".")[:-1])
        is_windows = (os.name == 'nt')

        # 2. Hàm định nghĩa chạy Ping dò thiết bị
        def check_ip(i):
            ip = f"{base_ip}.{i}"
            
            # Bố trí tham số ping phù hợp với nền tảng hệ điều hành
            if is_windows:
                cmd = ['ping', '-n', '1', '-w', '200', ip]
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup_info = si
            else:
                # Linux: ping -c 1 (1 gói), -W 1 (chờ 1 giây tối đa)
                # Lưu ý: 200ms thì một số công cụ ping cũ trên Linux không nhận, nên mình để hẳn 1s cho chắc
                cmd = ['ping', '-c', '1', '-W', '1', ip] 
                startup_info = None

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startup_info,
                    text=True
                )
                stdout, _ = proc.communicate()
                
                if proc.returncode == 0:
                    ping_time = 1
                    
                    if is_windows:
                        match = re.search(r"time[=<]([0-9]+)ms", stdout)
                        if match: ping_time = int(match.group(1))
                        elif "time<1ms" in stdout: ping_time = 1
                    else: 
                        # Trích xuất thời gian ping trên Linux (VD: time=0.034 ms)
                        match = re.search(r"time=([0-9.]+)\s*ms", stdout)
                        if match: ping_time = int(float(match.group(1)))
                    
                    self.found_buffer.append({'ip': ip, 'ping': ping_time})
            except Exception as e:
                pass

        # 3. Phóng luồng song song quét 255 dải địa chỉ cùng lúc để tăng tốc độ quét
        with ThreadPoolExecutor(max_workers=50) as executor:
            for i in range(1, 255):
                executor.submit(check_ip, i)
        
        self.scanning = False

    def update(self):
        self.angle = (self.angle + 2) % 360
        
        # Chuyển dữ liệu từ luồng nền vào luồng UI chính
        if self.found_buffer:
            while self.found_buffer:
                data = self.found_buffer.pop(0)
                ip = data['ip']
                ping = data['ping']
                
                if not any(t['ip'] == ip for t in self.targets):
                    # Signal Strength Mapping
                    # Ping 0-10ms -> Strong -> Dist 1.15
                    # Ping 100ms+ -> Weak -> Dist 2.0+
                    
                    base_dist = 1.15 # Just outside ring (1.0 is ring)
                    
                    # Logarithmic-ish scaling
                    # 1ms -> +0
                    # 10ms -> +0.1
                    # 100ms -> +0.5
                    added_dist = min(1.0, ping / 200.0) 
                    dist_factor = base_dist + added_dist
                    
                    # Collision Detection
                    # We need to find an angle where this target's box doesn't overlap others.
                    # Assume approximate box size in polar space (radians)
                    # Arc length s = r * theta. Box width ~150px.
                    # At r=300px, theta = 150/300 = 0.5 rad (~30 deg).
                    # We try random angles.
                    
                    valid_angle = -1
                    max_attempts = 50
                    
                    # Get center reference (approximate)
                    cx = self.parent.width() / 2
                    cy = self.parent.height() / 2
                    # Approximate radius reference (updated in draw)
                    # We assume r2 ~ 350 based on prev logic
                    
                    for _ in range(max_attempts):
                        cand_angle = random.uniform(0, 360)
                        
                        # Check collision with existing
                        collision = False
                        
                        # Simple angular distance check isn't enough because distances vary
                        # Let's project to simple X,Y relative to center 0,0
                        # normalized r = dist_factor
                        
                        candidate_rad = math.radians(cand_angle)
                        c_x = math.cos(candidate_rad) * dist_factor
                        c_y = math.sin(candidate_rad) * dist_factor
                        
                        # Size buffer in normalized coords? 
                        # box 150px / radius 300px ~ 0.5 units
                        buffer = 0.4
                        
                        for t in self.targets:
                            t_rad = math.radians(t['angle'])
                            t_x = math.cos(t_rad) * t['dist']
                            t_y = math.sin(t_rad) * t['dist']
                            
                            dx = c_x - t_x
                            dy = c_y - t_y
                            dist_sq = dx*dx + dy*dy
                            
                            # if closer than buffer
                            if dist_sq < (buffer * buffer):
                                collision = True
                                break
                        
                        if not collision:
                            valid_angle = cand_angle
                            break
                    
                    if valid_angle == -1:
                        # Fallback: Just place it far out? or random
                        valid_angle = random.uniform(0, 360)
                        dist_factor += 0.5 # Push further out to avoid mess
                    
                    self.targets.append({
                        'ip': ip,
                        'angle': valid_angle,
                        'dist': dist_factor,
                        'ping': ping,
                        'life': 1.0 
                    })
        
        self.parent.update()

    def draw(self, painter, width, height):
        center_x = width / 2
        center_y = height / 2
        
        # Determine Geometry based on LoginCard
        card_w = 420
        card_h = 350 
        corner_dist = math.sqrt((card_w/2)**2 + (card_h/2)**2)
        r1 = corner_dist + 10 # Buffer
        # Radius 2: Outer Radar - REDUCED SIZE
        r2 = r1 * 1.25 # Was 1.6
        
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Lựa chọn Bảng Màu Mặc Định
        color_main = QColor(0, 255, 200) # Cyan
        
        # Hình 1: Nền tảng hiển thị lưới chữ thập định vị
        pen_grid = QPen(QColor(255, 255, 255, 30))
        pen_grid.setWidth(1)
        pen_grid.setStyle(Qt.DotLine)
        painter.setPen(pen_grid)
        
        painter.drawLine(int(center_x), 0, int(center_x), height)
        painter.drawLine(0, int(center_y), width, int(center_y))
        
        # Hình 2: Các vòng tròn Radar đồng tâm bao quanh ngoài
        pen_radar = QPen(color_main)
        pen_radar.setWidth(2)
        painter.setPen(pen_radar)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(center_x, center_y), r1, r1)
        painter.drawEllipse(QPointF(center_x, center_y), r2, r2)
        
        # Hình 3: Thanh sáng Radar quét xoay tròn liên tục
        rad_angle = math.radians(self.angle)
        end_x = center_x + math.cos(rad_angle) * r2
        end_y = center_y + math.sin(rad_angle) * r2
        
        pen_sweep = QPen(QColor(255, 50, 50, 150))
        pen_sweep.setWidth(3)
        painter.setPen(pen_sweep)
        painter.drawLine(QPointF(center_x, center_y), QPointF(end_x, end_y))
        
        # Hình 4: Vẽ các Thiết Bị (Mục Tiêu) tìm được lên hệ thống HUD
        current_time_ms = QTime.currentTime().msecsSinceStartOfDay()
        
        for t in self.targets:
            # Calculate Position
            t_rad = math.radians(t['angle'])
            t_dist = r2 * t['dist']
            
            tx = center_x + math.cos(t_rad) * t_dist
            ty = center_y + math.sin(t_rad) * t_dist
            
            # Prepare Text
            name_text = ""
            ip_text = t['ip']
            ping_val = t.get('ping', 10)
            
            ip_map = {
                "192.168.1.111": "TRẠM ĐK",
                "192.168.1.97": "STREAMING",
                "192.168.1.100": "KÍNH PT"
            }
            if t['ip'] in ip_map: name_text = ip_map[t['ip']]

            # Font Setup
            font = QFont("Consolas", 10, QFont.Bold)
            painter.setFont(font)
            fm = painter.fontMetrics()
            
            # Calculate Box Size
            w_ip = fm.width(ip_text)
            w_name = fm.width(name_text) if name_text else 0
            
            box_w = max(w_ip, w_name) + 20 
            box_h = 40 if name_text else 25
            
            bx = tx - box_w / 2
            by = ty - box_h / 2
            
            # --- CLAMP TO SCREEN ---
            padding = 10
            if bx < padding: bx = padding
            if by < padding: by = padding
            if bx + box_w > width - padding: bx = width - box_w - padding
            if by + box_h > height - padding: by = height - box_h - padding
            
            # Re-center for line drawing
            tx = bx + box_w / 2
            ty = by + box_h / 2
            # -----------------------
            
            # Pulsing Effect (Signal Strength)
            # Higher Ping = Slower Pulse
            # Low Ping (1ms) -> Period 500ms
            # High Ping (200ms) -> Period 2000ms
            
            period = 500 + (ping_val * 10)
            pulse = (math.sin(current_time_ms / period * 3.14) + 1.0) / 2.0 
            
            # Signal Strength Opacity
            # Strong signal = brighter max opacity
            max_alpha = 255 if ping_val < 50 else 150
            
            alpha_border = 50 + int(pulse * (max_alpha - 50))
            alpha_fill = 10 + int(pulse * 40)
            
            # CYAN Borders (Blue/Green) as requested "giống như hiện tại" (general theme)
            color_border = QColor(0, 255, 200, alpha_border) 
            color_fill = QColor(0, 255, 200, alpha_fill)
            
            # Connection Line to Center
            if ping_val < 20:
                painter.setPen(QPen(QColor(0, 255, 200, 30), 1))
                painter.drawLine(QPointF(center_x, center_y), QPointF(tx, ty))
            
            # Draw Box
            painter.setPen(QPen(color_border, 2))
            painter.setBrush(QBrush(color_fill))
            rect = QRectF(bx, by, box_w, box_h)
            painter.drawRect(rect)
            
            # Draw Text - RED
            painter.setPen(QColor(255, 50, 50))
            if name_text:
                painter.drawText(QRectF(bx, by + 5, box_w, 15), Qt.AlignCenter, name_text)
                painter.drawText(QRectF(bx, by + 20, box_w, 15), Qt.AlignCenter, ip_text)
            else:
                painter.drawText(rect, Qt.AlignCenter, ip_text)
                
            # Draw Ping Tiny
            # painter.setFont(QFont("Consolas", 8))
            # painter.setPen(QColor(0, 255, 0, 150))
            # painter.drawText(int(tx + box_w/2), int(ty - box_h/2), f"{ping_val}ms")

        # Scan Status
        if getattr(self, 'offline_mode', False):
             painter.setPen(QColor(255, 50, 50))
             painter.setFont(QFont("Consolas", 10, QFont.Bold))
             painter.drawText(20, height - 20, "CẢNH BÁO: CHƯA KẾT NỐI WIFI")
        elif self.scanning:
             painter.setPen(QColor(255, 255, 0))
             painter.setFont(QFont("Consolas", 10))
             painter.drawText(20, height - 20, "NET: SCANNING...")
        else:
             painter.setPen(QColor(0, 255, 200))
             painter.setFont(QFont("Consolas", 10))
             painter.drawText(20, height - 20, f"NET: COMPLETE ({len(self.targets)} DEVICES)")

        # 5. Text HUD Elements - REMOVED AS REQUESTED
        # painter.setPen(QColor(0, 255, 200))
        # painter.setFont(QFont("Consolas", 10))
        # painter.drawText(20, 30, "SYS: ONLINE") ...

# ==========================================
# LOGIN TAB
# ==========================================
class LoginTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.showing_msg = False # Flag to prioritize error msgs over clock
        
        # Get Local IP for display
        # Get Local IP for display
        self.local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
            s.close()
        except:
             try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("192.168.1.1", 80)) 
                self.local_ip = s.getsockname()[0]
                s.close()
             except:
                pass

        self.hud = WeaponHUD(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30) # ~30 FPS

        self.init_ui()

    def update_loop(self):
        self.hud.update()
        
        # Update Status Label if no error/success message is being shown
        if not self.showing_msg:
            if getattr(self.hud, 'offline_mode', False):
                self.lbl_msg.setText("CHƯA KẾT NỐI MẠNG")
                self.lbl_msg.setStyleSheet("color: #ff3232; font-family: Consolas; font-size: 14px; margin-top: 10px; font-weight: bold;")
            else:
                self.lbl_msg.setText(f"IP MÁY: {self.local_ip}")
                self.lbl_msg.setStyleSheet("color: #0088aa; font-family: Consolas; font-size: 14px; margin-top: 10px; font-weight: bold;")

    def init_ui(self):
        # Configure Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # We use a transparent overlay for layout to sit centrally
        # The painting happens in paintEvent behind everything
        
        container = QWidget()
        l_container = QVBoxLayout(container)
        l_container.addStretch()
        
        # Overlay Card (Centered)
        card = QFrame()
        card.setObjectName("LoginCard")
        card.setFixedWidth(420)
        card.setStyleSheet("""
            #LoginCard {
                background-color: rgba(10, 20, 30, 230);
                border-radius: 5px;
                border: 2px solid #00ffc8;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(40, 40, 40, 40)
        
        lbl_title = QLabel("GIAO DIỆN ĐIỀU KHIỂN")
        lbl_title.setObjectName("LoginTitle")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-family: Consolas; font-size: 24px; font-weight: bold; color: #ff3232; margin-bottom: 10px; letter-spacing: 2px;")
        
        self.inp_password = QLineEdit()
        self.inp_password.setPlaceholderText("NHẬP MẬT MÃ")
        self.inp_password.setEchoMode(QLineEdit.Password)
        self.inp_password.setFixedHeight(50)
        self.inp_password.setAlignment(Qt.AlignCenter)
        self.inp_password.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0,0,0,100);
                border: 1px solid #005544;
                border-radius: 0px;
                padding: 0 10px;
                font-family: Consolas;
                font-size: 16px;
                color: #00ffc8;
                letter-spacing: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #00ffc8;
                background-color: rgba(0,0,0,200);
            }
        """)
        self.inp_password.returnPressed.connect(self.check_login)
        
        btn_login = QPushButton("ĐĂNG NHẬP")
        btn_login.setFixedHeight(50)
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.clicked.connect(self.check_login)
        btn_login.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 200, 50);
                color: #ff3232;
                font-weight: bold;
                font-family: Consolas;
                font-size: 16px;
                border: 1px solid #00ffc8;
                border-radius: 0px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 200, 100);
            }
            QPushButton:pressed {
                background-color: #00ffc8;
                color: black;
            }
        """)
        
        self.lbl_msg = QLabel("")
        self.lbl_msg.setAlignment(Qt.AlignCenter)
        # Style is handled in update_loop
        
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(self.inp_password)
        card_layout.addWidget(btn_login)
        card_layout.addWidget(self.lbl_msg)
        
        # Logo 
        lbl_logo = QLabel()
        lbl_logo.setAlignment(Qt.AlignCenter)
        from PyQt5.QtGui import QPixmap 
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        logo_path = os.path.join(base_dir, "logo.png")
        
        # Optional: Filter logo color if possible, or just display
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaledToWidth(150, Qt.SmoothTransformation)
            lbl_logo.setPixmap(scaled_pixmap)
            lbl_logo.setStyleSheet("margin-top: 20px; opacity: 0.8;")
            card_layout.addWidget(lbl_logo)

        l_container.addWidget(card, 0, Qt.AlignCenter)
        l_container.addStretch()
        
        layout.addWidget(container)

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw dark background
        painter.fillRect(self.rect(), QColor("#050a10"))
        
        # Draw HUD effects
        self.hud.draw(painter, self.width(), self.height())

    def check_login(self):
        pwd = self.inp_password.text()
        self.showing_msg = True
        
        if pwd == "123":
            self.lbl_msg.setText("TRANG THÁI: TOÀN QUYỀN")
            self.lbl_msg.setStyleSheet("color: #00ff00; font-family: Consolas; font-weight: bold; font-size: 14px; margin-top: 10px;")
            QTimer.singleShot(800, lambda: self.main_window.on_login_success('full'))
            
        elif pwd == "456":
            self.lbl_msg.setText("TRẠNG THÁI: CHỈ XEM")
            self.lbl_msg.setStyleSheet("color: #ffff00; font-family: Consolas; font-weight: bold; font-size: 14px; margin-top: 10px;")
            QTimer.singleShot(800, lambda: self.main_window.on_login_success('view'))
            
        else:
            self.lbl_msg.setText("LỖI: SAI MẬT MÃ")
            self.lbl_msg.setStyleSheet("color: #ff3333; font-family: Consolas; font-weight: bold; font-size: 14px; margin-top: 10px;")
            self.inp_password.clear()
            # Reset to clock after 2 seconds
            QTimer.singleShot(2000, self.reset_msg)

    def reset_msg(self):
        self.showing_msg = False
