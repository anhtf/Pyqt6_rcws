from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QPushButton, QLineEdit, QGroupBox, QRadioButton, 
                             QButtonGroup, QFrame, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, QDateTime
from core.protocol import TunningCommandPacket, calculate_checksum
from ui.components import InputRow, LabelRow, FIELD_WIDTH

class TunningTab(QWidget):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.map_val = {}
        self.map_auto_fields = {} 
        
        self.init_ui()
        
        # Bộ định thời gian cập nhật liên tục
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(100) # 10Hz

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # --- NỬA TRÊN (CĂN CHỈNH) ---
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)
        
        # Trái: Nhập các Tham số PID
        self.grp_pid = self.grp("PID Parameters")
        self.init_pid_ui(self.grp_pid)
        top_layout.addWidget(self.grp_pid)
        
        # Phải: Thử nghiệm thông số và kết quả
        self.grp_test = self.grp("Bài thử nghiệm vị trí")
        self.init_test_ui(self.grp_test)
        top_layout.addWidget(self.grp_test)
        
        main_layout.addWidget(top_widget, 1) # Stretch 1
        
        # --- NỬA DƯỚI (MÃ LỖI) ---
        bott_widget = QWidget()
        bott_layout = QVBoxLayout(bott_widget)
        bott_layout.setContentsMargins(0, 0, 0, 0)
        
        self.grp_err = self.grp("Bảng mã lỗi")
        
        self.err_table = QTableWidget(0, 3)
        self.err_table.setHorizontalHeaderLabels(["Thời gian", "Mã lỗi", "Nội dung"])
        self.err_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.err_table.verticalHeader().setVisible(False)
        self.err_table.setStyleSheet("background-color: white; color: black;")
        
        # Thêm một vài hàng dữ liệu tạm nếu cần hoặc để trống
        # Yêu cầu ghi là "sẽ update sau", nên để trống giữ chỗ là ổn.
        
        self.grp_err.layout().addWidget(self.err_table)
        bott_layout.addWidget(self.grp_err)
        
        main_layout.addWidget(bott_widget, 1) # Stretch 1

    def init_pid_ui(self, grp):
        l = grp.layout()
        
        # Chế độ vòng lặp (Loop Mode)
        mode_w = QWidget()
        mode_l = QHBoxLayout(mode_w)
        mode_l.setContentsMargins(0,0,0,0)
        mode_l.addWidget(QLabel("Loop Mode:"))
        
        self.bg_loop = QButtonGroup(self)
        self.rb_pos = QRadioButton("Pos"); self.bg_loop.addButton(self.rb_pos, 0)
        self.rb_rate = QRadioButton("Rate"); self.bg_loop.addButton(self.rb_rate, 1)
        self.rb_curr = QRadioButton("Current"); self.bg_loop.addButton(self.rb_curr, 2)
        self.rb_pos.setChecked(True)
        
        mode_l.addWidget(self.rb_pos)
        mode_l.addWidget(self.rb_rate)
        mode_l.addWidget(self.rb_curr)
        mode_l.addStretch()
        l.addWidget(mode_w)
        
        # Lựa chọn Kênh Tầm (EL) hoặc Kênh Hướng (AZ)
        sel_w = QWidget()
        sel_l = QHBoxLayout(sel_w); sel_l.setContentsMargins(0,0,0,0)
        sel_l.addWidget(QLabel("Kênh:"))
        self.bg_chan = QButtonGroup(self)
        self.rb_el = QRadioButton("Tầm (EL)"); self.bg_chan.addButton(self.rb_el, 1)
        self.rb_az = QRadioButton("Hướng (AZ)"); self.bg_chan.addButton(self.rb_az, 0)
        self.rb_el.setChecked(True)
        sel_l.addWidget(self.rb_el); sel_l.addWidget(self.rb_az); sel_l.addStretch()
        l.addWidget(sel_w)

        # Các ô nhập thông số PID
        # Dùng kiểu InputRow: Nhãn | Nhập (TX) | Nhận (RX) | Nút (M/A)
        self.inp_kp = self.add_inp(l, "Kp", True)
        self.inp_ki = self.add_inp(l, "Ki", True)
        self.inp_kd = self.add_inp(l, "Kd", True)
        self.inp_ilim = self.add_inp(l, "I_Limit", True)
        self.inp_rate = self.add_inp(l, "Rate Ctrl", True)
        
        # Các nút thao tác thực thi
        btn_w = QWidget()
        btn_l = QHBoxLayout(btn_w); btn_l.setContentsMargins(0,5,0,0)
        self.btn_set = QPushButton("SET PID")
        self.btn_set.setStyleSheet("background-color: #555; color: white; font-weight: bold; height: 30px;")
        self.btn_set.clicked.connect(self.on_set_pid)
        btn_l.addWidget(self.btn_set)
        
        self.btn_get = QPushButton("GET PID")
        self.btn_get.setStyleSheet("background-color: #ddd; font-weight: bold; height: 30px;")
        # self.btn_get.clicked.connect(self.on_get_pid) 
        btn_l.addWidget(self.btn_get)
        
        l.addWidget(btn_w)
        l.addStretch()

    def init_test_ui(self, grp):
        l = grp.layout()
        
        # Lưới dữ liệu giám sát thời gian thực (Telemetry)
        tel_w = QWidget()
        tel_g = QGridLayout(tel_w); tel_g.setContentsMargins(0,0,0,0)
        
        tel_g.addWidget(QLabel("<b>Encoder</b>"), 0, 1, Qt.AlignCenter)
        tel_g.addWidget(QLabel("<b>Gyro</b>"), 0, 2, Qt.AlignCenter)
        
        tel_g.addWidget(QLabel("Hướng (AZ):"), 1, 0)
        self.lbl_enc_az = QLabel("0.00"); self.lbl_enc_az.setAlignment(Qt.AlignCenter); self.lbl_enc_az.setStyleSheet("color: blue;")
        tel_g.addWidget(self.lbl_enc_az, 1, 1)
        self.lbl_gyro_az = QLabel("0.00"); self.lbl_gyro_az.setAlignment(Qt.AlignCenter); self.lbl_gyro_az.setStyleSheet("color: blue;")
        tel_g.addWidget(self.lbl_gyro_az, 1, 2)
        
        tel_g.addWidget(QLabel("Tầm (EL):"), 2, 0)
        self.lbl_enc_el = QLabel("0.00"); self.lbl_enc_el.setAlignment(Qt.AlignCenter); self.lbl_enc_el.setStyleSheet("color: blue;")
        tel_g.addWidget(self.lbl_enc_el, 2, 1)
        self.lbl_gyro_el = QLabel("0.00"); self.lbl_gyro_el.setAlignment(Qt.AlignCenter); self.lbl_gyro_el.setStyleSheet("color: blue;")
        tel_g.addWidget(self.lbl_gyro_el, 2, 2)
        
        l.addWidget(tel_w)
        l.addWidget(self.v_line_h())
        
        # Các ô nhập liệu Điều Khiển
        self.inp_tgt_az = self.add_inp(l, "Mục tiêu Hướng (mrad)", False)
        self.inp_tgt_el = self.add_inp(l, "Mục tiêu Tầm (mrad)", False)
        
        # Các nút bấm Stop/Go
        ctrl_w = QWidget()
        ctrl_l = QGridLayout(ctrl_w)
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet("background-color: #cc0000; color: white; font-weight: bold; height: 40px;")
        self.btn_stop.clicked.connect(self.on_stop)
        
        self.btn_go = QPushButton("GO")
        self.btn_go.setStyleSheet("background-color: #008800; color: white; font-weight: bold; height: 40px;")
        self.btn_go.clicked.connect(self.on_go)
        
        ctrl_l.addWidget(self.btn_stop, 0, 0)
        ctrl_l.addWidget(self.btn_go, 0, 1)
        
        l.addWidget(ctrl_w)
        l.addStretch()

    # --- CÁC HÀM PHỤ TRỢ (HELPERS) ---
    def grp(self, t):
        g = QGroupBox(t.upper())
        g.setStyleSheet("font-weight: bold; color: #444;")
        l = QVBoxLayout()
        l.setSpacing(5)
        l.setContentsMargins(5, 10, 5, 5)
        l.setAlignment(Qt.AlignTop)
        g.setLayout(l)
        return g

    def add_inp(self, layout, label, has_read=True):
        # Dùng Component InputRow chuẩn của giao diện
        w = InputRow(label, "0", has_btn=False)
        # Tùy chỉnh: Gỡ nhãn Rx nếu không cần đọc giá trị về, hoặc giữ lại nểu cần thiết
        if not has_read:
            w.rx_val.setVisible(False)
        layout.addWidget(w)
        return w

    def v_line_h(self):
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setFrameShadow(QFrame.Sunken)
        f.setStyleSheet("color: #ccc")
        return f

    # --- XỬ LÝ LOGIC ---

    def on_set_pid(self):
        try:
            kp = int(float(self.inp_kp.inp.text()))
            ki = int(float(self.inp_ki.inp.text()))
            kd = int(float(self.inp_kd.inp.text()))
            ilim = int(float(self.inp_ilim.inp.text()))
            rate = float(self.inp_rate.inp.text())
            
            is_el = (self.bg_chan.checkedId() == 1)
            
            ctrl1 = 0
            ctrl1 |= (1 << 1) # SET_FLAG
            if is_el: ctrl1 |= (1 << 2) # EL_AZ
            
            mode = self.bg_loop.checkedId()
            ctrl1 |= (mode << 3)
            
            pkt = TunningCommandPacket.pack(
                cmd=5,
                control_byte_1=ctrl1,
                control_byte_2=0,
                Kp=kp, Ki=ki, Kd=kd,
                i_limit=ilim,
                rate=rate,
                checksum=0
            )
            chk = calculate_checksum(pkt[:-1])
            pkt = pkt[:-1] + bytes([chk])
            
            self.worker.send_tunning_command(pkt)
            print(f"Sent PID {'EL' if is_el else 'AZ'}")
        except Exception as e:
            print(f"Error SET PID: {e}")

    def on_go(self):
        try:
            az = float(self.inp_tgt_az.inp.text())
            el = float(self.inp_tgt_el.inp.text())
            
            ctrl2 = (1 << 0) # GO_POS
            
            pkt = TunningCommandPacket.pack(
                cmd=5,
                control_byte_1=0,
                control_byte_2=ctrl2,
                pos_az=az,
                pos_el=el,
                checksum=0
            )
            chk = calculate_checksum(pkt[:-1])
            pkt = pkt[:-1] + bytes([chk])
            
            self.worker.send_tunning_command(pkt)
            print("Sent GO Position")
        except Exception as e:
            print(f"Error GO: {e}")

    def on_stop(self):
        # Nút DỪNG (STOP)
        try:
             # Gửi yêu cầu với tất cả các thông số tốc độ bằng 0
             # Tạm thời gán lệnh GO với tham số 0 để ép dừng xoay mục tiêu.
             # Tương đương với chế độ Rate xoay ở tốc độ tĩnh = 0.
             # Tiến hành gửi cấu trúc gói tin rỗng tham số.
             pkt = TunningCommandPacket.pack(5, 0, 0, 0, 0, 0, 0, 0, 0)
             # Tính toán checksum dữ liệu chặn đuôi
             chk = calculate_checksum(pkt[:-1])
             pkt = pkt[:-1] + bytes([chk])
             self.worker.send_tunning_command(pkt)
             print("Sent STOP")
        except: pass

    def update_ui(self):
        data = self.worker.get_data()
        
        # Cập nhật và ánh xạ thông số nhận về lên chữ hiển thị (Telemetry)
        if 'v_a_pos' in data: self.lbl_enc_az.setText(f"{data['v_a_pos']:.2f}")
        if 'v_r_pos' in data: self.lbl_enc_el.setText(f"{data['v_r_pos']:.2f}")
        
        if 'g_a_pos' in data: self.lbl_gyro_az.setText(f"{data['g_a_pos']:.2f}")
        if 'g_r_pos' in data: self.lbl_gyro_el.setText(f"{data['g_r_pos']:.2f}")
