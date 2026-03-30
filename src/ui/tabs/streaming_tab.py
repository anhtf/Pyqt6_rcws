from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt
import config
import sys

# Thử nạp thư viện VLC
try:
    import vlc
    HAS_VLC = True
except ImportError:
    HAS_VLC = False

# ==========================================
# TAB STREAMING (Hiển thị luồng Video mượt mà với VLC)
# ==========================================
class StreamingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.instance = None
        self.player = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Các nút điều khiển cấu hình
        ctrl_layout = QHBoxLayout()
        lbl_url = QLabel("RTSP URL:")
        self.inp_url = QLineEdit(config.DEFAULT_RTSP_URL)
        btn_play = QPushButton("Play")
        btn_stop = QPushButton("Stop")
        
        btn_play.clicked.connect(self.play_video)
        btn_stop.clicked.connect(self.stop_video)
        
        ctrl_layout.addWidget(lbl_url)
        ctrl_layout.addWidget(self.inp_url)
        ctrl_layout.addWidget(btn_play)
        ctrl_layout.addWidget(btn_stop)
        
        layout.addLayout(ctrl_layout)
        
        # Khu vực khung hiển thị Video trực tiếp
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.video_frame)

        if not HAS_VLC:
            lbl_err = QLabel("VLC Library (python-vlc) không tìm thấy!\nVui lòng cài đặt để xem video.", self.video_frame)
            lbl_err.setStyleSheet("color: white; font-size: 16px;")
            lbl_err.setAlignment(Qt.AlignCenter)
            # Để căn giữa chữ, mình cần bắt buộc gán Layout cho QFrame gốc
            # Cách fix nhanh gọn: Đặt 1 Layout dọc và nhét thông báo lỗi vào giữa đó luôn
            vlo = QVBoxLayout(self.video_frame)
            vlo.addWidget(lbl_err)

    def play_video(self):
        if not HAS_VLC: return
        
        url = self.inp_url.text().strip()
        if not url: return
        
        if not self.instance:
            self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()
            
        if self.player.is_playing():
            self.player.stop()
            
        media = self.instance.media_new(url)
        # Thêm options để tối ưu latency cho RTSP
        media.add_option(":network-caching=300")
        
        self.player.set_media(media)
        
        # Gắn video vào khung Qt hiện tại thay vì hiện cửa sổ rời ngoài màn hình
        if sys.platform.startswith('linux'):
            win_id = self.video_frame.winId()
            # Phải ép kiểu thành int thì ctypes của python-vlc mới ăn khớp được cái winId
            self.player.set_xwindow(int(win_id))
        elif sys.platform == "win32":
            win_id = self.video_frame.winId()
            self.player.set_hwnd(int(win_id))
        elif sys.platform == "darwin":
            win_id = self.video_frame.winId()
            self.player.set_nsobject(int(win_id))
            
        self.player.play()

    def stop_video(self):
        if self.player and self.player.is_playing():
            self.player.stop()
