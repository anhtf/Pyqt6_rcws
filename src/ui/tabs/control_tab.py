from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QComboBox, QPushButton, QGroupBox, QLineEdit, 
                             QCheckBox, QTableWidget, QHeaderView, QTableWidgetItem, QFrame, QSizePolicy, QTabWidget, QAbstractItemView)
import random
from PyQt5.QtCore import QTimer, Qt, QDateTime, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QEvent
from PyQt5.QtGui import QPainter, QRadialGradient, QColor, QBrush, QPen, QPainterPath
import config
import time
import json
import os
from core.definitions import CommandData
from core.constants import GCU_STATE_MAP, to_base_32
from ui.components import LabelRow, InputRow, SettingRow, GCUSettingRow, DualDisplayRow, FIELD_WIDTH, AnimatedToggle
from ui.components import ErrorPopup
import sys

# ==========================================
# TAB 1: CONTROL TAB
# ==========================================
class GridRowWrapper:
    """Wrapper to make grid items compliant with InputRow interface"""
    def __init__(self, inp, rx_val, btn=None, unit=None):
        self.inp = inp
        self.rx_val = rx_val
        self.btn = btn
        self.unit = unit

    def set_mode(self, is_auto):
        if not self.btn: return
        
        if is_auto:
            self.btn.setText("A")
            self.inp.setReadOnly(True)
            self.inp.setStyleSheet("border: 1px solid #ccc; background-color: #eee; color: black; font-weight: bold;")
        else:
            self.btn.setText("M")
            self.inp.setReadOnly(False)
            self.inp.setStyleSheet("border: 1px solid #999; background-color: #fff; color: #008800; font-weight: bold;")

class FireEffectOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.opacity = 0.0
        self.effect_color = 'red'
        self._anim = QPropertyAnimation(self, b"opacity", self)
        self._anim.setDuration(600) # Faster breathing
        self._anim.setLoopCount(-1) 
        self._anim.setKeyValueAt(0, 0.4)
        self._anim.setKeyValueAt(0.5, 0.9)
        self._anim.setKeyValueAt(1, 0.4)
        self.setVisible(False)
        
        # Pre-calculate random blobs for organic feel
        self.blobs = []
        for _ in range(12): # 12 blobs around the screen
            self.blobs.append({
                'r_scale': random.uniform(0.8, 1.5),
                'angle_offset': random.uniform(0, 360),
                'alpha_mult': random.uniform(0.7, 1.0)
            })

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        center = self.rect().center()
        max_dim = max(w, h)
        
        # 1. Base irregular vignette (Main glow)
        base_gradient = QRadialGradient(center, max_dim / 1.1)
        # Randomize focus slightly to "shake" the light source
        shake_x = random.randint(-5, 5)
        shake_y = random.randint(-5, 5)
        base_gradient.setCenter(center.x() + shake_x, center.y() + shake_y)
        
        alpha = int(255 * self.opacity)
        if self.effect_color == 'yellow':
            base_gradient.setColorAt(0.6, QColor(255, 255, 0, 0)) # Clean center
            base_gradient.setColorAt(0.85, QColor(200, 200, 0, int(alpha * 0.15))) # Soft mid
            base_gradient.setColorAt(1.0, QColor(255, 255, 0, int(alpha * 0.4))) # Hard edge
        else:
            base_gradient.setColorAt(0.6, QColor(255, 0, 0, 0)) # Clean center
            base_gradient.setColorAt(0.85, QColor(200, 0, 0, int(alpha * 0.15))) # Soft mid
            base_gradient.setColorAt(1.0, QColor(255, 0, 0, int(alpha * 0.4))) # Hard edge
            
        painter.fillRect(self.rect(), QBrush(base_gradient))
        
        # 2. Draw random "Blobs" or "Hotspots" on edges
        # We simulate this by drawing smaller radial gradients at the corners/edges
        corners = [
            (0, 0), (w, 0), (0, h), (w, h), # Corners
            (w//2, 0), (w//2, h), (0, h//2), (w, h//2) # Mid-points
        ]
        
        for i, pos in enumerate(corners):
            blob = self.blobs[i % len(self.blobs)]
            blob_alpha = int(alpha * blob['alpha_mult'] * 0.6) # Reduced blob opacity
            if blob_alpha <= 0: continue
            
            radius = (max_dim / 3.0) * blob['r_scale']
            
            # Pulsate radius slightly
            pulsing_radius = radius * (0.9 + 0.1 * self.opacity)
            
            g = QRadialGradient(pos[0], pos[1], pulsing_radius)
            if self.effect_color == 'yellow':
                g.setColorAt(0, QColor(255, 255, 50, blob_alpha)) # Hot center (yellow)
                g.setColorAt(0.6, QColor(180, 180, 0, int(blob_alpha * 0.4)))
                g.setColorAt(1.0, QColor(100, 100, 0, 0))
            else:
                g.setColorAt(0, QColor(255, 50, 0, blob_alpha)) # Hot center (orange-red)
                g.setColorAt(0.6, QColor(180, 0, 0, int(blob_alpha * 0.4)))
                g.setColorAt(1.0, QColor(100, 0, 0, 0))
            
            painter.setBrush(QBrush(g))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(pos[0] - pulsing_radius), int(pos[1] - pulsing_radius), 
                                int(pulsing_radius * 2), int(pulsing_radius * 2))

    @pyqtProperty(float)
    def opacity(self): return self._opacity
    
    @opacity.setter
    def opacity(self, val):
        self._opacity = val
        self.update()

    def start_effect(self, color='red'):
        self.effect_color = color
        if not self.isVisible():
            self.setVisible(True)
            self._anim.start()
        else:
            self.update()

    def stop_effect(self):
        if self.isVisible():
            self._anim.stop()
            self.setVisible(False)

class ControlTab(QWidget):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.cmd_data = CommandData()
        self.map_val = {}
        self.map_auto_fields = {} 
        self.map_echo_fields = {} 
        self.initial_sync_done = False
        self.current_btn_sender = None
        self.cached_fire_time = "00:00:00"
        self.last_aux_mode = False 
        self.last_update_ts = 0 
        
        self.init_ui()
        
        self.worker.send_status.connect(self.on_send_status)
        self.worker.data_received.connect(self.sync_inputs_to_system_state)
        
        self.btn_reset_timer = QTimer()
        self.btn_reset_timer.setSingleShot(True)
        self.btn_reset_timer.timeout.connect(self.reset_btn_color)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(config.REFRESH_RATE)

        self.fire_overlay = FireEffectOverlay(self)
        self.fire_overlay.resize(self.size())
        
        # Connection Shake Logic
        self.shake_timer = QTimer()
        self.shake_timer.setInterval(40) # 25 FPS shake
        self.shake_timer.timeout.connect(self.on_shake_window)
        self.is_shaking = False
        self.base_pos = None
        
        self.error_popup = ErrorPopup(self)

    def resizeEvent(self, event):
        self.fire_overlay.resize(self.size())
        super().resizeEvent(event)

    def start_shake(self):
        if self.is_shaking: return
        
        w = self.window()
        if w:
            self.is_shaking = True
            # We don't save base_pos here because window might be moved by user
            # Instead we shake relatively
            self.shake_timer.start()

    def stop_shake(self):
        if not self.is_shaking: return
        self.is_shaking = False
        self.shake_timer.stop()

    def on_shake_window(self):
        w = self.window()
        if not w: return

        dx = random.randint(-15, 15)
        dy = random.randint(-15, 15)

        
        current_pos = w.pos()
        w.move(current_pos.x() + dx, current_pos.y() + dy)

    def set_permissions(self, access_level):
        is_view_only = (access_level == 'view')

        for child in self.findChildren(QPushButton):
            child.setEnabled(not is_view_only)
            
        for child in self.findChildren(QLineEdit):
            child.setReadOnly(is_view_only)
            # Optional: Change style to look read-only
            
        for child in self.findChildren(QCheckBox):
            child.setEnabled(not is_view_only)
            
        if is_view_only:
            print("Access Level: VIEW ONLY - Controls Disabled")
        else:
            print("Access Level: FULL ACCESS")

    def init_ui(self):
        # Helpers for styles
        style_label = "font-size: 11px;"
        style_box_ro = "background-color: #fff; border: 1px solid #ccc; font-weight: bold; border-radius: 3px;"
        style_box_conn = "background-color: #ddd; border: 1px solid #999; font-weight: bold; border-radius: 3px;" 
        style_box_red = "background-color: red; color: white; border: 1px solid #cc0000; font-weight: bold; border-radius: 3px;"
        style_row = "#RowContainer { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }"
        
        style_checkbox_radio = """
        QCheckBox {
            spacing: 8px;
            color: #000;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border-radius: 9px;
            border: 2px solid #757575;
            background-color: transparent;
        }
        QCheckBox::indicator:checked {
            border: 2px solid #008800;
            background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #008800, stop:0.6 #008800, stop:0.75 transparent, stop:1 transparent);
        }
        """

        # Helper to register status field for updates
        class StatusWrapper:
             def __init__(self, lbl): self.val = lbl
             def set_connection_status(self, is_conn):
                 if is_conn:
                     self.val.setText("ĐÃ KẾT NỐI")
                     self.val.setStyleSheet("background-color: #ccffcc; color: #008800; font-weight: bold; border: 1px solid #008800;")
                 else:
                     self.val.setText("MẤT KẾT NỐI")
                     self.val.setStyleSheet("background-color: red; color: white; font-weight: bold; border: 1px solid #cc0000;")
             def set_val(self, x):
                 try: is_on = int(float(x)) > 0
                 except: is_on = False
                 self.set_connection_status(is_on)
             def set_text_color(self, c): pass # Ignore color updates from legacy logic if any

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0,5,0,5) 
        main_vbox.setSpacing(0)

        # Header removed
        main_vbox.addWidget(QWidget()) 

        # Body
        body = QWidget()
        main_vbox.addWidget(body, 1)
        
        grid = QGridLayout(body)
        grid.setSpacing(6)
        grid.setContentsMargins(4,0,4,4)
        
        for i in range(6): grid.setColumnStretch(i, 1)
        grid.setRowStretch(0, 1); grid.setRowStretch(1, 1); grid.setRowStretch(2, 1)

        # --- ROW 0 ---
        g_sys = self.grp("trạng thái hệ thống")
        self.lbl_row_wide(g_sys, "Trạm vũ khí", "POWER UP", "sys_wpn_str")
        self.lbl_row_wide(g_sys, "Trạm ĐK", "FIRE", "sys_ctrl_str")
        self.lbl_row(g_sys, "Lazer", "0", "sys_laser")
        self.lbl_row(g_sys, "Bát Bám", "0", "sys_track")
        grid.addWidget(g_sys, 0, 0)

        g_veh = self.grp("hệ quy chiếu thân xe")
        self.complex_group_content(g_veh, "v_r_pos", "v_r_spd", "v_a_pos", "v_a_spd")
        grid.addWidget(g_veh, 0, 1)

        g_gyro = self.grp("hệ quy chiếu quán tính")
        self.complex_group_content(g_gyro, "g_r_pos", "g_r_spd", "g_a_pos", "g_a_spd")
        grid.addWidget(g_gyro, 0, 2, 1, 2) 

        g_adj = self.grp("tinh chỉnh")
        adj_w = QWidget(); adj_l = QHBoxLayout(adj_w); adj_l.setContentsMargins(0,0,0,0)
        
        col_el = QVBoxLayout(); col_el.setSpacing(2); col_el.setAlignment(Qt.AlignCenter)
        self.btn_up = self.btn_icon("↑")
        self.inp_tc_el = QLineEdit("0"); self.inp_tc_el.setAlignment(Qt.AlignCenter); self.inp_tc_el.setFixedWidth(70)
        self.inp_tc_el.setStyleSheet("color: #008800; font-weight: bold; border: 1px solid #999;")
        self.btn_down = self.btn_icon("↓")
        col_el.addWidget(self.btn_up, 0, Qt.AlignHCenter)
        col_el.addWidget(self.inp_tc_el, 0, Qt.AlignHCenter)
        col_el.addWidget(self.btn_down, 0, Qt.AlignHCenter)
        
        col_az = QHBoxLayout(); col_az.setSpacing(2); col_az.setAlignment(Qt.AlignCenter)
        self.btn_left = self.btn_icon("←")
        self.inp_tc_az = QLineEdit("0"); self.inp_tc_az.setAlignment(Qt.AlignCenter); self.inp_tc_az.setFixedWidth(70)
        self.inp_tc_az.setStyleSheet("color: #008800; font-weight: bold; border: 1px solid #999;")
        self.btn_right = self.btn_icon("→")
        col_az.addWidget(self.btn_left)
        col_az.addWidget(self.inp_tc_az)
        col_az.addWidget(self.btn_right)
        
        ctrl_w = QWidget(); ctrl_g = QGridLayout(ctrl_w)
        ctrl_g.setContentsMargins(0,0,0,0)
        ctrl_g.addLayout(col_el, 0, 0)
        ctrl_g.addLayout(col_az, 0, 1)
        
        adj_l.addWidget(ctrl_w)
        
        # Handshake Timer
        self.init_timer = QTimer()
        self.init_timer.setInterval(1000)
        self.init_timer.timeout.connect(self.send_init_packet)
        # print("DEBUG: init_timer created in ControlTab", file=sys.stderr)
        
        adj_l.addWidget(self.v_line())
        
        feat_w = QWidget(); feat_l = QVBoxLayout(feat_w); feat_l.setContentsMargins(10,0,0,0); feat_l.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.cb_formula = QCheckBox("Sử dụng Công thức chuyển đổi")
        self.cb_ballistic = QCheckBox("Bù đạn đạo")
        self.cb_autopath = QCheckBox("Tự động đặt đường bắn")
        self.cb_enable_bandon = QCheckBox("Bật chế độ bắn đón")
        self.cb_enable_bandon.toggled.connect(self.on_toggle_bandon)
        
        # Apply radio-button styling
        self.cb_formula.setStyleSheet(style_checkbox_radio)
        self.cb_ballistic.setStyleSheet(style_checkbox_radio)
        self.cb_autopath.setStyleSheet(style_checkbox_radio)
        self.cb_enable_bandon.setStyleSheet(style_checkbox_radio)
        
        feat_l.addWidget(self.cb_formula); feat_l.addWidget(self.cb_ballistic); feat_l.addWidget(self.cb_autopath); feat_l.addWidget(self.cb_enable_bandon)
        adj_l.addWidget(feat_w)
        
        g_adj.layout().addStretch()
        g_adj.layout().addWidget(adj_w)
        g_adj.layout().addStretch()
        grid.addWidget(g_adj, 0, 4, 1, 2)

        self.btn_up.clicked.connect(lambda: self.on_tc_click(0, self.btn_up))
        self.btn_down.clicked.connect(lambda: self.on_tc_click(1, self.btn_down))
        self.btn_right.clicked.connect(lambda: self.on_tc_click(2, self.btn_right))
        self.btn_left.clicked.connect(lambda: self.on_tc_click(3, self.btn_left))

        # --- ROW 1 ---
        g_cp = self.grp("thông tin bảng điều khiển")
        # Status Only
        self.lbl_cp_conn = QLabel("MẤT KẾT NỐI")
        self.lbl_cp_conn.setAlignment(Qt.AlignCenter); self.lbl_cp_conn.setStyleSheet(style_box_red)
        g_cp.layout().addWidget(self.lbl_cp_conn)
       
        self.map_val["cp_conn"] = StatusWrapper(self.lbl_cp_conn)
        self.lbl_row(g_cp, "Khóa lên đạn", "0", "cp_lock_load")
        self.lbl_row(g_cp, "Khóa cò điện", "0", "cp_lock_trig")
        
        def add_styled_toggle(layout, label_text, toggle_widget):
            row = QWidget(); row.setObjectName("RowContainer"); row.setStyleSheet(style_row)
            row.setMinimumHeight(30)
            
            # Match LabelRow margins and spacing exactly (5, 5, 5, 5) and spacing 5
            l = QHBoxLayout(row)
            l.setContentsMargins(5, 5, 5, 5) 
            l.setSpacing(5)
            
            lbl = QLabel(label_text)
            lbl.setWordWrap(True)
            l.addWidget(lbl, 1)
            
            # Container to represent the read-only box width
            val_w = QWidget(); val_l = QHBoxLayout(val_w)
            # Remove margins so toggle can be centered exactly inside the 60px width
            val_l.setContentsMargins(0, 0, 0, 0)
            val_l.setSpacing(0)
            val_w.setFixedWidth(FIELD_WIDTH) # FIELD_WIDTH is 60
            
            # Match the border style of the input fields above exactly
            val_w.setStyleSheet("background-color: #f0f0f0; border: none; border-radius: 3px;")
            
            # Center the toggle horizontally
            val_l.addWidget(toggle_widget, 0, Qt.AlignCenter)
            
            l.addWidget(val_w)
            
            # Spacer for the unit column to match upper rows
            spacer = QLabel()
            spacer.setFixedWidth(0)
            l.addWidget(spacer)
            
            layout.addWidget(row)

        # New Checkbox for Aux Mode
        self.cb_enable_aux = AnimatedToggle()
        self.cb_enable_aux.toggled.connect(self.on_toggle_aux_enable)
        add_styled_toggle(g_cp.layout(), "Bật chế độ phụ trợ", self.cb_enable_aux)
        

        # GCU inside Checkbox
        self.cb_gcu_inside = AnimatedToggle()
        self.cb_gcu_inside.toggled.connect(self.on_toggle_gcu_inside)
        add_styled_toggle(g_cp.layout(), "Dùng GCU trong", self.cb_gcu_inside)
        
        # Bypass LVDT Checkbox (Moved from GCU Board)
        self.cb_bypass_lvdt = AnimatedToggle()
        self.cb_bypass_lvdt.toggled.connect(self.toggle_bypass_lvdt)
        add_styled_toggle(g_cp.layout(), "Không dùng LVDT", self.cb_bypass_lvdt)
        
        grid.addWidget(g_cp, 1, 0)

        # GCU (Col 1-2)
        g_gcu = self.grp("thông tin khối cò điện")
        gcu_container = QWidget()
        gcu_layout = QGridLayout(gcu_container)
        gcu_layout.setContentsMargins(5,5,5,5)
        gcu_layout.setSpacing(5)
        g_gcu.layout().addWidget(gcu_container)

        # === LEFT SIDE (Grid) ===
        left_w = QWidget()
        left_main = QVBoxLayout(left_w)
        left_main.setContentsMargins(0,0,0,0); left_main.setSpacing(5)

        # --- Top Info Grid ---
        top_l = QVBoxLayout()
        top_l.setContentsMargins(0,0,0,0); top_l.setSpacing(5)

        def add_top_row(l1, w1, l2, w2):
            row = QWidget(); row.setObjectName("RowContainer"); row.setStyleSheet(style_row)
            row.setMinimumHeight(30)
            l = QHBoxLayout(row); l.setContentsMargins(5,5,5,5); l.setSpacing(5)
            
            lbl1 = QLabel(l1); lbl1.setStyleSheet(style_label)
            lbl2 = QLabel(l2); lbl2.setStyleSheet(style_label)
            
            l.addWidget(lbl1, 1)
            l.addWidget(w1, 1)
            l.addWidget(lbl2, 1)
            l.addWidget(w2, 1)
            
            top_l.addWidget(row)

        # R0: Status only
        # R0: Status only
        # Use fresh variable name to ensure valid reference
        self.lbl_gcu_conn_final = QLabel("MẤT KẾT NỐI")
        self.lbl_gcu_conn_final.setAlignment(Qt.AlignCenter)
        self.lbl_gcu_conn_final.setStyleSheet("background-color: red; color: white; font-weight: bold; border: 1px solid #cc0000; border-radius: 3px;")
        
        top_l.addWidget(self.lbl_gcu_conn_final)
        
        wrap = StatusWrapper(self.lbl_gcu_conn_final)
        # self.map_val["gcu_conn_state"] = wrap # REMOVED: gcu_conn_state is system status (int), not connection bool
        self.map_val["gcu_conn"] = wrap
        #print(wrap)
        
        # R1: STATE ONLY (Bypass LVDT moved to CP)
        self.lbl_gcu_state = QLabel("KXĐ")
        self.lbl_gcu_state.setAlignment(Qt.AlignCenter); self.lbl_gcu_state.setStyleSheet(style_box_ro)
        
        # Add STATE taking full width or just the normal left width
        # We pass empty QWidget for the right side
        empty_w = QWidget()
        add_top_row("STATE", self.lbl_gcu_state, "", empty_w)

        # R2: Mode | Current
        self.lbl_gcu_mode = QLabel("PM")
        self.lbl_gcu_mode.setAlignment(Qt.AlignCenter); self.lbl_gcu_mode.setStyleSheet(style_box_ro)
        self.lbl_gcu_curr = QLabel("0.00")
        self.lbl_gcu_curr.setAlignment(Qt.AlignCenter); self.lbl_gcu_curr.setStyleSheet(style_box_ro)
        add_top_row("Chế độ bắn", self.lbl_gcu_mode, "Dòng điện (A)", self.lbl_gcu_curr)

        # R3: Limit | Prox BD
        self.lbl_gcu_limit = QLabel("OFF")
        self.lbl_gcu_limit.setAlignment(Qt.AlignCenter); self.lbl_gcu_limit.setStyleSheet(style_box_ro)
        self.lbl_gcu_prox_bd = QLabel("0")
        self.lbl_gcu_prox_bd.setAlignment(Qt.AlignCenter); self.lbl_gcu_prox_bd.setStyleSheet(style_box_ro)
        add_top_row("Hạn chế góc", self.lbl_gcu_limit, "Proximity BĐ", self.lbl_gcu_prox_bd)

        # R4: Ammo | Prox LD
        # Ammo: [Display] only, expand
        ammo_w = QWidget(); ammo_l = QHBoxLayout(ammo_w); ammo_l.setContentsMargins(0,0,0,0)
        self.lbl_ammo_display = QLabel("0"); self.lbl_ammo_display.setAlignment(Qt.AlignCenter)
        self.lbl_ammo_display.setStyleSheet("background-color: #fff; font-weight: bold; border: 1px solid #ccc; border-radius: 3px;") 
        # Make it expand or full width of the container
        ammo_l.addWidget(self.lbl_ammo_display)
        
        self.lbl_gcu_prox_ld = QLabel("0")
        self.lbl_gcu_prox_ld.setAlignment(Qt.AlignCenter); self.lbl_gcu_prox_ld.setStyleSheet(style_box_ro)
        add_top_row("Số đạn còn lại", ammo_w, "Proximity LĐ", self.lbl_gcu_prox_ld)

        left_main.addLayout(top_l)
        left_main.addSpacing(5)

        # --- Modes Grid ---
        modes_l = QVBoxLayout()
        modes_l.setContentsMargins(0,0,0,0); modes_l.setSpacing(5)
        # Cols: Label, TimeTx, TimeRx, CntTx, CntRx, Btn
        
        def add_mode_item(lbl, val_t, val_c, idx, cnt_fixed=False):
            row = QWidget(); row.setObjectName("RowContainer"); row.setStyleSheet(style_row)
            row.setMinimumHeight(40) 
            # Let's keep 30 but ensure alignment.
            row.setMinimumHeight(30)
            gl = QHBoxLayout(row); gl.setContentsMargins(5,5,5,5); gl.setSpacing(5)
            
            gl.addWidget(QLabel(lbl), 1)

            # TX Auto Off (NEW)
            tx_auto = QLineEdit("0"); tx_auto.setFixedWidth(50); tx_auto.setAlignment(Qt.AlignCenter)
            tx_auto.setStyleSheet("color: red; font-weight: bold; border: 1px solid red; background-color: #ffcccc; border-radius: 3px;")
            gl.addWidget(tx_auto)
            
            # Time TX
            tx_t = QLineEdit(str(val_t)); tx_t.setFixedWidth(50); tx_t.setAlignment(Qt.AlignCenter)
            # Default RED (mismatch/disconnected)
            tx_t.setStyleSheet("color: red; font-weight: bold; border: 1px solid red; background-color: #ffcccc; border-radius: 3px;")
            gl.addWidget(tx_t)

            # Time RX
            rx_t = QLabel(str(val_t)); rx_t.setFixedWidth(50); rx_t.setAlignment(Qt.AlignCenter)
            rx_t.setStyleSheet("background-color: #e0e0e0; border: 1px solid #999; color: #555; border-radius: 3px;")
            gl.addWidget(rx_t)

            # Count TX
            tx_c = QLineEdit(str(val_c)); tx_c.setFixedWidth(40); tx_c.setAlignment(Qt.AlignCenter)
            if cnt_fixed:
                tx_c.setReadOnly(True)
                # ReadOnly but still RED if not matched? Yes.
                tx_c.setStyleSheet("background-color: #ffcccc; border: 1px solid red; color: red; font-weight: bold; border-radius: 3px;")
            else:
                tx_c.setStyleSheet("color: red; font-weight: bold; border: 1px solid red; background-color: #ffcccc; border-radius: 3px;")
            gl.addWidget(tx_c)

            # Count RX
            rx_c = QLabel(str(val_c)); rx_c.setFixedWidth(40); rx_c.setAlignment(Qt.AlignCenter)
            rx_c.setStyleSheet("background-color: #e0e0e0; border: 1px solid #999; color: #555; border-radius: 3px;")
            gl.addWidget(rx_c)

            btn = QPushButton("↓"); btn.setFixedSize(24, 22)
            btn.setStyleSheet("background-color: #ddd; border: 1px solid #999; border-radius: 3px;")
            btn.clicked.connect(lambda: self.send_gcu_param(idx))
            gl.addWidget(btn)
            
            modes_l.addWidget(row)

            return tx_auto, tx_t, rx_t, tx_c, rx_c, btn

        self.gcu_pm_auto_tx, self.gcu_pm_tx, self.gcu_pm_rx, self.gcu_pm_cnt_tx, self.gcu_pm_cnt_rx, self.gcu_pm_btn = add_mode_item("Phát một (ms)", 30, 1, 0, cnt_fixed=True)
        self.gcu_dxn_auto_tx, self.gcu_dxn_time_tx, self.gcu_dxn_time_rx, self.gcu_dxn_cnt_tx, self.gcu_dxn_cnt_rx, self.gcu_dxn_btn = add_mode_item("Điểm xạ ngắn (ms)", 450, 3, 1)
        self.gcu_dxd_auto_tx, self.gcu_dxd_time_tx, self.gcu_dxd_time_rx, self.gcu_dxd_cnt_tx, self.gcu_dxd_cnt_rx, self.gcu_dxd_btn = add_mode_item("Điểm xạ dài (ms)", 800, 10, 2)
        self.gcu_lt_auto_tx, self.gcu_lt_time_tx, self.gcu_lt_time_rx, self.gcu_lt_cnt_tx, self.gcu_lt_cnt_rx, self.gcu_lt_btn = add_mode_item("Liên thanh (ms)", 10000, 0, 3, cnt_fixed=True)

        def sync_auto_off(text):
            for tx in (self.gcu_pm_auto_tx, self.gcu_dxn_auto_tx, self.gcu_dxd_auto_tx, self.gcu_lt_auto_tx):
                if tx.text() != text:
                    tx.setText(text)
        
        self.gcu_pm_auto_tx.textEdited.connect(sync_auto_off)
        self.gcu_dxn_auto_tx.textEdited.connect(sync_auto_off)
        self.gcu_dxd_auto_tx.textEdited.connect(sync_auto_off)
        self.gcu_lt_auto_tx.textEdited.connect(sync_auto_off)

        left_main.addLayout(modes_l)

        # Bottom Checkbox Block Removed
        left_main.addStretch()
        left_main.addStretch()

        gcu_layout.addWidget(left_w, 0, 0)
        gcu_layout.addWidget(self.create_right_gcu_table(), 0, 1)        
        gcu_layout.setColumnStretch(0, 1) 
        gcu_layout.setColumnStretch(1, 0) 
        
        grid.addWidget(g_gcu, 1, 1, 1, 2)

        # Trạm vũ khí
        g_ws = self.grp("thông tin trạm vũ khí")
        ws_l = QVBoxLayout(); ws_l.setContentsMargins(0,0,0,0); ws_l.setSpacing(5); ws_l.setAlignment(Qt.AlignTop)
        dcu_w = QWidget(); dcu_l = QVBoxLayout(dcu_w); dcu_l.setContentsMargins(0,0,0,0); dcu_l.setSpacing(1); dcu_l.setAlignment(Qt.AlignTop)
        self.lbl_dcu_conn = QLabel("MẤT KẾT NỐI")
        self.lbl_dcu_conn.setAlignment(Qt.AlignCenter); self.lbl_dcu_conn.setStyleSheet(style_box_red)
        dcu_l.addWidget(self.lbl_dcu_conn)
        self.map_val["dcu_conn"] = StatusWrapper(self.lbl_dcu_conn)
        self.lbl_row_manual(dcu_l, "Nhiệt độ (oC)", "0.00", "dcu_temp")
        self.lbl_row_manual(dcu_l, "Giới hạn dòng", "0", "dcu_limit_curr")
        self.lbl_row_manual(dcu_l, "Mã Lỗi", "0", "dcu_err")
        ws_l.addWidget(dcu_w); ws_l.addWidget(self.v_line())
        
        # Driver section
        drv_w = QWidget(); drv_l = QVBoxLayout(drv_w); drv_l.setContentsMargins(0,0,0,0); drv_l.setSpacing(1)
        lbl_drv = QLabel("DRIVER")
        lbl_drv.setAlignment(Qt.AlignCenter)
        lbl_drv.setStyleSheet("background-color: #555; color: white; font-weight: bold; padding: 2px;")
        drv_l.addWidget(lbl_drv)
        drv_l.addSpacing(5) 

        self.lbl_row_manual(drv_l, "Nhiệt độ Tầm", "0.00", "drv_el_temp")
        self.lbl_row_manual(drv_l, "Lỗi Tầm", "0", "drv_el_err")
        self.lbl_row_manual(drv_l, "Nhiệt độ Hướng", "0.00", "drv_az_temp")
        self.lbl_row_manual(drv_l, "Lỗi Hướng", "0", "drv_az_err")
        ws_l.addWidget(drv_w)
        
        g_ws.layout().addLayout(ws_l)
        grid.addWidget(g_ws, 1, 3)

        self.g_kpt = self.grp("thông tin kính pháo thủ")
        self.lbl_sight_conn = QLabel("MẤT KẾT NỐI")
        self.lbl_sight_conn.setAlignment(Qt.AlignCenter); self.lbl_sight_conn.setStyleSheet(style_box_red)
        self.g_kpt.layout().addWidget(self.lbl_sight_conn)
        self.map_val["sight_conn"] = StatusWrapper(self.lbl_sight_conn)
        self.lbl_row(self.g_kpt, "Chế độ", "KP", "sight_mode")
        self.lbl_row(self.g_kpt, "Tầm (mrad)", "0.00", "sight_el")
        self.lbl_row(self.g_kpt, "Hướng (mrad)", "0.00", "sight_az")
        self.lbl_row(self.g_kpt, "EleAngleTarget", "0.00", "sight_el_tgt")
        grid.addWidget(self.g_kpt, 1, 4)

        self.g_tgt = self.grp("thông tin mục tiêu")
        self.lbl_row(self.g_tgt, "Cự ly (m)", "0.00", "t_dist")
        self.lbl_row(self.g_tgt, "Vị trí Tầm", "0.00", "t_el")
        self.lbl_row(self.g_tgt, "Vị trí Hướng", "0.00", "t_az")
        self.lbl_row(self.g_tgt, "Tốc độ (m/s)", "0.00", "t_spd")
        self.lbl_row(self.g_tgt, "Hướng DC", "0.00", "t_dir")
        grid.addWidget(self.g_tgt, 1, 5)

        # --- ROW 2 ---
        
        # --- AUXILIARY MODE ---
        self.group_aux = self.grp("chế độ phụ trợ")
        self.group_aux.setEnabled(False) 
        
        aux_main_l = QVBoxLayout()
        aux_main_l.setContentsMargins(0,0,0,0)
        
        aux_chk_l = QHBoxLayout()
        aux_chk_l.setSpacing(15) 
        self.cb_sync = QCheckBox("Đồng bộ súng kính")
        self.cb_sensor = QCheckBox("Thiết lập phạm vi cảm biến")
        self.cb_load = QCheckBox("Chức năng nạp đạn")
        self.cb_unload = QCheckBox("Chức năng khám đạn, tháo đạn")
        
        # Apply radio-button styling
        self.cb_sync.setStyleSheet(style_checkbox_radio)
        self.cb_sensor.setStyleSheet(style_checkbox_radio)
        self.cb_load.setStyleSheet(style_checkbox_radio)
        self.cb_unload.setStyleSheet(style_checkbox_radio)
        
        aux_chk_l.addWidget(self.cb_sync)
        aux_chk_l.addWidget(self.cb_sensor)
        aux_chk_l.addWidget(self.cb_load)
        aux_chk_l.addWidget(self.cb_unload)
        aux_chk_l.addStretch()
        
        aux_main_l.addLayout(aux_chk_l)
        aux_main_l.addSpacing(5) # Reduced from 15

        self.aux_sync_widget = QWidget()
        aux_layout = QVBoxLayout(self.aux_sync_widget)
        aux_layout.setContentsMargins(5,5,5,5); aux_layout.setSpacing(5)

        # Helper for Aux Pairs
        def add_aux_group(title, key_t=None, key_h=None):
             # Group Container
             grp = QWidget()
             grp.setAttribute(Qt.WA_StyledBackground, True)
             # Solid border as requested "giống kiểu border của toàn hệ thống" (#bbb)
             grp.setStyleSheet(".QWidget { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
             grp_l = QHBoxLayout(grp); grp_l.setContentsMargins(2,2,2,2); grp_l.setSpacing(5) # Compact margins/spacing

             # Left Title
             lbl_title = QLabel(title)
             lbl_title.setAlignment(Qt.AlignCenter)
             lbl_title.setWordWrap(True)
             lbl_title.setStyleSheet("border: 1px solid #999; padding: 5px; background-color: #fff; font-weight: bold;")
             lbl_title.setFixedWidth(140) 
             grp_l.addWidget(lbl_title)

             # Right Column
             right_col = QWidget()
             right_col.setStyleSheet("border: none; background-color: transparent;") 
             rc_l = QVBoxLayout(right_col); rc_l.setContentsMargins(0,0,0,0); rc_l.setSpacing(5)
             
             # Sub-row Helper
             def add_sub_row(lbl_text, key=None):
                 r = QWidget()
                 # "Thêm 1 lớp border ở hàng Tầm/Hướng"
                 r.setStyleSheet("border: 1px solid #bbb; border-radius: 4px; background-color: transparent;")
                 rl = QHBoxLayout(r); rl.setContentsMargins(5,5,5,5); rl.setSpacing(5)
                 
                 lb = QLabel(lbl_text)
                 lb.setFixedWidth(60)
                 lb.setAlignment(Qt.AlignCenter)
                 lb.setStyleSheet("border: 1px solid #ccc; background-color: #fff;")
                 
                 inp = QLineEdit("0")
                 inp.setAlignment(Qt.AlignCenter); inp.setFixedWidth(FIELD_WIDTH)
                 inp.setStyleSheet("border: 1px solid #999; color: #008800; font-weight: bold; background-color: #fff; border-radius: 3px;")
                 
                 rx = QLabel("0")
                 rx.setAlignment(Qt.AlignCenter); rx.setFixedWidth(FIELD_WIDTH)
                 rx.setStyleSheet("color: blue; font-weight: bold; border: 1px solid #999; background-color: #e0e0e0; border-radius: 3px;")
                 
                 rl.addWidget(lb)
                 rl.addStretch() # Push input/rx to right
                 rl.addWidget(inp)
                 rl.addWidget(rx)
                 
                 w = GridRowWrapper(inp, rx, None)
                 if key: self.map_auto_fields[key] = w
                 return r, w

             r1, w1 = add_sub_row("Tầm", key_t)
             r2, w2 = add_sub_row("Hướng", key_h)
             
             rc_l.addWidget(r1)
             rc_l.addWidget(r2)
             
             grp_l.addWidget(right_col)
             aux_layout.addWidget(grp)
             
             return w1, w2

        self.inp_lech_t, self.inp_lech_h = add_aux_group("Khoảng lệch trục", "echo_h_tam", "echo_h_huong")
        self.inp_cam_t, self.inp_cam_h = add_aux_group("Phạm vi cấm bắn", "echo_cam_tam", "echo_cam_huong")
        self.inp_sua_t, self.inp_sua_h = add_aux_group("Lượng sửa đầu Gương", "echo_sua_dg_tam", "echo_sua_dg_huong")
        self.inp_zero_t, self.inp_zero_h = add_aux_group("Lượng sửa Zeroing", "echo_sua_tam_zero", "echo_sua_huong_zero")
        
        # Wrapper for Calib to match Group Style
        def add_aux_single(title, key=None):
             grp = QWidget()
             grp.setAttribute(Qt.WA_StyledBackground, True)
             grp.setStyleSheet(".QWidget { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
             grp_l = QHBoxLayout(grp); grp_l.setContentsMargins(2,2,2,2); grp_l.setSpacing(5) # Compact margins/spacing
             
             # Left Title
             lbl_title = QLabel(title)
             lbl_title.setAlignment(Qt.AlignCenter)
             lbl_title.setWordWrap(True)
             lbl_title.setStyleSheet("border: 1px solid #999; padding: 5px; background-color: #fff; font-weight: bold;")
             lbl_title.setFixedWidth(140) 
             grp_l.addWidget(lbl_title)
             
             # Right content - Structure matching add_sub_row
             r = QWidget()
             r.setStyleSheet("border: 1px solid #bbb; border-radius: 4px; background-color: transparent;")
             rl = QHBoxLayout(r); rl.setContentsMargins(5,5,5,5); rl.setSpacing(5)
             
             dummy_lbl = QLabel("")
             dummy_lbl.setFixedWidth(60)
             dummy_lbl.setStyleSheet("border: none;") 
             
             inp = QLineEdit("0")
             inp.setAlignment(Qt.AlignCenter); inp.setFixedWidth(FIELD_WIDTH)
             inp.setStyleSheet("border: 1px solid #999; color: #008800; font-weight: bold; background-color: #fff; border-radius: 3px;")
                 
             rx = QLabel("0")
             rx.setAlignment(Qt.AlignCenter); rx.setFixedWidth(FIELD_WIDTH)
             rx.setStyleSheet("color: blue; font-weight: bold; border: 1px solid #999; background-color: #e0e0e0; border-radius: 3px;")
             
             rl.addWidget(dummy_lbl)
             rl.addStretch()
             rl.addWidget(inp)
             rl.addWidget(rx)
             
             grp_l.addWidget(r)
             aux_layout.addWidget(grp)
             
             w = GridRowWrapper(inp, rx, None)
             if key: self.map_auto_fields[key] = w
             return w

        self.inp_calib = add_aux_single("Cự ly Đồng Trục", "echo_cu_ly_hc")
        
        # self.inp_calib = GridRowWrapper(self.inp_calib_inp, self.inp_calib_rx, None) # Removed manual wrap
        
        self.aux_load_widget = QWidget(); self.aux_load_widget.setVisible(False)
        load_l = QHBoxLayout(self.aux_load_widget); load_l.setContentsMargins(0,0,0,0)
        load_l.addWidget(QLabel("Nhập tổng số đạn nạp:"))
        self.inp_ammo_load = QLineEdit("20"); self.inp_ammo_load.setFixedWidth(80)
        self.inp_ammo_load.setAlignment(Qt.AlignCenter)
        self.inp_ammo_load.setStyleSheet("font-weight: bold; color: blue;")
        self.inp_ammo_load.textEdited.connect(lambda text: setattr(self.cmd_data, 'iMode', 1))
        load_l.addWidget(self.inp_ammo_load)
        load_l.addStretch()

        aux_main_l.addWidget(self.aux_sync_widget)
        aux_main_l.addWidget(self.aux_load_widget)
        aux_main_l.addStretch()
        
        self.group_aux.layout().addLayout(aux_main_l)
        grid.addWidget(self.group_aux, 2, 0, 1, 2)

        self.cb_load.toggled.connect(self.on_toggle_load)

        # --- SHOOTING PARAMETERS ---
        g_inp = self.grp("nhập thông số phần tử bắn")
        inp_w = QWidget(); 
        
        # Split into two columns (Left/Right)
        inp_layout = QHBoxLayout(inp_w); 
        inp_layout.setContentsMargins(0,0,0,0); 
        inp_layout.setSpacing(10)
        
        # Left Container
        left_container = QWidget()
        left_grid = QGridLayout(left_container)
        left_grid.setContentsMargins(0,0,0,0)
        left_grid.setSpacing(5)
        
        # Right Container
        right_container = QWidget()
        right_grid = QGridLayout(right_container)
        right_grid.setContentsMargins(0,0,0,0)
        right_grid.setSpacing(5)
        
        inp_layout.addWidget(left_container)
        inp_layout.addWidget(right_container)
        
        row_l = 0
        row_r = 0
        
        class PurpleWrapper:
            def __init__(self, v_widget): self.val = v_widget
            def set_val(self, x): self.val.setText(f"{x:.3f}" if isinstance(x, float) else str(x))
            def set_text_color(self, c): self.val.setStyleSheet(f"border: 1px solid #ccc; background-color: #eee; color: {c}; font-weight: bold;")

        def add_purple_hdr(layout, r, lbl, key):
            row = QWidget(); row.setObjectName("RowContainer"); 
            row.setStyleSheet("#RowContainer { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
            row.setMinimumHeight(55)
            
            l = QHBoxLayout(row); l.setContentsMargins(5,5,5,5); l.setSpacing(5)
            
            l1 = QLabel(lbl); l1.setWordWrap(True)
            v = QLineEdit("0.00"); v.setReadOnly(True); v.setAlignment(Qt.AlignCenter); v.setFixedWidth(FIELD_WIDTH)
            v.setStyleSheet("border: 1px solid #999; background-color: #fff; color: purple; font-weight: bold; border-radius: 3px;")
            
            l.addWidget(l1, 1) # Label takes available space
            l.addWidget(v)
            l.addWidget(QLabel()) # Spacer 
            l.addWidget(QLabel()) # Spacer 
            
            layout.addWidget(row, r, 0, 1, 4)
            self.map_val[key] = PurpleWrapper(v)
            
        add_purple_hdr(left_grid, row_l, "Góc phần tử bắn tầm (mrad)", "echo_goc_ngam_tam"); row_l+=1
        add_purple_hdr(left_grid, row_l, "Góc phần tử bắn hướng (mrad)", "echo_goc_ngam_huong"); row_l+=1

        self.add_section_header(left_grid, row_l, 0, "Thông tin lượng sửa", 4); row_l+=1
        self.ip_sua_t = self.add_grid_inp(left_grid, row_l, 0, "Lượng sửa tầm (mrad)", has_btn=False, bit=-1, udp_key="echo_bu_tam"); row_l+=1
        self.ip_sua_h = self.add_grid_inp(left_grid, row_l, 0, "Lượng sửa hướng (mrad)", has_btn=False, bit=-1, udp_key="echo_bu_huong"); row_l+=1
        
        self.add_section_header(left_grid, row_l, 0, "Thông tin góc nảy", 4); row_l+=1
        self.ip_nay = self.add_grid_inp(left_grid, row_l, 0, "Góc nảy (mrad)", has_btn=False, bit=-1, udp_key="echo_goc_nay"); row_l+=1
        
        self.add_section_header(left_grid, row_l, 0, "Thông tin bắn đón", 4); row_l+=1
        self.ip_vt_t = self.add_grid_inp(left_grid, row_l, 0, "Vận tốc MT tầm (m/s)", True, 7, "echo_vt_mt_el"); row_l+=1
        self.ip_vt_h = self.add_grid_inp(left_grid, row_l, 0, "Vận tốc MT hướng (m/s)", True, 8, "echo_vt_mt_az"); row_l+=1
        
        left_grid.setRowStretch(row_l, 1)

        # Right Side
        self.add_section_header(right_grid, row_r, 0, "Thông tin đạn đạo", 4); row_r+=1
        self.ip_dist = self.add_grid_inp(right_grid, row_r, 0, "Cự ly (m)", True, 6, "echo_cu_ly"); row_r+=1
        self.ip_temp = self.add_grid_inp(right_grid, row_r, 0, "Nhiệt độ (0C)", True, 5, "echo_nhiet_do"); row_r+=1
        self.ip_pres = self.add_grid_inp(right_grid, row_r, 0, "Áp suất (mmHg)", True, 0, "echo_ap_suat"); row_r+=1
        self.ip_wind_x = self.add_grid_inp(right_grid, row_r, 0, "Gió ngang (m/s)", True, 3, "echo_gio_ngang"); row_r+=1
        self.ip_wind_y = self.add_grid_inp(right_grid, row_r, 0, "Gió dọc (m/s)", True, 2, "echo_gio_doc"); row_r+=1
        self.ip_tilt = self.add_grid_inp(right_grid, row_r, 0, "Độ nghiêng (0)", True, 1, "echo_do_nghieng"); row_r+=1
        self.ip_cant = self.add_grid_inp(right_grid, row_r, 0, "Góc tà (0)", True, 4, "echo_goc_ta"); row_r+=1
        self.ip_sotoc = self.add_grid_inp(right_grid, row_r, 0, "Sơ tốc đầu nòng (m/s)", False, -1, "echo_so_toc"); row_r+=1

        # Removed forced column widths to prevent horizontal overflow
        self.btn_ok = QPushButton("Đồng ý")
        self.btn_ok.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.btn_ok.setStyleSheet("background-color:#555; color:white; font-weight:bold; font-size:14px; border:1px solid #333; height: 30px;")
        self.btn_ok.clicked.connect(self.send_all_params)
        
        right_grid.addWidget(self.btn_ok, row_r, 0, 1, 4)
        row_r += 1
        
        right_grid.setRowStretch(row_r, 1)
        
        g_inp.layout().addWidget(inp_w)
        grid.addWidget(g_inp, 2, 2, 1, 3) 

        g_env = self.grp("môi trường")
        self.lbl_row(g_env, "Nhiệt độ (0C)", "0.00", "env_temp")
        self.lbl_row(g_env, "Tốc độ gió", "0.00", "env_wind")
        self.lbl_row(g_env, "Áp suất", "0.00", "env_pres")
        self.lbl_row(g_env, "Hướng gió", "0.00", "env_wdir")
        
        # Stretch to push Time/Date to bottom
        g_env.layout().addStretch()
        
        self.lbl_time = QLabel("00:00:00 - 01/01/2000")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.lbl_time.setObjectName("TimeWidget")
        
        g_env.layout().addWidget(self.lbl_time)
        grid.addWidget(g_env, 2, 5)

        # Install Event Filters for Error Hover
        if 'dcu_err' in self.map_val:
            self.map_val['dcu_err'].val.installEventFilter(self)
        if 'drv_el_err' in self.map_val:
            self.map_val['drv_el_err'].val.installEventFilter(self)
        if 'drv_az_err' in self.map_val:
            self.map_val['drv_az_err'].val.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Enter:
            if 'dcu_err' in self.map_val and source == self.map_val['dcu_err'].val:
                self.show_error_popup(source, "DCU")
            elif 'drv_el_err' in self.map_val and source == self.map_val['drv_el_err'].val:
                self.show_error_popup(source, "DRIVER_EL")
            elif 'drv_az_err' in self.map_val and source == self.map_val['drv_az_err'].val:
                self.show_error_popup(source, "DRIVER_AZ")
        elif event.type() == QEvent.Leave:
            self.error_popup.hide()
        return super().eventFilter(source, event)

    def show_error_popup(self, widget, erratic_type):
        try:
            # Parse the Base32 string back to int
            text = widget.text()
            val = int(text, 32)
        except:
            val = 0
            
        self.error_popup.set_data(val, erratic_type)
        
        # Calculate geometry to cover both g_kpt and g_tgt
        # They are in the grid at (1,4) and (1,5)
        # We can map their geometry to global
        
        rect_kpt = self.g_kpt.rect()
        rect_tgt = self.g_tgt.rect()
        
        # Map to global
        pos_kpt = self.g_kpt.mapToGlobal(rect_kpt.topLeft())
        pos_tgt = self.g_tgt.mapToGlobal(rect_tgt.topLeft())
        
        # Combined Rect
        # Assuming g_kpt is left of g_tgt
        # Top Left = pos_kpt
        # Width = width(kpt) + width(tgt) + spacing? 
        # Better: TopLeft = min(x,y), BotRight = max(x+w, y+h)
        
        # We can map top-left of KPT and bottom-right of TGT
        # This assumes KPT is (1,4) and TGT is (1,5) next to each other
        
        tl = pos_kpt
        br_tgt = self.g_tgt.mapToGlobal(rect_tgt.bottomRight())
        
        w = br_tgt.x() - tl.x()
        h = br_tgt.y() - tl.y()
        # Ensure height matches the max of both? They should be same row height
        h = max(rect_kpt.height(), rect_tgt.height())
        
        self.error_popup.setGeometry(tl.x(), tl.y(), w, h)
        self.error_popup.show()

    def create_right_gcu_table(self):
        right_w = QWidget()
        right_l = QVBoxLayout(right_w)
        right_l.setContentsMargins(0,0,0,0)
        right_l.setSpacing(5)

        self.btn_reset_batch = QPushButton("Loạt mới")
        self.btn_reset_batch.clicked.connect(self.on_reset_batch)
        self.btn_reset_batch.setStyleSheet("font-weight: bold; background-color: #ddd;")
        right_l.addWidget(self.btn_reset_batch)
        
        self.bullet_table = QTableWidget(10, 2)
        self.bullet_table.setHorizontalHeaderLabels(["Viên", "Trễ (ms)"])
        self.bullet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bullet_table.verticalHeader().setVisible(False)
        self.bullet_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.bullet_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.bullet_table.setFixedWidth(150) 
        self.bullet_table.setMaximumHeight(230) 
        
        for r in range(10):
            self.bullet_table.setItem(r, 0, QTableWidgetItem(str(r+1)))
            self.bullet_table.setItem(r, 1, QTableWidgetItem(""))
            
        right_l.addWidget(self.bullet_table)
        right_l.addStretch() 
        return right_w

    def add_grid_inp(self, grid, r, c, label, has_btn=True, bit=-1, udp_key=None):
        row = QWidget()
        row.setObjectName("RowContainer")
        row.setAttribute(Qt.WA_StyledBackground, True)
        row.setMinimumHeight(30)
        row.setStyleSheet("#RowContainer { border: 1px solid #bbb; border-radius: 4px; background-color: transparent; }")
        
        l = QHBoxLayout(row)
        l.setContentsMargins(5, 5, 5, 5)
        l.setSpacing(5)
        
        lbl = QLabel(label); lbl.setWordWrap(True)
        
        inp = QLineEdit("0")
        inp.setAlignment(Qt.AlignCenter)
        inp.setFixedWidth(FIELD_WIDTH)
        inp.setStyleSheet("border: 1px solid #999; color: #008800; font-weight: bold; background-color: #fff; border-radius: 3px;")
        
        rx_val = QLabel("0")
        rx_val.setFixedWidth(FIELD_WIDTH)
        rx_val.setAlignment(Qt.AlignCenter)
        rx_val.setStyleSheet("color: blue; font-weight: bold; border: 1px solid #999; background-color: #e0e0e0; border-radius: 3px;")
        
        btn = None
        
        l.addWidget(lbl, 1)
        l.addWidget(inp)
        l.addWidget(rx_val)
        
        if has_btn:
            btn = QPushButton("M")
            btn.setFixedSize(26, 22)
            btn.setStyleSheet("padding: 0px; font-size: 11px;")
            l.addWidget(btn)
        else:
            spacer = QLabel()
            spacer.setFixedSize(26, 22)
            l.addWidget(spacer)
            
        grid.addWidget(row, r, c, 1, 4)
        
        w = GridRowWrapper(inp, rx_val, btn)
        if udp_key: self.map_auto_fields[udp_key] = w
        
        if has_btn and bit >= 0:
             # Connect after wrapper creation to pass it
             btn.clicked.connect(lambda checked=False, b=btn, i=bit, wp=w: self.toggle_ttdd_flag(b, i, wp))

        return w

    # Removed ip_history methods here as they are now in MainWindow

    def start_handshake(self):
        self.handshake_acked = False
        self.initial_sync_done = False # Reset One-time Sync
        print("DEBUG: Starting Handshake Timer...", file=sys.stderr)
        sys.stderr.flush()
        self.init_timer.start()

    def stop_handshake(self):
        print("DEBUG: Stopping Handshake Timer.", file=sys.stderr)
        sys.stderr.flush()
        self.init_timer.stop()

    def check_match(self, tx, rx_val, is_ro=False):
        try: v_rx = int(float(rx_val)); v_tx = int(float(tx.text()))
        except: v_rx = -1; v_tx = -2
        
        s_green = "color: green; font-weight: bold; border: 1px solid #008800; background-color: #ccffcc; border-radius: 3px;"
        s_red = "color: red; font-weight: bold; border: 1px solid red; background-color: #ffcccc; border-radius: 3px;"
        
        if v_tx == v_rx: tx.setStyleSheet(s_green)
        else: tx.setStyleSheet(s_red)

    def sync_inputs_to_system_state(self, d):
        # Throttling to prevent UI dizziness (20 FPS)
        cur = time.time()
        if cur - self.last_update_ts < 0.05: return
        self.last_update_ts = cur
        
        # Generic Update Loop for simple mapped fields (StatusWrapper, etc)
        for k, v in d.items():
            if k in self.map_val:
                if k in ['drv_az_err', 'drv_el_err', 'dcu_err']:
                    try:
                        v = to_base_32(v)
                    except:
                        pass
                
                w = self.map_val[k]
                if hasattr(w, 'set_val'):
                    w.set_val(v)
                elif hasattr(w, 'setText'):
                    txt = f"{v:.3f}" if isinstance(v, float) else str(v)
                    w.setText(txt)

        # GCU
        if 'echo_gcu_auto_off' in d:
            auto_val = d['echo_gcu_auto_off']
            self.check_match(self.gcu_pm_auto_tx, auto_val)
            self.check_match(self.gcu_dxn_auto_tx, auto_val)
            self.check_match(self.gcu_dxd_auto_tx, auto_val)
            self.check_match(self.gcu_lt_auto_tx, auto_val)

        if 'echo_gcu_dx' in d: 
            self.gcu_pm_rx.setText(str(d['echo_gcu_dx']))
            self.check_match(self.gcu_pm_tx, d['echo_gcu_dx'], True)
        
        if 'echo_gcu_dxn' in d: 
            self.gcu_dxn_time_rx.setText(str(d['echo_gcu_dxn']))
            self.check_match(self.gcu_dxn_time_tx, d['echo_gcu_dxn'])
        if 'echo_gcu_cnt_dxn' in d: 
            self.gcu_dxn_cnt_rx.setText(str(int(d['echo_gcu_cnt_dxn'])))
            self.check_match(self.gcu_dxn_cnt_tx, d['echo_gcu_cnt_dxn'])

        if 'echo_gcu_dxd' in d: 
            self.gcu_dxd_time_rx.setText(str(d['echo_gcu_dxd']))
            self.check_match(self.gcu_dxd_time_tx, d['echo_gcu_dxd'])
        if 'echo_gcu_cnt_dxd' in d: 
            self.gcu_dxd_cnt_rx.setText(str(int(d['echo_gcu_cnt_dxd'])))
            self.check_match(self.gcu_dxd_cnt_tx, d['echo_gcu_cnt_dxd'])

        if 'echo_gcu_lt' in d: 
            self.gcu_lt_time_rx.setText(str(d['echo_gcu_lt']))
            self.check_match(self.gcu_lt_time_tx, d['echo_gcu_lt'], True)
        
        # Also check fixed counts just in case? Matches logic.
        # PM Count (0)
        self.check_match(self.gcu_pm_cnt_tx, self.gcu_pm_cnt_rx.text(), True)
        # LT Count (3)
        self.check_match(self.gcu_lt_cnt_tx, self.gcu_lt_cnt_rx.text(), True)
        
        # New Ammo Logic
        if 'gcu_rem_ammo' in d or 'echo_gcu_total_ammo' in d:
            curr_text = self.lbl_ammo_display.text()
            rem = d.get('gcu_rem_ammo', curr_text.split('/')[0] if '/' in curr_text else '?')
            tot = d.get('echo_gcu_total_ammo', curr_text.split('/')[1] if '/' in curr_text else '?')
            self.lbl_ammo_display.setText(f"{rem}/{tot}")

        # Logic REPLACING manual updates with Generic Loop + Flicker Check
        # This covers Aux, Calibration, Inputs, Ballistic if they are in map_auto_fields
        
        # 1. Auto-Sync Logic (Initial Connect)
        if not getattr(self, 'initial_sync_done', False):
             synced_count = 0
             for k, w in self.map_auto_fields.items():
                 if k in d:
                     w.inp.setText(f"{d[k]:.2f}")
                     synced_count += 1
             if synced_count > 0: self.initial_sync_done = True

        # 2. Continuous Update Loop
        for k, w in self.map_auto_fields.items():
            if k in d:
                val = d[k]
                txt = f"{val:.2f}"
                
                # Anti-Flicker: Only update if text changed
                if w.rx_val.text() != txt:
                    w.rx_val.setText(txt)
                
                # Auto Input Mode
                if w.btn and w.btn.text() == "A":
                    if w.inp.text() != txt:
                        w.inp.setText(txt)

    def send_init_packet(self):
        print(f"DEBUG: Timer Tick. Acked={self.handshake_acked}, WorkerRunning={self.worker.running if self.worker else 'None'}", file=sys.stderr)
        sys.stderr.flush()
        if self.handshake_acked:
            print("DEBUG: Handshake Acked. Stopping Timer.", file=sys.stderr)
            self.init_timer.stop()
            return

        if self.worker and self.worker.running:
            print("DEBUG: Sending HANDSHAKE...", file=sys.stderr)
            self.worker.send_tunning_command(b'HANDSHAKE')
        
    def on_click_go(self):
        # Nút này giờ là Kết nối / Ngắt kết nối
        is_connecting = (self.btn_go.text() == "Kết nối")
        
        if is_connecting:
            # --- START CONNECT ---
            new_ip = self.inp_ip.currentText().strip()
            if not new_ip: return
            
            # Removed save_ip_history logic here

            
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
                
            self.btn_go.setText("Ngắt kết nối")
            self.btn_go.setStyleSheet("background-color: #ffcccc; color: #cc0000; font-weight: bold;")
            self.inp_ip.setEnabled(False)
            
            self.start_handshake() # Start handshake process
            
        else:
            # --- DISCONNECT ---
            self.worker.stop()
            if self.worker.logger:
                self.worker.logger.stop_session()
            
            self.stop_handshake() # Stop handshake process
                
            self.btn_go.setText("Kết nối")
            self.btn_go.setStyleSheet("")
            self.inp_ip.setEnabled(True)

    def get_val(self, w):
        try: return float(w.text())
        except: return 0.0

    def send_all_params(self):
        self.current_btn_sender = self.btn_ok
        
        self.cmd_data.bu_tam = self.get_val(self.ip_sua_t.inp)
        self.cmd_data.bu_huong = self.get_val(self.ip_sua_h.inp)
        self.cmd_data.nhiet_do = self.get_val(self.ip_temp.inp)
        self.cmd_data.ap_suat = self.get_val(self.ip_pres.inp)
        self.cmd_data.gio_ngang = self.get_val(self.ip_wind_x.inp)
        self.cmd_data.gio_doc = self.get_val(self.ip_wind_y.inp)
        self.cmd_data.do_nghieng = self.get_val(self.ip_tilt.inp)
        self.cmd_data.so_toc = self.get_val(self.ip_sotoc.inp)
        self.cmd_data.goc_nay = self.get_val(self.ip_nay.inp)
        self.cmd_data.goc_ta = self.get_val(self.ip_cant.inp)
        self.cmd_data.cu_ly = self.get_val(self.ip_dist.inp)
        self.cmd_data.vt_mt_el = self.get_val(self.ip_vt_t.inp)
        self.cmd_data.vt_mt_az = self.get_val(self.ip_vt_h.inp)
        
        self.cmd_data.h_tam = self.get_val(self.inp_lech_t.inp)
        self.cmd_data.h_huong = self.get_val(self.inp_lech_h.inp)
        self.cmd_data.cambantam = self.get_val(self.inp_cam_t.inp)
        self.cmd_data.cambanhuong = self.get_val(self.inp_cam_h.inp)
        self.cmd_data.sua_dau_guong_tam = self.get_val(self.inp_sua_t.inp)
        self.cmd_data.sua_dau_guong_huong = self.get_val(self.inp_sua_h.inp)
        self.cmd_data.sua_tam_zero = self.get_val(self.inp_zero_t.inp)
        self.cmd_data.sua_huong_zero = self.get_val(self.inp_zero_h.inp)
        self.cmd_data.cu_ly_hieu_chinh = self.get_val(self.inp_calib.inp)
        self.cmd_data.nhapsodan = self.get_val(self.inp_ammo_load)
        #print(self.cmd_data.nhapsodan)
        
        # Feature Flags
        f = 0
        if self.cb_formula.isChecked(): f |= 1
        if self.cb_ballistic.isChecked(): f |= 2
        if self.cb_autopath.isChecked(): f |= 4
        if self.cb_enable_bandon.isChecked(): f |= 8
        self.cmd_data.feature_flags = f

        self.worker.send_command(self.cmd_data)
        
        if self.cb_load.isChecked():
            # Legacy or other ammo load logic if needed
            pass
            
    def send_ammo_setup(self):
        try: 
            val = int(self.inp_ammo_set.text())
            self.cmd_data.gcu_total_ammo = val
            # Flag 5 (index 4?) checks? 
            # In legacy code gcu_total_ammo was just sent, maybe with a flag?
            # Assuming just setting the value and sending command is enough if using standard struct.
            # But let's check if there is a specific command flag for ammo set.
            # Based on previous code, it just set cmd_data.gcu_total_ammo and called send_command generally.
            self.worker.send_command(self.cmd_data)
        except: pass
        
        f = 0
        if self.cb_formula.isChecked(): f |= 1
        if self.cb_ballistic.isChecked(): f |= 2
        if self.cb_autopath.isChecked(): f |= 4
        if self.cb_enable_bandon.isChecked(): f |= 8
        self.cmd_data.feature_flags = f

        self.worker.send_command(self.cmd_data)

    def toggle_ttdd_flag(self, btn, bit_idx, wrapper=None):
        if btn.text() == "M":
            btn.setText("A")
            self.cmd_data.ttdd_flags |= (1 << bit_idx)
            if wrapper: wrapper.set_mode(True)
        else:
            btn.setText("M")
            self.cmd_data.ttdd_flags &= ~(1 << bit_idx)
            if wrapper: wrapper.set_mode(False)

    def on_tc_click(self, btn_idx, btn_obj):
        self.current_btn_sender = btn_obj
        
        try: el_val = float(self.inp_tc_el.text())
        except: el_val = 0.0
        try: az_val = float(self.inp_tc_az.text())
        except: az_val = 0.0
        
        self.cmd_data.tc_dpos_el = el_val
        self.cmd_data.tc_dpos_az = az_val
        self.cmd_data.btn_flags = (1 << btn_idx)
        
        self.worker.send_command(self.cmd_data)

    def on_toggle_load(self, checked):
        self.aux_sync_widget.setVisible(not checked)
        self.aux_load_widget.setVisible(checked)

    def on_reset_batch(self):
        self.current_btn_sender = self.btn_reset_batch
        self.cmd_data.flagResetChukidan = 1
        self.worker.send_command(self.cmd_data)
        #self.cmd_data.gcu_cmd_flag = 0
        
        for r in range(10):
            self.bullet_table.setItem(r, 0, QTableWidgetItem(str(r+1)))
            self.bullet_table.setItem(r, 1, QTableWidgetItem(""))

    def send_gcu_param(self, cmd_id):
        # cmd_id: 0=PM, 1=DXN, 2=DXD, 3=LT
        # Determine which button triggered this? 
        # Actually passed as argument to lambda, but we need the button object for color feedback.
        # We can look up the button based on cmd_id.
        
        btn = None
        if cmd_id == 0: btn = self.gcu_pm_btn
        elif cmd_id == 1: btn = self.gcu_dxn_btn
        elif cmd_id == 2: btn = self.gcu_dxd_btn
        elif cmd_id == 3: btn = self.gcu_lt_btn
        
        self.current_btn_sender = btn
        
        try:
            if cmd_id == 0: self.cmd_data.gcu_auto_off = float(self.gcu_pm_auto_tx.text())
            elif cmd_id == 1: self.cmd_data.gcu_auto_off = float(self.gcu_dxn_auto_tx.text())
            elif cmd_id == 2: self.cmd_data.gcu_auto_off = float(self.gcu_dxd_auto_tx.text())
            elif cmd_id == 3: self.cmd_data.gcu_auto_off = float(self.gcu_lt_auto_tx.text())
        except: self.cmd_data.gcu_auto_off = 0.0
        
        # Read values from new widgets
        try: self.cmd_data.gcu_dx = float(self.gcu_pm_tx.text())
        except: self.cmd_data.gcu_dx = 0.0
        
        try: self.cmd_data.gcu_dxn = float(self.gcu_dxn_time_tx.text())
        except: self.cmd_data.gcu_dxn = 0.0
        
        try: self.cmd_data.gcu_dxd = float(self.gcu_dxd_time_tx.text())
        except: self.cmd_data.gcu_dxd = 0.0
        
        try: self.cmd_data.gcu_lt = float(self.gcu_lt_time_tx.text())
        except: self.cmd_data.gcu_lt = 0.0
        
        if cmd_id == 1: # DXN
            try: 
                val = int(self.gcu_dxn_cnt_tx.text())
                if val < 2: val = 2
                if val > 5: val = 5
                self.cmd_data.gcu_cnt_dxn = val
                self.gcu_dxn_cnt_tx.setText(str(val))
            except: pass
        elif cmd_id == 2: # DXD
            try:
                val = int(self.gcu_dxd_cnt_tx.text())
                if val < 6: val = 6
                if val > 10: val = 10
                self.cmd_data.gcu_cnt_dxd = val
                self.gcu_dxd_cnt_tx.setText(str(val))
            except: pass

        self.cmd_data.gcu_cmd_flag = cmd_id + 1 # Original logic used 1-based IDs for send_gcu? 
        self.cmd_data.gcu_cmd_flag = cmd_id + 1
        self.worker.send_command(self.cmd_data)
        self.cmd_data.gcu_cmd_flag = 0

    def send_gcu(self, cmd_id, btn):
        self.current_btn_sender = btn
        
        try: self.cmd_data.gcu_dx = float(self.st_dx.time_val.text())
        except: self.cmd_data.gcu_dx = 0.0
        try: self.cmd_data.gcu_dxn = float(self.st_dxn.time_val.text())
        except: self.cmd_data.gcu_dxn = 0.0
        try: self.cmd_data.gcu_dxd = float(self.st_dxd.time_val.text())
        except: self.cmd_data.gcu_dxd = 0.0
        try: self.cmd_data.gcu_lt = float(self.st_lt.time_val.text())
        except: self.cmd_data.gcu_lt = 0.0
        
        if cmd_id == 2:
            try: 
                val = int(self.st_dxn.count_val.text())
                if val < 2: val = 2
                if val > 5: val = 5
                self.cmd_data.gcu_cnt_dxn = val
                self.st_dxn.count_val.setText(str(val))
            except: pass
        elif cmd_id == 3:
            try:
                val = int(self.st_dxd.count_val.text())
                if val < 6: val = 6
                if val > 10: val = 10
                self.cmd_data.gcu_cnt_dxd = val
                self.st_dxd.count_val.setText(str(val))
            except: pass

        self.cmd_data.gcu_cmd_flag = cmd_id
        self.worker.send_command(self.cmd_data)
        self.cmd_data.gcu_cmd_flag = 0

    def on_send_status(self, success):
        if self.current_btn_sender:
            if success:
                self.current_btn_sender.setStyleSheet("background-color: #008800; color: white; border: 1px solid #005500; font-weight: bold;")
                if self.cmd_data.btn_flags != 0:
                    self.cmd_data.btn_flags = 0
            else:
                self.current_btn_sender.setStyleSheet("background-color: #cc0000; color: white; border: 1px solid #880000; font-weight: bold;")
            
            self.btn_reset_timer.start(1000)

    def reset_btn_color(self):
        if self.current_btn_sender:
            if self.current_btn_sender == self.btn_ok:
                self.current_btn_sender.setStyleSheet("background-color:#ccffcc; color:black; font-weight:bold; font-size:14px; border:1px solid #008800;")
            else:
                self.current_btn_sender.setStyleSheet("background-color: #e0e0e0; border: 1px solid #999; border-radius: 3px; font-weight: bold;")
            self.current_btn_sender = None

    def grp(self, t):
        g = QGroupBox(t.upper()); 
        g.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        l = QVBoxLayout(); 
        l.setSpacing(1); 
        l.setContentsMargins(4,10,4,4); 
        l.setAlignment(Qt.AlignTop)
        g.setLayout(l); 
        return g

    def lbl_row(self, gb, t, d, k):
        w = LabelRow(t,"",k); w.set_val(d); gb.layout().addWidget(w); self.map_val[k]=w

    def lbl_row_wide(self, gb, t, d, k):
        w = LabelRow(t,"",k)
        w.val.setFixedWidth(120) 
        w.set_val(d)
        gb.layout().addWidget(w)
        self.map_val[k]=w

    def lbl_row_manual(self, l, t, d, k):
        w = LabelRow(t,"",k); w.set_val(d); l.addWidget(w); self.map_val[k]=w
    
    def lbl_row_grid(self, g, r, c, t, d, k):
        w = LabelRow(t,"",k); w.set_val(d); g.addWidget(w, r, c); self.map_val[k]=w

    def add_section_header(self, grid, r, c, text, span=3):
        l = QLabel(text)
        l.setStyleSheet("color: blue; font-weight: bold; padding-top: 5px;")
        grid.addWidget(l, r, c, 1, span)

    def setting_row(self, gb, t, d):
        w = SettingRow(t,""); w.val.setText(d); gb.layout().addWidget(w); return w

    def add_inp(self, l, t, m, bit=-1, udp_key=None):
        if m: 
            w = InputRow(t,"")
            if bit >= 0:
                w.btn.clicked.connect(lambda: self.toggle_ttdd_flag(w.btn, bit))
                if udp_key: self.map_auto_fields[udp_key] = w
        else: 
            w = InputRow(t,"",has_btn=False)
        l.addWidget(w); return w
        
    def add_inp_grid(self, g, r, c, t, m, bit=-1, udp_key=None):
        if m: 
            w = InputRow(t,"")
            if bit >= 0:
                w.btn.clicked.connect(lambda: self.toggle_ttdd_flag(w.btn, bit))
                if udp_key: self.map_auto_fields[udp_key] = w
        else: 
            w = InputRow(t,"",has_btn=False)
        g.addWidget(w, r, c); return w

    def add_inp_aux(self, grid, r, c, t):
        w = InputRow(t,"",has_btn=False)
        grid.addWidget(w, r, c)
        return w

    def complex_group_content(self, gb, k1,k2,k3,k4):
        self.complex_content_manual(gb.layout(), k1,k2,k3,k4)

    def complex_content_manual(self, l, k1,k2,k3,k4):
        # Clean Grid Style with Distinguishing Borders
        
        # --- FRAME 1 (Tầm/Vị trí) ---
        wt = QWidget()
        wt.setObjectName("FrameContent")
        # Add border to distinguish Tầm section
        wt.setStyleSheet("border: 1px solid #bbb; border-radius: 4px; background-color: #f9f9f9;")
        
        lt = QGridLayout(wt)
        lt.setContentsMargins(5, 5, 5, 5) # Add padding inside the border
        lt.setSpacing(5)
        
        # Headers
        l_tam = QLabel("Tầm"); l_tam.setStyleSheet("font-weight: bold; border: none;")
        l_vitri = QLabel("Vị trí (mrad)"); l_vitri.setStyleSheet("border: none;")
        l_tocdo = QLabel("Tốc độ (mrad/s)"); l_tocdo.setStyleSheet("border: none;")
        
        # Values
        def val_cell():
            v = QLineEdit("0.00")
            v.setReadOnly(True)
            v.setFixedWidth(110)
            v.setAlignment(Qt.AlignCenter)
            v.setStyleSheet("border: 1px solid #ccc; background-color: #fff; color: black; font-weight: bold;")
            return v

        v1 = val_cell()
        v2 = val_cell()
        
        lt.addWidget(l_tam, 0, 0, 2, 1, Qt.AlignVCenter)
        lt.addWidget(l_vitri, 0, 1)
        lt.addWidget(v1, 0, 2)
        lt.addWidget(l_tocdo, 1, 1)
        lt.addWidget(v2, 1, 2)
        
        l.addWidget(wt)
        
        # Spacing between groups instead of line
        l.addSpacing(5)
        
        # --- FRAME 2 (Hướng/Vị trí) ---
        wh = QWidget()
        wh.setObjectName("FrameContent")
        wh.setStyleSheet("border: 1px solid #bbb; border-radius: 4px; background-color: #f9f9f9;")
        
        lh = QGridLayout(wh)
        lh.setContentsMargins(5, 5, 5, 5)
        lh.setSpacing(5)
        
        l_huong = QLabel("Hướng"); l_huong.setStyleSheet("font-weight: bold; border: none;")
        l_vitri_h = QLabel("Vị trí (mrad)"); l_vitri_h.setStyleSheet("border: none;")
        l_tocdo_h = QLabel("Tốc độ (mrad/s)"); l_tocdo_h.setStyleSheet("border: none;")
        
        v3 = val_cell()
        v4 = val_cell()
        
        lh.addWidget(l_huong, 0, 0, 2, 1, Qt.AlignVCenter)
        lh.addWidget(l_vitri_h, 0, 1)
        lh.addWidget(v3, 0, 2)
        lh.addWidget(l_tocdo_h, 1, 1)
        lh.addWidget(v4, 1, 2)
        
        l.addWidget(wh)
        
        self.map_val[k1]=v1; self.map_val[k2]=v2; self.map_val[k3]=v3; self.map_val[k4]=v4

    def v_line(self):
        f=QFrame(); f.setFrameShape(QFrame.VLine); f.setFrameShadow(QFrame.Sunken); f.setStyleSheet("color:#ccc"); return f
    def btn_icon(self,t):
        b=QPushButton(t); b.setFixedSize(30,26); return b

    def send_ammo_config(self):
        try:
             val = int(self.gcu_ammo_tx.text())
        except: val = 0
        self.cmd_data.gcu_total_ammo = val # Assuming this maps to sodanconlai setting? Or a new field?
        # Mock doesn't seem to have a specific "Set Ammo" field other than maybe re-using something?
        # The struct `cGCU` doesn't have `sodanconlai` as a SETTABLE field, it's in SHARE.
        # Wait, `cGCU` has `SovienDXN`, `SovienDXD`. 
        # Maybe `nhapsodan` in `cTtddData`?
        self.cmd_data.nhapsodan = float(val)
        self.current_btn_sender = self.btn_send_ammo
        self.worker.send_command(self.cmd_data)

    def toggle_bypass_lvdt(self):
        # bit 0 of something?
        # cGCU has `BypassLvdt`.
        val = 1 if self.cb_bypass_lvdt.isChecked() else 0
        self.cmd_data.gcu_bypass_lvdt = val # Need to ensure CommandData has this
        self.worker.send_command(self.cmd_data)
        
    def update_ui(self):
        d = self.worker.get_data()
        last_ts = d.get('_timestamp', 0)
        is_connected = (time.time() - last_ts) < config.CONNECTION_TIMEOUT
        
        # 1. Connection & State
        if not is_connected:
            self.map_val["gcu_conn"].set_connection_status(False)
            self.map_val["dcu_conn"].set_connection_status(False)
            self.map_val["sight_conn"].set_connection_status(False)
            self.map_val["cp_conn"].set_connection_status(False)
            
        if is_connected:
            if not self.handshake_acked:
                self.handshake_acked = True
                self.init_timer.stop()
            
        if 'gcu_conn_state' in d:
             state_val = d['gcu_conn_state']
             jam_state = d.get('gcu_jam_state', 0)
             if jam_state == 1:
                 self.lbl_gcu_state.setText("KẸT ĐẠN")
                 self.lbl_gcu_state.setStyleSheet("color: red; font-weight: bold; border: 1px solid red; background-color: #ffcccc; border-radius: 3px;")
             else:
                 self.lbl_gcu_state.setText(GCU_STATE_MAP.get(state_val, str(state_val)))
                 self.lbl_gcu_state.setStyleSheet("color: blue; font-weight: bold; border: 1px solid #999; background-color: #e0e0e0; border-radius: 3px;") # Default RO style
             
        if 'gcu_mode' in d:
                mode_val = d['gcu_mode']
                self.lbl_gcu_mode.setText(mode_val)

        # 2. Common Fields
        if 'gcu_curr' in d: self.lbl_gcu_curr.setText(f"{d['gcu_curr']:.3f}")
        
        # Sensors (Using struct fields)
        # vitribekhoanongdau -> Prox BD
        if 'gcu_prox_bd' in d: self.lbl_gcu_prox_bd.setText(str(d['gcu_prox_bd']))
        # vitribekhoanongcuoi -> Prox LD
        if 'gcu_prox_ld' in d: self.lbl_gcu_prox_ld.setText(str(d['gcu_prox_ld']))
        # Limit (RCS_Limit?)
        if 'gcu_limit' in d: 
             self.lbl_gcu_limit.setText(d['gcu_limit'])

        # 3. Ammo - Moved to sync_inputs
        # 4. Mode Table Verification - Moved to sync_inputs


        # 5. Bullet Table
        if 'gcu_bullet_list' in d:
            lst = d['gcu_bullet_list']
            self.bullet_table.setRowCount(20)
            for i in range(20):
                self.bullet_table.setRowHeight(i, 20)
                self.bullet_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
                if i < len(lst) and lst[i] > 0:
                     self.bullet_table.setItem(i, 1, QTableWidgetItem(f"{lst[i]:.1f}"))
                else:
                     self.bullet_table.setItem(i, 1, QTableWidgetItem(""))
        
        # 6. Autom Update for other fields
        if 'sys_ctrl_mode' in d:
            is_aux = (d['sys_ctrl_mode'] == 5)
            # Enable if System Mode is 5 OR Checkbox is Checked
            should_enable = is_aux or self.cb_enable_aux.isChecked()
            self.group_aux.setEnabled(should_enable)
            
            if is_aux and not self.last_aux_mode:
                self.cb_sync.setChecked(True) # Optional: default sync on?
                self.cb_load.setChecked(False)
            
            self.last_aux_mode = is_aux
        
        if not is_connected:
            self.initial_sync_done = False # Reset for next connection
            
        if d.get('gcu_fire_flag', 0) == 1:
            self.cached_fire_time = QDateTime.currentDateTime().toString("HH:mm:ss")
        if 'gcu_time' in self.map_val:
             self.map_val['gcu_time'].set_val(self.cached_fire_time)


        ctrl_str = str(d.get('sys_ctrl_str', '')).upper()
        jam_state = d.get('gcu_jam_state', 0)
        
        if jam_state == 1:
            self.fire_overlay.start_effect('yellow')
            self.start_shake()
        elif "FIRE" in ctrl_str:
            self.fire_overlay.start_effect('red')
            self.start_shake()
        else:
            self.fire_overlay.stop_effect()
            self.stop_shake()

        self.lbl_time.setText(QDateTime.currentDateTime().toString("HH:mm:ss - dd/MM/yyyy"))

    def on_toggle_gcu_inside(self, checked):
        self.cmd_data.is_gcu_inside = 1 if checked else 0
        self.worker.send_command(self.cmd_data)

    def on_toggle_bandon(self, checked):
        if checked:
            self.cmd_data.feature_flags |= (1 << 3)
        else:
            self.cmd_data.feature_flags &= ~(1 << 3)
        self.worker.send_command(self.cmd_data)

    def on_toggle_aux_enable(self, checked):
        # Trigger update of visibility immediately
        # Use existing logic by checking against last known mode if needed, 
        # or simplified:
        self.group_aux.setEnabled(checked)
        # However, update_ui might overwrite this if running.
        # But update_ui now checks "is_aux or cb_enable_aux.isChecked()", so it persists.
