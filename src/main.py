import sys
import os

# Cho phép import các module ở thư mục gốc (như helpers)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Cài đặt nền tảng hiển thị đồ hoạ của PyQt (hỗ trợ tự động nhận dạng Linux và Windows)
if "QT_QPA_PLATFORM" not in os.environ:
    if sys.platform.startswith("linux"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    elif sys.platform.startswith("win"):
        os.environ["QT_QPA_PLATFORM"] = "windows"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.app_window import MainWindow # Dùng file giao diện chính của ứng dụng
from core.comms import UdpWorker
from core.logger import LoggerWorker # Import module ghi log csv
import config

if __name__ == "__main__":
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setStyleSheet(config.STYLESHEET)
    
    # 1. KHỞI TẠO VÀ CHẠY LOGGER
    logger = LoggerWorker()
    logger.start()
    
    # 2. TRUYỀN LOGGER VÀO UDP WORKER
    worker = UdpWorker(config.UDP_IP_BIND, config.UDP_PORT_BIND, 
                       config.UDP_IP_DEST, config.UDP_PORT_DEST,
                       logger=logger)
    
    win = MainWindow(worker)
    win.showFullScreen()
    
    exit_code = app.exec_()

    worker.stop()
    logger.stop() 
    sys.exit(exit_code)