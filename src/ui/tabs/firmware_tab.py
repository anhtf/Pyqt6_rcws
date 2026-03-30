
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QTextEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QFileDialog, QAbstractItemView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import config
import os
import json
import paramiko
import time
from helpers.paths import get_config_path

# Luồng xử lý chạy nền thao tác SSH, giúp giao diện không bị treo khi kết nối lâu
class SSHWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool) # Tín hiệu chạy Thành công/Thất bại

    def __init__(self, ip, user, password, tasks):
        super().__init__()
        self.ip = ip
        self.user = user
        self.password = password
        self.tasks = tasks # Danh sách các việc cần làm: gồm bộ (loại lệnh, đường dẫn nguồn, đường dẫn đích)
        self.is_running = True

    def run(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sftp = None
        
        try:
            self.log_signal.emit(f"Đang kết nối tới {self.user}@{self.ip}...")
            ssh.connect(self.ip, username=self.user, password=self.password, timeout=5)
            self.log_signal.emit("Kết nối thành công.")

            sftp = None

            for task in self.tasks:
                if not self.is_running: break
                
                t_type, arg1, arg2 = task
                
                if t_type == "CMD":
                    self.log_signal.emit(f"LỆNH: {arg1}")
                    # pty=True cần thiết trong trường hợp dùng lệnh sudo phải gõ mật khẩu (mặc dù ta dùng echo pwd)
                    stdin, stdout, stderr = ssh.exec_command(arg1, get_pty=True)
                    
                    # Đợi lệnh chạy xong và lấy mã trạng thái trả về
                    exit_status = stdout.channel.recv_exit_status()
                    
                    # Đọc kết quả màn hình hiển thị
                    out = stdout.read().decode().strip()
                    err = stderr.read().decode().strip()
                    
                    if out: self.log_signal.emit(out)
                    if err: self.log_signal.emit(f"LỖI: {err}")
                    
                    if exit_status != 0:
                        self.log_signal.emit(f"Lệnh thất bại với mã lỗi: {exit_status}")
                        raise Exception("Command failed")
                        
                elif t_type == "SCP":
                    if not sftp: sftp = ssh.open_sftp()
                    local = arg1
                    remote = arg2
                    target_dir = os.path.dirname(remote)
                    self.log_signal.emit(f"Đang chép {os.path.basename(local)} -> {remote}")
                    
                    # Note: tạo thư mục đa tầng qua SFTP khá lằng nhằng, nên phải chạy cmd mkdir -p trên đó trước rồi mới SCP
                    try:
                        sftp.put(local, remote)
                        self.log_signal.emit("Chép file thành công.")
                    except Exception as e:
                        self.log_signal.emit(f"Lỗi SCP: {e}")
                        raise e

            self.log_signal.emit("=== THAO TÁC HOÀN THÀNH ===")
            self.finished_signal.emit(True)

        except Exception as e:
            self.log_signal.emit(f"LỖI KẾT NỐI/THỰC THI: {e}")
            self.finished_signal.emit(False)
        finally:
            if sftp: sftp.close()
            ssh.close()

    def stop(self):
        self.is_running = False

class FirmwareTab(QWidget):
    def __init__(self):
        super().__init__()
        self.file_inputs = {} # key -> {inp: QLineEdit, sub: str}
        self.history_file = get_config_path("firmware_history.json")
        
        self.worker = None

        self.init_ui()
        self.load_history()

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.inp_ip.setText(data.get("ip", "192.168.1.111"))
                    self.inp_user.setText(data.get("user", "box"))
                    self.inp_pass.setText(data.get("pass", "2"))
                    self.inp_service.setText(data.get("service", "rcws.service"))
                    self.inp_script.setText(data.get("script", "run_newjoystick.sh"))
            except Exception as e:
                pass # Bỏ qua nếu có lỗi tải file cấu hình

    def save_history(self):
        data = {
            "ip": self.inp_ip.text(),
            "user": self.inp_user.text(),
            "pass": self.inp_pass.text(),
            "service": self.inp_service.text(),
            "script": self.inp_script.text()
        }
        try:
            with open(self.history_file, 'w') as f:
                json.dump(data, f)
        except: pass

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # === BẢNG BÊN TRÁI: Các nút cấu hình và tác vụ ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # 1. Connection
        grp_conn = QGroupBox("CẤU HÌNH KẾT NỐI")
        grp_conn.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #aaa; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        grid_conn = QGridLayout(grp_conn)
        grid_conn.setSpacing(8)

        self.inp_ip = QLineEdit("192.168.1.111") 
        self.inp_user = QLineEdit("box")        
        self.inp_pass = QLineEdit(); self.inp_pass.setEchoMode(QLineEdit.Password)
        
        grid_conn.addWidget(QLabel("IP:"), 0, 0)
        grid_conn.addWidget(self.inp_ip, 0, 1)
        grid_conn.addWidget(QLabel("User:"), 0, 2)
        grid_conn.addWidget(self.inp_user, 0, 3)
        grid_conn.addWidget(QLabel("Pass:"), 0, 4)
        grid_conn.addWidget(self.inp_pass, 0, 5)
        left_layout.addWidget(grp_conn)

        # 2. Service
        grp_svc = QGroupBox("QUẢN LÝ DỊCH VỤ")
        grp_svc.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #aaa; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        grid_svc = QGridLayout(grp_svc)
        
        self.inp_service = QLineEdit("rcws.service")
        
        btn_stop = QPushButton("Dừng")
        btn_stop.setStyleSheet("background-color: #ffcccc; color: red; font-weight: bold;")
        btn_stop.clicked.connect(self.stop_service)
        
        btn_start = QPushButton("Chạy")
        btn_start.setStyleSheet("background-color: #ccffcc; color: green; font-weight: bold;")
        btn_start.clicked.connect(self.start_service)
        
        btn_restart = QPushButton("Khởi động lại")
        btn_restart.setStyleSheet("background-color: #ddd; font-weight: bold;")
        btn_restart.clicked.connect(self.restart_service)

        grid_svc.addWidget(QLabel("Dịch vụ:"), 0, 0)
        grid_svc.addWidget(self.inp_service, 0, 1)
        
        btn_box = QHBoxLayout()
        btn_box.addWidget(btn_stop)
        btn_box.addWidget(btn_start)
        btn_box.addWidget(btn_restart)
        grid_svc.addLayout(btn_box, 1, 0, 1, 2)
        left_layout.addWidget(grp_svc)

        # 3. Update Firmware (Table)
        grp_upd = QGroupBox("CẬP NHẬT PHẦN MỀM")
        grp_upd.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #aaa; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        vbox_upd = QVBoxLayout(grp_upd)
        
        self.table = QTableWidget(4, 4)
        self.table.setHorizontalHeaderLabels(["Mô đun", "Đường dẫn nguồn", "Chọn", "Thao tác"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setStyleSheet("QTableWidget { border: 1px solid #ccc; gridline-color: #ddd; } QHeaderView::section { background-color: #e0e0e0; font-weight: bold; border: 1px solid #bbb; }")

        # Rows
        self.add_table_row(0, "ControlApp", "Monitor/ControlApp")
        self.add_table_row(1, "DashboardRCWS", "Dashboard/build-DashboardRCWS-Desktop-Debug/DashboardRCWS")
        self.add_table_row(2, "RCWS", "rcws")
        self.add_table_row(3, "Tập tin khác", "")

        vbox_upd.addWidget(self.table)
        left_layout.addWidget(grp_upd)

        # 4. Demo Script
        grp_demo = QGroupBox("CHẠY THỬ NGHIỆM")
        grp_demo.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #aaa; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        hbox_demo = QHBoxLayout(grp_demo)
        
        self.inp_script = QLineEdit("run_newjoystick.sh")
        self.inp_script.setPlaceholderText("Tên script...")
        
        btn_demo = QPushButton("Chạy Script")
        btn_demo.setStyleSheet("background-color: #007acc; color: white; font-weight: bold;")
        btn_demo.clicked.connect(self.run_demo_script)
        
        hbox_demo.addWidget(QLabel("Script:"))
        hbox_demo.addWidget(self.inp_script)
        hbox_demo.addWidget(btn_demo)
        
        left_layout.addWidget(grp_demo)
        left_layout.addStretch()

        # === BẢNG ĐIỀU KHIỂN BÊN PHẢI (Panel in Log) ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_log = QLabel("NHẬT KÝ HỆ THỐNG")
        lbl_log.setAlignment(Qt.AlignCenter)
        lbl_log.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; background-color: #ddd; border: 1px solid #aaa;")
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Monospace; font-size: 12px; border: 1px solid #444;")
        
        right_layout.addWidget(lbl_log)
        right_layout.addWidget(self.log_area)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

    def add_table_row(self, row, name, remote_sub):
        self.table.setItem(row, 0, QTableWidgetItem(name))
        inp = QLineEdit()
        inp.setPlaceholderText("...")
        inp.setStyleSheet("border: none; background: transparent;")
        self.table.setCellWidget(row, 1, inp)
        
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(30)
        btn_browse.clicked.connect(lambda: self.browse_file(inp))
        self.table.setCellWidget(row, 2, btn_browse)
        
        btn_upd = QPushButton("Cập nhật")
        btn_upd.setStyleSheet("font-weight: bold; color: #005500;")
        btn_upd.clicked.connect(lambda: self.update_single_file(name, inp.text(), remote_sub))
        self.table.setCellWidget(row, 3, btn_upd)
        
        self.file_inputs[name] = {"inp": inp, "sub": remote_sub}

    def browse_file(self, inp_widget):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn tập tin", os.getcwd())
        if path:
            inp_widget.setText(path)

    def log(self, msg):
        self.log_area.append(msg)
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def start_worker(self, tasks):
        if self.worker and self.worker.isRunning():
            self.log("Đang có tác vụ chạy, vui lòng chờ...")
            return

        ip = self.inp_ip.text().strip()
        user = self.inp_user.text().strip()
        pwd = self.inp_pass.text().strip()

        if not ip or not user:
            self.log("LỖI: Thiếu IP hoặc User.")
            return

        self.worker = SSHWorker(ip, user, pwd, tasks)
        self.worker.log_signal.connect(self.log)
        self.worker.start()

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN (ACTIONS) ---
    def stop_service(self):
        self.save_history()
        svc = self.inp_service.text()
        pwd = self.inp_pass.text()
        # sudo requires password. Echoing password to sudo -S
        # But exec_command might not handle pipes well with some shells?
        # Standard approach: echo PASS | sudo -S ...
        cmd_stop = f"echo {pwd} | sudo -S systemctl stop {svc}"
        # Check status, exit 0 to prevent error if service is dead
        cmd_status = f"systemctl status {svc} --no-pager; exit 0" 
        
        self.start_worker([
            ("CMD", cmd_stop, None),
            ("CMD", cmd_status, None)
        ])

    def start_service(self):
        self.save_history()
        svc = self.inp_service.text()
        pwd = self.inp_pass.text()
        cmd_start = f"echo {pwd} | sudo -S systemctl start {svc}"
        cmd_status = f"systemctl status {svc} --no-pager; exit 0"
        
        self.start_worker([
            ("CMD", cmd_start, None),
            ("CMD", cmd_status, None)
        ])

    def restart_service(self):
        self.save_history()
        svc = self.inp_service.text()
        pwd = self.inp_pass.text()
        cmd_restart = f"echo {pwd} | sudo -S systemctl restart {svc}"
        cmd_status = f"systemctl status {svc} --no-pager; exit 0"
        
        self.start_worker([
            ("CMD", cmd_restart, None),
            ("CMD", cmd_status, None)
        ])

    def update_single_file(self, name, local_path, remote_sub):
        self.save_history()
        if not local_path:
            self.log(f"LỖI: Chưa chọn tập tin cho {name}")
            return
            
        remote_base = config.DEFAULT_DEPLOY_DIR
        pwd = self.inp_pass.text()
        
        if remote_sub:
             sub_dir = os.path.dirname(remote_sub)
        else:
             sub_dir = ""
             
        # Chuẩn hóa đường dẫn cho môi trường máy đích (Hệ điều hành Linux)
        full_dest_dir = f"{remote_base}/{sub_dir}".replace("//", "/")
        target_filename = os.path.basename(local_path)
        full_remote_path = f"{full_dest_dir}/{target_filename}".replace("//", "/")
        
        # Tạo danh sách các tác vụ update:
        # 1. Tạo thư mục chứa file
        tasks = []
        tasks.append(("CMD", f"mkdir -p {full_dest_dir}", None))
        # 2. Chép file qua SCP
        tasks.append(("SCP", local_path, full_remote_path))
        # 3. Phân quyền đầy đủ cho file (Chmod 777) để chạy được luôn
        tasks.append(("CMD", f"echo {pwd} | sudo -S chmod 777 {full_remote_path}", None))
        
        self.start_worker(tasks)
    
    def run_demo_script(self):
        self.save_history()
        script = self.inp_script.text().strip()
        pwd = self.inp_pass.text()
        
        if not script:
            self.log("LỖI: Chưa nhập tên script.")
            return

        remote_base = config.DEFAULT_DEPLOY_DIR
        # Gửi lệnh chạy qua quyền root (sử dụng sudo)
        cmd = f"cd {remote_base} && echo {pwd} | sudo -S ./{script}"
        self.start_worker([("CMD", cmd, None)])
