UDP_IP_BIND = "0.0.0.0"
UDP_PORT_BIND = 0
UDP_IP_DEST = "127.0.0.1"
UDP_PORT_DEST = 5001
BUFFER_SIZE = 8192
REFRESH_RATE = 10
CONNECTION_TIMEOUT = 5
DEBUG = True

LOGIN_PASSWORD = "123"
DEFAULT_RTSP_URL = "rtsp://192.168.1.97:1123/gs" 

DEFAULT_DEPLOY_DIR = "Desktop/App"

TARGET_PATHS = {
    "ControlApp": "Monitor/ControlApp",
    "DashboardRCWS": "Dashboard/build-DashboardRCWS-Desktop-Debug/DashboardRCWS",
    "RCWS": "rcws"
}

STYLESHEET = """
    /* Cấu hình màu nền tổng thể của ứng dụng */
    QMainWindow { 
        background-color: #dcdcdc; 
    }
    QWidget { 
        color: #000; 
        font-family: 'Segoe UI', Arial, sans-serif; 
        font-size: 13px;
    }

    /* Giao diện thanh menu Sidebar - Tone màu sáng chuyên nghiệp */
    QListWidget {
        background-color: #d0d0d0; /* Màu nền xám nhạt đồng với màu của ô nhập dữ liệu */
        outline: 0;
        border: none;
        border-right: 1px solid #bfbfbf;
        min-width: 200px;
        max-width: 200px;
    }
    QListWidget::item {
        color: #333;
        padding: 15px 20px;
        border-bottom: 1px solid #c0c0c0;
    }
    QListWidget::item:selected {
        background-color: #f0f0f0; /* Làm sáng nền khi đang được chọn */
        color: #000;
        font-weight: bold;
        border-left: 4px solid #555; /* Tạo viền xám đậm bên trái cho nổi bật */
    }
    QListWidget::item:hover {
        background-color: #e0e0e0;
    }

    /* Giao diện form Đăng nhập */
    #LoginCard {
        background-color: #f2f2f2; /* Màu nền ô đăng nhập khớp với các GroupBox */
        border: 1px solid #cdcdcd;
        border-radius: 8px;
    }
    #LoginTitle {
        font-size: 20px;
        font-weight: bold;
        color: #333;
    }

    /* Element dùng chung - Trả về phối màu truyền thống */
    QGroupBox { 
        background-color: #f2f2f2; 
        border: 1px solid #a0a0a0; 
        border-radius: 4px; 
        margin-top: 22px; 
        font-weight: bold;
    }
    QGroupBox::title { 
        subcontrol-origin: margin; 
        subcontrol-position: top center; 
        padding: 5px 20px; 
        color: #fff; 
        background-color: #555; 
        border: 1px solid #333;
        border-radius: 3px;
        text-transform: uppercase;
        font-weight: bold; 
        font-size: 12px;
    }

    QLineEdit { 
        background-color: #ffffff; 
        border: 1px solid #a0a0a0; 
        color: #000;
        padding: 2px 5px;
        border-radius: 4px;
    }
    QLineEdit[readOnly="true"] {
        background-color: #d0d0d0; 
        color: #000; 
        border: 1px solid #a0a0a0;
    }

    QPushButton { 
        background-color: #e0e0e0; 
        border: 1px solid #999; 
        border-radius: 4px;
        padding: 4px 10px;
        font-weight: bold;
        color: #000;
    }
    QPushButton:hover { background-color: #fff; }
    QPushButton:pressed { background-color: #ccc; }
    
    QLabel { color: #000; }
    
    QCheckBox { spacing: 5px; font-size: 12px; font-weight: bold; }
    QCheckBox::indicator { width: 14px; height: 14px; }
    
    #RowContainer {
        background-color: #ffffff;
        border: 1px solid #bfbfbf;
        border-radius: 3px;
    }
    #RowContainer > QLabel {
        border: none;
        background-color: transparent;
        font-weight: normal; 
    }
    #TimeWidget {
        background-color: #f0f0f0;
        border: 2px solid #999;
        border-radius: 5px;
        padding: 5px;
        color: #cc0000;
        font-weight: bold;
        font-size: 14px;
    }
"""
