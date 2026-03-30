
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QStackedWidget, QLabel, QComboBox)
from PyQt5.QtCore import Qt, QSize
from .tabs.control_tab import ControlTab
from .tabs.login_tab import LoginTab
from .tabs.streaming_tab import StreamingTab
from .tabs.firmware_tab import FirmwareTab
from .ip_scanner import IpScannerThread
import time

import sys
import json
import os
import config

# ==========================================
# CỬA SỔ CHÍNH CỦA ỨNG DỤNG (Container)
# File này chứa khung chính, thanh menu bên trái và phần nội dung bên phải.
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self, worker):
        super().__init__()
        self.setWindowTitle("VRW-V12 - Control System")
        self.resize(1280, 800)
        self.worker = worker
        
        self.ip_history = []
        self.load_ip_history()
        
        # Vùng chứa widget trung tâm
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Bố cục gốc (Sắp xếp dọc để có chỗ cho thanh top bar ở trên cùng)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # --- Thanh Bar phía trên giữ nút Đóng ứng dụng ---
        top_bar = QWidget()
        top_bar.setFixedHeight(30)
        top_bar.setStyleSheet("background-color: #333; border-bottom: 1px solid #555;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)
        
        lbl_title = QLabel("VRW-V12")
        lbl_title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        
        btn_close = QPushButton("X")
        btn_close.setFixedSize(30, 24)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("background-color: #ff3333; color: white; font-weight: bold; border: none;")
        btn_close.clicked.connect(self.close_app)
        
        top_layout.addStretch()
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()
        top_layout.addWidget(btn_close)
        
        root_layout.addWidget(top_bar)
        
        # Bố cục chính (Ngang) chia làm 2 phần: Menu bên trái và Nội dung bên phải
        content_widget = QWidget()
        main_layout = QHBoxLayout(content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Thanh Menu bên trái (Sidebar) ---
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220) # Narrower sidebar
        self.sidebar.setFocusPolicy(Qt.NoFocus)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #e0e0e0;
                outline: none;
                border: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #ccc;
                color: #333;
                padding: 12px 5px; /* Increase padding for height */
            }
            QListWidget::item:selected {
                background-color: #fff;
                color: black;
                font-weight: bold;
                border-left: 5px solid #555;
            }
        """)
        self.sidebar.currentRowChanged.connect(self.on_tab_changed)
        
        # Khai báo các mục trong Sidebar
        # Định dạng: ("Tên hiển thị", Widget tương ứng, là_widget_tùy_chỉnh)
        self.menu_items = [
            ("🔒  ĐĂNG NHẬP", LoginTab(self), False),
            ("🛠️  HỆ THỐNG", ControlTab(worker), True), # Tab này xử lý đặc biệt vì có cục nhập IP
            ("⚙️   UPDATE", FirmwareTab(), False),
            ("📺   STREAMING", StreamingTab(), False)
        ]
        
        # --- Vùng Nội dung chính (Bên Phải) ---
        self.stack = QStackedWidget()
        
        self.sys_widget_container = None
        
        for name, widget, is_custom in self.menu_items:
            # Add to Sidebar
            item = QListWidgetItem()
            
            if is_custom and "HỆ THỐNG" in name:
                # Giao diện Tab HT được custom để nhét chèn thêm nút kết nối IP
                # TRẠNG THÁI BAN ĐẦU CỦA TAB NÀY KHI CHƯA CLICK VÀO LÀ THU GỌN (Chỉ hiện chữ HỆ THỐNG)
                item.setSizeHint(QSize(0, 60)) 
                self.sidebar.addItem(item)
                
                self.sys_widget_container = QWidget()
                sys_layout = QVBoxLayout(self.sys_widget_container)
                sys_layout.setContentsMargins(5,5,5,5)
                sys_layout.setSpacing(5)
                
                lbl = QLabel(name)
                lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
                
                # Khu vực chứa nút bấm Kết nối (Bình thường bị xếp ẩn đi)
                self.conn_container = QWidget()
                self.conn_container.setVisible(False)
                conn_layout = QVBoxLayout(self.conn_container)
                conn_layout.setContentsMargins(15,0,0,0) # INDENTATION
                conn_layout.setSpacing(5)
                
                # IP Input
                self.inp_ip = QComboBox()
                self.inp_ip.setEditable(True)
                self.inp_ip.addItems(self.ip_history)
                if hasattr(config, 'UDP_IP_DEST') and config.UDP_IP_DEST not in self.ip_history:
                     self.inp_ip.setEditText(config.UDP_IP_DEST)
                elif self.ip_history:
                     self.inp_ip.setEditText(self.ip_history[0])
                else:
                     self.inp_ip.setEditText(config.UDP_IP_DEST)

                # Connect Button
                self.btn_go = QPushButton("Kết nối")
                self.btn_go.setStyleSheet("background-color: #555; color: white; font-weight: bold; height: 24px;")
                self.btn_go.clicked.connect(self.on_click_go)
                self.inp_ip.lineEdit().returnPressed.connect(self.on_click_go)
                
                conn_layout.addWidget(QLabel("Địa chỉ máy trạm:"))
                conn_layout.addWidget(self.inp_ip)
                conn_layout.addWidget(self.btn_go)
                
                sys_layout.addWidget(lbl)
                sys_layout.addWidget(self.conn_container)
                sys_layout.addStretch()
                
                self.sidebar.setItemWidget(item, self.sys_widget_container)
                self.sys_item = item # Keep ref
            else:
                item.setText(name)
                item.setSizeHint(QSize(0, 50)) 
                self.sidebar.addItem(item)
            
            # Add to Stack
            if "HỆ THỐNG" in name:
                # Bọn mình bọc ControlTab trong ScrollArea để nếu màn hình nhỏ thì vẫn cuộn xem thông số được
                from PyQt5.QtWidgets import QScrollArea
                scroll = QScrollArea()
                scroll.setWidget(widget)
                scroll.setWidgetResizable(True)
                scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
                self.stack.addWidget(scroll)
            else:
                self.stack.addWidget(widget)
            
        main_layout.addWidget(self.sidebar, 0) # Fixed width
        main_layout.addWidget(self.stack, 1)   # Content expands
        
        root_layout.addWidget(content_widget, 1)
        
        # Thiết lập Trạng thái mặc định lúc khởi động app
        self.sidebar.setCurrentRow(0)
        self.lock_sidebar(True)
        
        # Khởi chạy luồng dò tìm và tự động kết nối IP
        self.ip_scanner = IpScannerThread("192.168.1.111")
        self.ip_scanner.ip_detected.connect(self.on_auto_connect_ip)
        self.ip_scanner.start()

    def on_tab_changed(self, index):
        self.stack.setCurrentIndex(index)
        
        # Kiểm tra nếu người dùng chọn tab Hệ thống (index 1) VÀ tài khoản của họ đã đăng nhập
        if index == 1 and not self.sidebar.item(1).flags() & Qt.NoItemFlags:
             if self.sys_widget_container and self.conn_container:
                 self.conn_container.setVisible(True)
                 self.sys_item.setSizeHint(QSize(0, 160)) # Expand
                 self.sidebar.scrollToItem(self.sys_item) # Ensure visible
        else:
             if self.sys_widget_container and self.conn_container:
                 self.conn_container.setVisible(False)
                 self.sys_item.setSizeHint(QSize(0, 50)) # Collapse

    def lock_sidebar(self, locked):
        # Khóa tất cả các tab khác trừ tab đầu tiên (Đăng nhập)
        for i in range(1, self.sidebar.count()):
            item = self.sidebar.item(i)
            if locked:
                item.setFlags(Qt.NoItemFlags) # Disable interaction
            else:
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                
    def load_ip_history(self):
        try:
            from helpers.paths import get_config_path
            path = get_config_path("ip_history.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.ip_history = json.load(f)
        except Exception as e:
            print(f"Error loading ip history: {e}")
            self.ip_history = []

    def save_ip_history(self, new_ip):
        if new_ip in self.ip_history:
            self.ip_history.remove(new_ip)
        self.ip_history.insert(0, new_ip)
        self.ip_history = self.ip_history[:5]
        
        try:
            from helpers.paths import get_config_path
            path = get_config_path("ip_history.json")
            with open(path, "w") as f:
                json.dump(self.ip_history, f)
        except Exception as e:
            print(f"Error saving ip history: {e}")

    def on_click_go(self):
        is_connecting = (self.btn_go.text() == "Kết nối")
        
        if is_connecting:
            # --- BẮT ĐẦU CHẠY KẾT NỐI ---
            new_ip = self.inp_ip.currentText().strip()
            if not new_ip: return
            
            self.save_ip_history(new_ip)
            
            # Update ComboBox
            self.inp_ip.blockSignals(True)
            self.inp_ip.clear()
            self.inp_ip.addItems(self.ip_history)
            self.inp_ip.setEditText(new_ip)
            self.inp_ip.blockSignals(False)
            
            self.worker.set_dest_ip(new_ip)
            self.worker.start_communication()
            
            if self.worker.logger:
                self.worker.logger.start_session()
                
            # Thực hiện bước bắt tay (Handshake) khởi tạo với thiết bị trong ControlTab
            if hasattr(self, 'menu_items') and len(self.menu_items) > 1:
                # Based on index 1 as defined in __init__ ("🛠️ HỆ THỐNG", ControlTab(worker), True)
                control_tab = self.menu_items[1][1]
                if hasattr(control_tab, 'start_handshake'):
                    control_tab.start_handshake()
                
            self.btn_go.setText("NGẮT KẾT NỐI")
            self.btn_go.setStyleSheet("background-color: #ffcccc; color: #cc0000; font-weight: bold; height: 24px;")
            self.inp_ip.setEnabled(False)
            
        else:
            # --- NGẮT KẾT NỐI ---
            # Stop Handshake in ControlTab
            if hasattr(self, 'menu_items') and len(self.menu_items) > 1:
                control_tab = self.menu_items[1][1]
                if hasattr(control_tab, 'stop_handshake'):
                    control_tab.stop_handshake()

            self.worker.stop()
            if self.worker.logger:
                self.worker.logger.stop_session()
                
            self.btn_go.setText("Kết nối")
            self.btn_go.setStyleSheet("background-color: #555; color: white; font-weight: bold; height: 24px;")
            self.inp_ip.setEnabled(True)

    def on_login_success(self, access_level='full'):
        self.lock_sidebar(False)
        self.sidebar.setCurrentRow(1) # Switch to System
        
        # Propagate permissions
        # Control Tab is at index 1 in menu_items
        if len(self.menu_items) > 1:
            control_tab = self.menu_items[1][1]
            if hasattr(control_tab, 'set_permissions'):
                control_tab.set_permissions(access_level)
        
        login_item = self.sidebar.item(0)
        login_item.setText(f"🔓  LOGOUT ({access_level.upper()})")

    def close_app(self):
        if hasattr(self, 'ip_scanner'):
             self.ip_scanner.stop()
        self.close() 

    def on_auto_connect_ip(self, ip_str):
        if self.btn_go.text() == "Kết nối":
             print(f"Auto-Connecting to {ip_str}...")
             self.inp_ip.setEditText(ip_str)
             self.on_click_go()
             # Dừng ngắt scanner một chút để tránh vòng lặp bắt event liên tục lúc kết nối
             # Tạm thời cứ cho chạy bắt IP đâm để đề phòng thiết bị thay đổi IP
             # Logic in thread handles basic throttle.
             pass 