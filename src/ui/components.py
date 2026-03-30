from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen

ROW_HEIGHT = 30
FIELD_WIDTH = 70

class LabelRow(QWidget):
    def __init__(self, label, unit="", key=None, sim_btn=False):
        super().__init__()
        self.key = key
        self.setObjectName("RowContainer") 
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(ROW_HEIGHT)
        self.setStyleSheet("#RowContainer { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
        
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 5, 5, 5) # Tăng nhẹ khoảng cách đệm dọc
        l.setSpacing(5)
        
        self.lb = QLabel(label)
        self.lb.setWordWrap(True)
        self.lb.setMinimumWidth(80)
        
        self.val = QLineEdit("0.000")
        self.val.setReadOnly(True)
        self.val.setAlignment(Qt.AlignCenter)
        self.val.setFixedWidth(FIELD_WIDTH)
        self.val.setStyleSheet("border: 1px solid #999; background-color: #fff; color: black; font-weight: bold;")
        
        self.unit = QLabel(unit)
        if unit:
            self.unit.setFixedWidth(25)
        else:
            self.unit.setFixedWidth(0)
        
        l.addWidget(self.lb, 1)
        l.addWidget(self.val)
        l.addWidget(self.unit)
        
        if sim_btn:
             lbl_spacer = QLabel()
             lbl_spacer.setFixedSize(26, 22)
             l.addWidget(lbl_spacer)

    def set_text_color(self, color):
        self.val.setStyleSheet(f"border: 1px solid #999; background-color: #fff; color: {color}; font-weight: bold;")

    def set_val(self, v):
        self.val.setStyleSheet("border: 1px solid #999; background-color: #fff; color: black; font-weight: bold;")
        txt = f"{v:.3f}" if isinstance(v, float) else str(v)
        if self.val.text() != txt: self.val.setText(txt)

    def set_connection_status(self, is_connected):
        if is_connected:
            self.val.setText("CONNECTED")
            self.val.setStyleSheet("background-color: #ccffcc; color: #008800; font-weight: bold; border: 1px solid #008800;")
        else:
            self.val.setText("DIS_CONN")
            self.val.setStyleSheet("background-color: #ffcccc; color: #cc0000; font-weight: bold; border: 1px solid #cc0000;")

class InputRow(QWidget):
    def __init__(self, label, unit="", has_btn=True):
        super().__init__()
        self.setObjectName("RowContainer")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(ROW_HEIGHT)
        self.setStyleSheet("#RowContainer { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
        
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 5, 5, 5)
        l.setSpacing(5)
        
        self.lb = QLabel(label)
        self.lb.setWordWrap(True)
        self.lb.setMinimumWidth(80)
        
        self.inp = QLineEdit("0")
        self.inp.setAlignment(Qt.AlignCenter)
        self.inp.setFixedWidth(FIELD_WIDTH)
        self.inp.setStyleSheet("border: 1px solid #999; color: #008800; font-weight: bold; background-color: #fff; border-radius: 3px;")
        
        self.unit = QLabel(unit)
        if unit:
            self.unit.setFixedWidth(25)
        else:
            self.unit.setFixedWidth(0)
        
        # Nhãn hiển thị giá trị nhận về (RX)
        self.rx_val = QLabel("0")
        self.rx_val.setFixedWidth(FIELD_WIDTH)
        self.rx_val.setAlignment(Qt.AlignCenter)
        # Định dạng RX giống TX nhưng chữ xanh và nền xám
        self.rx_val.setStyleSheet("color: blue; font-weight: bold; border: 1px solid #999; background-color: #e0e0e0; border-radius: 3px;")
        
        l.addWidget(self.lb, 1)
        l.addWidget(self.inp)
        l.addWidget(self.rx_val) # Đã thêm nhãn RX
        l.addWidget(self.unit)
        
        self.btn = QPushButton("M")
        self.btn.setFixedSize(26, 22)
        self.btn.setStyleSheet("padding: 0px; font-size: 11px;")
        if has_btn:
            l.addWidget(self.btn)
        else:
            self.btn.setVisible(False)
            # Thêm một khoảng trống ẩn để căn đều với các hàng có nút bấm
            lbl_spacer = QLabel()
            lbl_spacer.setFixedSize(26, 22)
            l.addWidget(lbl_spacer)

    def set_mode(self, is_auto):
        if is_auto:
            self.btn.setText("A")
            self.inp.setReadOnly(True)
            self.inp.setStyleSheet("border: 1px solid #ccc; background-color: #eee; color: black; font-weight: bold;")
        else:
            self.btn.setText("M")
            self.inp.setReadOnly(False)
            self.inp.setStyleSheet("border: 1px solid #999; background-color: #fff; color: #008800; font-weight: bold;")

class SettingRow(QWidget):
    def __init__(self, label, unit=""):
        super().__init__()
        self.setObjectName("RowContainer")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(ROW_HEIGHT)
        self.setStyleSheet("#RowContainer { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
        
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 5, 5, 5)
        l.setSpacing(5)
        
        self.lb = QLabel(label)
        self.lb.setWordWrap(True)
        
        self.val = QLineEdit("30")
        self.val.setAlignment(Qt.AlignCenter)
        self.val.setFixedWidth(80) 
        self.val.setStyleSheet("color: #cc0000; font-weight: bold; border: 1px solid #999;") 
        
        self.btn = QPushButton("↓")
        self.btn.setFixedSize(26, 22)
        
        l.addWidget(self.lb, 1)
        l.addWidget(self.val)
        l.addWidget(self.btn)

    def update_sync_status(self, recv_val):
        try:
            curr = float(self.val.text())
            if abs(curr - recv_val) < 0.1:
                self.val.setStyleSheet("color: #008800; font-weight: bold; border: 1px solid #008800; background-color: #ccffcc;")
            else:
                self.val.setStyleSheet("color: #cc0000; font-weight: bold; border: 1px solid #cc0000; background-color: #ffcccc;")
        except:
            pass

class GCUSettingRow(QWidget):
    def __init__(self, label, default_time, default_count, is_count_fixed=False):
        super().__init__()
        self.setObjectName("RowContainer")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(ROW_HEIGHT)
        self.setStyleSheet("#RowContainer { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
        
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 5, 5, 5)
        l.setSpacing(5)
        
        self.lb = QLabel(label)
        
        self.time_val = QLineEdit(str(default_time))
        self.time_val.setAlignment(Qt.AlignCenter)
        self.time_val.setFixedWidth(60)
        self.time_val.setStyleSheet("color: #cc0000; font-weight: bold; border: 1px solid #999;")
        
        self.count_val = QLineEdit(str(default_count))
        self.count_val.setAlignment(Qt.AlignCenter)
        self.count_val.setFixedWidth(40)
        
        if is_count_fixed:
            self.count_val.setReadOnly(True)
            self.count_val.setStyleSheet("background-color: #eee; color: #555; border: 1px solid #ccc; font-weight: bold;")
        else:
            self.count_val.setStyleSheet("color: #cc0000; font-weight: bold; border: 1px solid #999;")
            
        self.btn = QPushButton("↓")
        self.btn.setFixedSize(26, 22)
        
        l.addWidget(self.lb, 1)
        l.addWidget(self.time_val)
        l.addWidget(self.count_val)
        l.addWidget(self.btn)

    def update_sync_status(self, recv_time, recv_count=None):
        try:
            curr_time = float(self.time_val.text())
            time_ok = abs(curr_time - recv_time) < 0.1
            
            count_ok = True
            if recv_count is not None and not self.count_val.isReadOnly():
                curr_count = int(self.count_val.text())
                count_ok = (curr_count == recv_count)
            
            if time_ok and count_ok:
                style = "color: #008800; font-weight: bold; border: 1px solid #008800; background-color: #ccffcc;"
            else:
                style = "color: #cc0000; font-weight: bold; border: 1px solid #cc0000; background-color: #ffcccc;"
            
            self.time_val.setStyleSheet(style)
            if not self.count_val.isReadOnly():
                self.count_val.setStyleSheet(style)
        except:
            pass

class DualDisplayRow(QWidget):
    def __init__(self, label, default_val="", rx_default="0"):
        super().__init__()
        self.setObjectName("RowContainer")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(ROW_HEIGHT)
        self.setStyleSheet("#RowContainer { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
        
        l = QHBoxLayout(self)
        l.setContentsMargins(5, 5, 5, 5)
        l.setSpacing(5)
        
        self.lb = QLabel(label)
        self.lb.setMinimumWidth(120)
        
        self.tx_inp = QLineEdit(str(default_val))
        self.tx_inp.setFixedWidth(FIELD_WIDTH)
        self.tx_inp.setAlignment(Qt.AlignCenter)
        self.tx_inp.setStyleSheet("color: black; font-weight: bold; border: 1px solid #999;")
        
        self.rx_val = QLabel(str(rx_default))
        self.rx_val.setFixedWidth(FIELD_WIDTH)
        self.rx_val.setAlignment(Qt.AlignCenter)
        self.rx_val.setStyleSheet("color: blue; font-weight: bold; border: 1px solid #999; background-color: #e0e0e0; border-radius: 3px;")
        
        l.addWidget(self.lb, 1)
        l.addWidget(self.tx_inp)
        l.addWidget(self.rx_val)

    def set_rx(self, val):
        self.rx_val.setText(str(val))
        # Tùy chọn: So sánh tx và rx rồi báo màu cảnh báo lệch giá trị
        try:
            tx_v = float(self.tx_inp.text())
            rx_v = float(val)
            if abs(tx_v - rx_v) < 0.01:
                self.rx_val.setStyleSheet("color: green; font-weight: bold; border: 1px solid #008800; background-color: #ccffcc;")
            else:
                self.rx_val.setStyleSheet("color: red; font-weight: bold; border: 1px solid #cc0000; background-color: #ffcccc;")
        except:
            self.rx_val.setStyleSheet("color: blue; font-weight: bold; border: 1px solid #999; background-color: #fff;")

class AnimatedToggle(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.PointingHandCursor)
        
        # Màu sắc
        self._bg_color = QColor("#dcdcdc")
        self._circle_color = QColor("#ffffff")
        self._active_color = QColor("#008800") # Khớp với màu xanh lá đậm
        
        # Hiệu ứng chuyển động
        self._circle_position = 2.0
        self.animation = QPropertyAnimation(self, b"circle_position")
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setDuration(150)
        
        self.stateChanged.connect(self.setup_animation)

    @pyqtProperty(float)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def setup_animation(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(self.width() - 20)
        else:
            self.animation.setEndValue(2)
        self.animation.start()

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Background
        p.setPen(Qt.NoPen)
        if self.isChecked():
            p.setBrush(self._active_color)
        else:
            p.setBrush(self._bg_color)
            
        rect = QRect(0, 0, self.width(), self.height())
        p.drawRoundedRect(rect, 11, 11)
        
        # Nút tròn gạt
        p.setBrush(self._circle_color)
        circle_rect = QRect(int(self._circle_position), 2, 18, 18)
        p.drawEllipse(circle_rect)

# ==========================================
# COMPONENT HIỂN THỊ POPUP BÁO LỖI
# ==========================================
from PyQt5.QtWidgets import QFrame, QGridLayout, QVBoxLayout
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen
from core.definitions import (
    driver_flag_t, dcu_status_t, 
    Mean_Driver_Error, Mean_DCU_Error
)
import ctypes

class StatusDot(QWidget):
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state # 0 or 1
        self.setFixedSize(16, 16)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        color = QColor("green") if self.state == 0 else QColor("red")
        if self.state == 0:
            color.setAlpha(100) # Dim green
        
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 12, 12)

class ErrorPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip) 
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        # Bỏ thuộc tính TranslucentBackground để viền cửa sổ đặc màu hơn
        # self.setAttribute(Qt.WA_TranslucentBackground) 
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0; 
                border: 2px solid #555; 
                border-radius: 0px;
            }
            QLabel {
                color: #333;
                background-color: transparent;
                font-size: 11px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5) # Thu hẹp lề
        self.layout.setSpacing(2)
        
        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setSpacing(2) # Thu hẹp khoảng cách
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.content_widget)

    def set_data(self, value, limit_type="DCU"):
        # Xóa các mục lỗi hiện thị lần trước
        for i in reversed(range(self.content_layout.count())): 
            self.content_layout.itemAt(i).widget().setParent(None)

        if limit_type == "DRIVER_AZ" or limit_type == "DRIVER_EL":
            # Ép kiểu thành cấu trúc bits driver_flag_t
            flag_obj = driver_flag_t()
            flag_obj.m_raw = value
            definitions = Mean_Driver_Error
            
            # Hàm phụ trợ phân tích và kiểm tra từng bit lỗi
            def check_bits(bits_obj, prefix):
                results = []
                for field_name, f_type, f_len in bits_obj._fields_:
                    if field_name == "m_unused" or field_name == "m_backup": continue
                    
                    val = getattr(bits_obj, field_name)
                    desc = definitions.get(field_name, field_name)
                    results.append((val, desc))
                return results

            all_flags = []
            all_flags.extend(check_bits(flag_obj.m_error, "m_error"))
            all_flags.extend(check_bits(flag_obj.m_warn, "m_warn"))
            all_flags.extend(check_bits(flag_obj.m_state, "m_state"))

        else: # DCU
            flag_obj = dcu_status_t()
            flag_obj.m_raw = value
            definitions = Mean_DCU_Error
            
            all_flags = []
            for field_name, f_type, f_len in flag_obj.m_bits._fields_:
                val = getattr(flag_obj.m_bits, field_name)
                desc = definitions.get(field_name, field_name)
                all_flags.append((val, desc))

        # Hiển thị lên màn hình (Render)
        row = 0
        col = 0
        # Giảm số hàng tối đa để vừa với chiều cao ~180px của GroupBox
        # Giả định 20px mỗi hàng -> 9 hàng = 180px
        max_rows_per_col = 8 
        
        for val, desc in all_flags:
            # Dấu chấm trạng thái
            dot = StatusDot(val)
            self.content_layout.addWidget(dot, row, col * 2)
            
            # Nội dung văn bản lỗi
            lbl = QLabel(desc)
            if val > 0:
                lbl.setStyleSheet("color: red; font-weight: bold;")
            else:
                lbl.setStyleSheet("color: #777;")
            self.content_layout.addWidget(lbl, row, col * 2 + 1)
            
            row += 1
            if row >= max_rows_per_col:
                row = 0
                col += 1
                # Add a spacer column between data columns
                # self.content_layout.setColumnMinimumWidth(col*2 - 1, 10) 