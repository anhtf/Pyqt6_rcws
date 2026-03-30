from ctypes import *
import struct

class cFlagOfData(Structure):
    _pack_ = 1
    _fields_ = [
        ("b_NhietDo", c_uint8, 1), ("b_Apsuat", c_uint8, 1),
        ("b_GioNgang", c_uint8, 1), ("b_GioDoc", c_uint8, 1),
        ("b_DoNghieng", c_uint8, 1), ("b_GocTa", c_uint8, 1),
        ("b_CuLy", c_uint8, 1), ("b_VanTocEl", c_uint8, 1),
        ("b_VanTocAz", c_uint8, 1), ("backup", c_uint8, 7),
    ]

class cTargetInfo(Structure):
    _pack_ = 1
    _fields_ = [("fSpeedEl", c_float), ("fSpeedAz", c_float)]

class cFeatureTTDD(Structure):
    _pack_ = 1
    _fields_ = [
        ("b_CTChuyenDoi", c_uint8, 1), 
        ("b_BuDanDao", c_uint8, 1),
        ("b_AutoLoF", c_uint8, 1), 
        ("b_Chedobandon", c_uint8, 1),
        ("backup", c_uint8, 4),
    ]

class cTtddData(Structure):
    _fields_ = [
        ("fBuTam", c_float), ("fBuHuong", c_float),
        ("fHTam", c_float), ("fHHuong", c_float),
        ("fGocNgamTam", c_float), ("fGocNgamHuong", c_float),
        ("fNhietdo", c_float), ("fApsuat", c_float),
        ("fGiongang", c_float), ("fGiodoc", c_float),
        ("fDoNghieng", c_float), ("fSoTocDauNong", c_float),
        ("fGocNay", c_float), ("fDoCongNong", c_float),
        ("fGocTa", c_float),
        ("fSuaDauGuongTam", c_float), ("fSuaDauGuongHuong", c_float),
        ("fSuaTamZeroing", c_float), ("fSuaHuongZeroing", c_float),
        ("fCulyHieuChinh", c_float),
        ("iMode", c_int),
        ("nhapsodan", c_float), 
        ("cambantam", c_float),
        ("cambanhuong", c_float),
        ("sTargetInfo", cTargetInfo),
        ("sFlag", cFlagOfData),
        ("sFeature", cFeatureTTDD),
        ("FlagChedoHieuchinh", c_float),
    ]

class S_TTDD_DATA(Structure):
    _pack_ = 1
    _fields_ = [
        ("fBuTam", c_float), ("fBuHuong", c_float),
        ("fHTam", c_float), ("fHHuong", c_float),
        ("fGocNgamTam", c_float), ("fGocNgamHuong", c_float),
        ("fNhietdo", c_float), ("fApsuat", c_float),
        ("fGiongang", c_float), ("fGiodoc", c_float),
        ("fDoNghieng", c_float), ("fSoTocDauNong", c_float),
        ("fGocNay", c_float), ("fDoCongNong", c_float),
        ("fGocTa", c_float),
        ("fSuaDauGuongTam", c_float), ("fSuaDauGuongHuong", c_float),
        ("fSuaTamZeroing", c_float), ("fSuaHuongZeroing", c_float),
        ("fCulyHieuChinh", c_float),
        ("iMode", c_int),
        ("fAlpha", c_float),
        ("sTargetInfo", cTargetInfo),
        ("sFlag", cFlagOfData),
        ("sFeature", cFeatureTTDD),
    ]

class cButtonHMI(Structure):
    _pack_ = 1
    _fields_ = [
        ("SavedFlag", c_uint8, 1),
        ("GotoSaved", c_uint8, 1),
        ("CtrlByRate", c_uint8, 1),
        ("ElUp", c_uint8, 1),
        ("ElDown", c_uint8, 1),
        ("AzUp", c_uint8, 1),
        ("AzDown", c_uint8, 1),
        ("backup", c_uint8, 1),
        ("Rate", c_float),
        ("fDposEl_TC", c_float),
        ("fDposAz_TC", c_float),
    ]

class cGCU(Structure):
    _pack_ = 1
    _fields_ = [
        ("Time_DX", c_uint16),
        ("Time_DXN", c_uint16),
        ("Time_DXD", c_uint16),
        ("Time_LT", c_uint16),
        ("Time_Auto_Off", c_uint16),
        ("SovienDXN", c_uint16),
        ("SovienDXD", c_uint16),
        ("_ConfigFlag", c_uint8),
        ("BurstCount", c_uint16),
        ("BypassLvdt", c_uint8),
        ("flagResetChukidan", c_uint8),
        ("is_gcu_inside", c_uint8),
    ]

# ==========================================
# CÁC CẤU TRÚC ĐỂ GỬI ĐI (SEND STRUCTURES)
# ==========================================

class sMessageFromAppTTDD(Structure):
    _pack_ = 1
    _fields_ = [
        ("sTTDD", cTtddData),
        ("sBtn", cButtonHMI),
        ("sGCU", cGCU),
        ("Alpha", c_float),
        ("u8CheckSum", c_uint8),
    ]

# ==========================================
# CÁC CẤU TRÚC ĐỂ NHẬN VỀ (RECEIVE STRUCTURES)
# ==========================================

class S_BUTTON_HW_SHARE(Structure):
    _pack_ = 1
    _fields_ = [("is_connected", c_uint8, 1), ("backup", c_uint8, 7)]

class S_DCU_SHARE(Structure):
    _pack_ = 1
    _fields_ = [
        ("is_connected", c_uint8, 1), ("backup", c_uint8, 7),
        ("dcu_temp", c_uint8), ("dcu_ilimited", c_uint8),
        ("dcu_error_code", c_uint16),
    ]

class S_GCU_SHARE(Structure):
    _pack_ = 1
    _fields_ = [
        ("is_connected", c_uint8, 1),
        ("khoa_co_dien", c_uint8, 1),
        ("khoa_len_dan", c_uint8, 1), 
        ("thoi_diem_khai_hoa", c_uint8, 1),
        ("vitribekhoanongdau", c_uint8, 1),
        ("vitribekhoanongcuoi", c_uint8, 1),
        ("hetdan", c_uint8, 1),
        ("danthoi", c_uint8, 1),
        
        ("gcu_current", c_float),
        ("gcu_Time_DX", c_uint16), ("gcu_Time_DXN", c_uint16),
        ("gcu_Time_DXD", c_uint16), ("gcu_Time_LT", c_uint16),
        ("gcu_Time_Auto_Off", c_uint16),
        
        ("sodanconlai", c_uint16),
        ("dotremoivien", c_uint16),
        ("s_systemState", c_uint8),
        
        ("trekhaihoa", c_uint16 * 20),
        ("sodandaban", c_uint8),
    ]

class S_MOTOR_DRIVER_SHARE(Structure):
    _pack_ = 1
    _fields_ = [
        ("_temp_az", c_uint8), ("_temp_el", c_uint8),
        ("_error_az", c_uint32), ("_error_el", c_uint32),
    ]

# ==========================================
# ĐỊNH NGHĨA VÀ DỊCH MÃ LỖI
# ==========================================

Mean_Driver_Error = {
    # Mã lỗi phần cứng (Hardware errors)
    "m_ovcurr": "Quá dòng",
    "m_ovvolt": "Quá áp",
    "m_unvolt": "Thấp áp",
    "m_angsens": "Lỗi cảm biến góc tuyệt đối",
    "m_iasens": "Lỗi cảm biến dòng Ia",
    "m_ibsens": "Lỗi cảm biến dòng Ib",
    "m_icsens": "Lỗi cảm biến dòng Ic",
    "m_ovload": "Quá tải (I2t)",
    "m_asymmetry": "Mất cân bằng pha",
    "m_phaseloss": "Mất pha",
    "m_backup1": "Dự phòng 1",
    "m_backup2": "Dự phòng 2",
    "m_dcu_dis": "Mất kết nối DCU (10ms)",
    "m_enc_dis": "Mất kết nối Encoder (10ms)",
    
    # Mã cảnh báo (Warnings)
    "m_ovmol": "Cảnh báo quá tải",
    "m_dcu_miss_frame": "Mất gói tin DCU",
    "m_dcu_miss_10ms": "Mất tin DCU 10ms",
    "m_obs_mode": "Chế độ Quan sát",
    "m_lock_mode": "Chế độ Bám",
    "m_fire_mode": "Chế độ Bắn",
    "m_eng_mode": "Chế độ Kỹ thuật",
    "m_aux_mode": "Chế độ Phụ trợ",
    
    # Trạng thái (System states)
    "m_run": "Đang chạy",
    "m_aiming": "Đang ổn định",
    "m_pri_stabil": "Ổn định sơ cấp",
    "m_slave_stabil": "Ổn định tớ",
    "m_txdata": "Đang gửi dữ liệu",
}

Mean_DCU_Error = {
    "m_az_enc_err": "Lỗi Encoder Hướng",
    "m_az_enc_miss_10ms": "Mất tin Enc Hướng 10ms",
    "m_el_enc_err": "Lỗi Encoder Tầm",
    "m_el_enc_miss_10ms": "Mất tin Enc Tầm 10ms",
    "m_gyro_miss": "Mất tin Gyro",
    "m_gyro_miss_10ms": "Mất tin Gyro 10ms",
    "m_gyro_dis_1s": "Mất kết nối Gyro 1s",
    "m_rcs_miss": "Mất tin RCS",
    "m_rcs_miss_10ms": "Mất tin RCS 10ms",
    "m_rcs_dis_1s": "Mất kết nối RCS 1s",
    "m_az_drv_miss": "Mất tin Driver Hướng",
    "m_az_drv_miss_100ms": "Mất tin Drv Hướng 100ms",
    "m_az_drv_dis_1s": "Mất kết nối Drv Hướng 1s",
    "m_el_drv_miss": "Mất tin Driver Tầm",
    "m_el_drv_miss_100ms": "Mất tin Drv Tầm 100ms",
    "m_el_drv_dis_1s": "Mất kết nối Drv Tầm 1s",
}

class driver_error_bits(Structure):
    _fields_ = [
        ("m_ovcurr", c_uint32, 1),
        ("m_ovvolt", c_uint32, 1),
        ("m_unvolt", c_uint32, 1),
        ("m_angsens", c_uint32, 1),
        ("m_iasens", c_uint32, 1),
        ("m_ibsens", c_uint32, 1),
        ("m_icsens", c_uint32, 1),
        ("m_ovload", c_uint32, 1),
        ("m_asymmetry", c_uint32, 1),
        ("m_phaseloss", c_uint32, 1),
        ("m_backup1", c_uint32, 1),
        ("m_backup2", c_uint32, 1),
        ("m_dcu_dis", c_uint32, 1),
        ("m_enc_dis", c_uint32, 1),
        ("m_backup", c_uint32, 2),
    ]

class driver_warn_bits(Structure):
    _fields_ = [
        ("m_unused", c_uint32, 16),
        ("m_ovmol", c_uint32, 1),
        ("m_dcu_miss_frame", c_uint32, 1),
        ("m_dcu_miss_10ms", c_uint32, 1),
        ("m_obs_mode", c_uint32, 1),
        ("m_lock_mode", c_uint32, 1),
        ("m_fire_mode", c_uint32, 1),
        ("m_eng_mode", c_uint32, 1),
        ("m_aux_mode", c_uint32, 1),
    ]

class driver_state_bits(Structure):
    _fields_ = [
        ("m_unused", c_uint32, 24),
        ("m_run", c_uint32, 1),
        ("m_aiming", c_uint32, 1),
        ("m_pri_stabil", c_uint32, 1),
        ("m_slave_stabil", c_uint32, 1),
        ("m_txdata", c_uint32, 1),
        ("m_backup", c_uint32, 3),
    ]

class driver_flag_t(Union):
    _fields_ = [
        ("m_error", driver_error_bits),
        ("m_warn", driver_warn_bits),
        ("m_state", driver_state_bits),
        ("m_raw", c_uint32),
    ]

# Trạng thái DCU (DCU Status)
class dcu_status_bits(Structure):
    _fields_ = [
        ("m_az_enc_err", c_uint16, 1),
        ("m_az_enc_miss_10ms", c_uint16, 1),
        ("m_el_enc_err", c_uint16, 1),
        ("m_el_enc_miss_10ms", c_uint16, 1),
        ("m_gyro_miss", c_uint16, 1),
        ("m_gyro_miss_10ms", c_uint16, 1),
        ("m_gyro_dis_1s", c_uint16, 1),
        ("m_rcs_miss", c_uint16, 1),
        ("m_rcs_miss_10ms", c_uint16, 1),
        ("m_rcs_dis_1s", c_uint16, 1),
        ("m_az_drv_miss", c_uint16, 1),
        ("m_az_drv_miss_100ms", c_uint16, 1),
        ("m_az_drv_dis_1s", c_uint16, 1),
        ("m_el_drv_miss", c_uint16, 1),
        ("m_el_drv_miss_100ms", c_uint16, 1),
        ("m_el_drv_dis_1s", c_uint16, 1),
    ]

class dcu_status_t(Union):
    _fields_ = [
        ("m_bits", dcu_status_bits),
        ("m_raw", c_uint16),
    ]

class S_FEATURE(Structure):
    _pack_ = 1
    _fields_ = [("lazer_state", c_uint8, 1), ("batbam_state", c_uint8, 1), ("backup", c_uint8, 6)]

class S_SHARE_TO_GIAODIEN(Structure):
    _pack_ = 1
    _fields_ = [
        ("fWindSpeed", c_float), ("fWindDir", c_float),
        ("fAtm", c_float), ("fTemp", c_float), ("fHumd", c_float),
        ("fDistan", c_float), ("EleAngleTarget", c_float),
        ("KPT_ele", c_float), ("KPT_azi", c_float),
        ("V_target_El", c_float), ("V_target_Az", c_float),
        ("fAZRate", c_float), ("fAZPos", c_float),
        ("fELRate", c_float), ("fELPos", c_float),
        ("fAZRate_gyro", c_float), ("fAZPos_gyro", c_float),
        ("fELRate_gyro", c_float), ("fELPos_gyro", c_float),
        ("iTVKState", c_int), ("iTDKMode", c_int),
        ("iCheDoBan", c_int), ("iModeTTDD", c_int), ("iKPTMode", c_int),
        ("iKPTconnected", c_uint8),
        ("RCS_Limit", c_uint8),
        ("sDCU_add", S_DCU_SHARE),
        ("sGCU_add", S_GCU_SHARE),
        ("sDriver_add", S_MOTOR_DRIVER_SHARE),
        ("sFeature", S_FEATURE),
        ("sBtnHw", S_BUTTON_HW_SHARE),
        ("u8CheckSum", c_uint8),
    ]

class sMessageSendtoApp(Structure):
    _pack_ = 1
    _fields_ = [
        ("s_ShareToGiaoDien", S_SHARE_TO_GIAODIEN),
        ("s_TtddData", cTtddData),
        ("sGCU", cGCU), 
        ("Alpha", c_float),
        ("checksum", c_uint8),
    ]

# ==========================================
# LOGIC & HELPERS
# ==========================================

class CommandData:
    def __init__(self):
        self.bu_tam = 0.0
        self.bu_huong = 0.0
        self.goc_ngam_tam = 0.0
        self.goc_ngam_huong = 0.0
        self.nhiet_do = 25.0
        self.ap_suat = 750.0
        self.gio_ngang = 0.0
        self.gio_doc = 0.0
        self.do_nghieng = 0.0
        self.so_toc = 0.0
        self.goc_nay = 0.0
        self.do_cong_nong = 0.0
        self.goc_ta = 0.0
        self.cu_ly = 0.0
        self.vt_mt_el = 0.0
        self.vt_mt_az = 0.0
        
        self.h_tam = 0.0
        self.h_huong = 0.0
        self.sua_dau_guong_tam = 0.0
        self.sua_dau_guong_huong = 0.0
        self.sua_tam_zero = 0.0
        self.sua_huong_zero = 0.0
        self.cu_ly_hieu_chinh = 0.0

        self.ttdd_flags = 0
        self.feature_flags = 0

        self.gcu_dx = 30.0
        self.gcu_dxn = 150.0
        self.gcu_dxd = 450.0
        self.gcu_lt = 10000.0
        self.gcu_auto_off = 0.0
        self.gcu_cnt_dxn = 3
        self.gcu_cnt_dxd = 8
        self.gcu_total_ammo = 0
        self.gcu_cmd_flag = 0 
        self.gcu_bypass_lvdt = 0
        self.flagResetChukidan = 0
        self.is_gcu_inside = 0
        
        self.iMode = 0
        self.nhapsodan = 20
        self.cambantam = 0.0
        self.cambanhuong = 0.0
        self.flag_chedo_hieuchinh = 0.0

        self.tc_dpos_el = 0.0
        self.tc_dpos_az = 0.0
        self.btn_flags = 0 

class ProtocolHandler:
    @staticmethod
    def calculate_checksum(struct_obj):
        ptr = cast(byref(struct_obj), POINTER(c_uint8))
        size = sizeof(struct_obj)
        checksum = 0
        for i in range(size - 1):
            checksum += ptr[i]
        return checksum & 0xFF

    @staticmethod
    def parse(data: bytes) -> dict:
        expected_size = sizeof(sMessageSendtoApp)
        
        if len(data) != expected_size: 
            print(f"DEBUG: Kích thước không khớp! Nhận: {len(data)}, Yêu cầu: {expected_size}")
            return {}

        rx = sMessageSendtoApp()
        memmove(byref(rx), data, expected_size)

        cal_sum = ProtocolHandler.calculate_checksum(rx)
        
        if cal_sum != rx.checksum: 
            print(f"DEBUG: Lỗi Checksum! Tính được: {cal_sum}, Nhận được: {rx.checksum}")
            return {}

        share = rx.s_ShareToGiaoDien
        echo_ttdd = rx.s_TtddData

        fire_map = {0: "PM", 1: "ĐXN", 2: "ĐXD", 3 : "LT"}
        sys_map = {0: "POWERUP", 1: "STANDBY", 2: "AIMING", 3: "PRI_STABIL", 4 : "GOTO", 5: "SLAVE_STABIL", 6: "ENGINEERING", 7: "EXCEPTION"}
        tdk_map = {0: "POWERUP", 1: "OBSERVATION", 2: "TARGET_LOCK", 3: "FIRE", 4: "ENGINEERING", 5: "AUXILIARY"}
        kpt_map = {0: "KP", 1: "PK"}

        kpt_is_connected = 1 

        return {
            "echo_bu_tam": echo_ttdd.fBuTam,
            "echo_bu_huong": echo_ttdd.fBuHuong,
            "echo_goc_ngam_tam": echo_ttdd.fGocNgamTam,
            "echo_goc_ngam_huong": echo_ttdd.fGocNgamHuong,
            "echo_nhiet_do": echo_ttdd.fNhietdo,
            "echo_ap_suat": echo_ttdd.fApsuat,
            "echo_gio_ngang": echo_ttdd.fGiongang,
            "echo_gio_doc": echo_ttdd.fGiodoc,
            "echo_do_nghieng": echo_ttdd.fDoNghieng,
            "echo_so_toc": echo_ttdd.fSoTocDauNong,
            "echo_goc_nay": echo_ttdd.fGocNay,
            "echo_do_cong_nong": echo_ttdd.fDoCongNong,
            "echo_goc_ta": echo_ttdd.fGocTa,
            "echo_cu_ly": rx.Alpha, 
            "echo_vt_mt_el": echo_ttdd.sTargetInfo.fSpeedEl,
            "echo_vt_mt_az": echo_ttdd.sTargetInfo.fSpeedAz,
            "echo_h_tam": echo_ttdd.fHTam,
            "echo_h_huong": echo_ttdd.fHHuong,
            "echo_sua_dg_tam": echo_ttdd.fSuaDauGuongTam,
            "echo_sua_dg_huong": echo_ttdd.fSuaDauGuongHuong,
            "echo_sua_tam_zero": echo_ttdd.fSuaTamZeroing,
            "echo_sua_huong_zero": echo_ttdd.fSuaHuongZeroing,
            "echo_cu_ly_hc": echo_ttdd.fCulyHieuChinh,
            "echo_cam_tam": echo_ttdd.cambantam,
            "echo_cam_huong": echo_ttdd.cambanhuong,

            "echo_gcu_dx": share.sGCU_add.gcu_Time_DX,
            "echo_gcu_dxn": share.sGCU_add.gcu_Time_DXN,
            "echo_gcu_dxd": share.sGCU_add.gcu_Time_DXD,
            "echo_gcu_lt": share.sGCU_add.gcu_Time_LT,
            "echo_gcu_auto_off": share.sGCU_add.gcu_Time_Auto_Off,
            
            "echo_gcu_cnt_dxn": rx.sGCU.SovienDXN,
            "echo_gcu_cnt_dxd": rx.sGCU.SovienDXD,
            "echo_gcu_flag": 0,

            "echo_btn_el_up": 0,
            "echo_btn_el_down": 0,
            "echo_btn_az_up": 0,
            "echo_btn_az_down": 0,
            "echo_btn_dpos_el": 0.0,
            "echo_btn_dpos_az": 0.0,
            
            "g_r_pos": share.fELPos_gyro, "g_r_spd": share.fELRate_gyro, "g_a_pos": share.fAZPos_gyro, "g_a_spd": share.fAZRate_gyro,
            "v_r_pos": share.fELPos, "v_r_spd": share.fELRate, "v_a_pos": share.fAZPos, "v_a_spd": share.fAZRate,
            
            "env_temp": share.fTemp, 
            "env_pres": share.fAtm, 
            "t_dist": share.fDistan, 
            "t_el": share.V_target_El, 
            "t_az": share.V_target_Az, 

            "cp_conn": share.sBtnHw.is_connected, 
            "cp_lock_load": share.sGCU_add.khoa_len_dan, 
            "cp_lock_trig": share.sGCU_add.khoa_co_dien,
            "gcu_fire_flag": share.sGCU_add.thoi_diem_khai_hoa,
            
            "gcu_conn_state": share.sGCU_add.s_systemState, 
            "gcu_mode": fire_map.get(share.iCheDoBan, str(share.iCheDoBan)),
            "gcu_limit": "ON" if share.RCS_Limit else "OFF", 
            "gcu_curr": share.sGCU_add.gcu_current, 
            
            "gcu_dx": share.sGCU_add.gcu_Time_DX, 
            "gcu_rem_ammo": share.sGCU_add.sodanconlai,
            "echo_gcu_total_ammo": rx.sGCU.BurstCount,
            "gcu_jam_state": share.sGCU_add.danthoi,
            "gcu_bullet_list": list(share.sGCU_add.trekhaihoa),

            "gcu_prox_bd": share.sGCU_add.vitribekhoanongdau,
            "gcu_prox_ld": share.sGCU_add.vitribekhoanongcuoi,
            
            "dcu_conn": share.sDCU_add.is_connected, 
            "gcu_conn": share.sGCU_add.is_connected,
            "dcu_temp": share.sDCU_add.dcu_temp/2, 
            "dcu_limit_curr": share.sDCU_add.dcu_ilimited, 
            "dcu_err": share.sDCU_add.dcu_error_code,
            "sys_wpn_str": sys_map.get(share.iTVKState, str(share.iTVKState)), 
            "sys_ctrl_str": tdk_map.get(share.iTDKMode, str(share.iTDKMode)),
            "sys_ctrl_mode": share.iTDKMode,
            "sys_laser": share.sFeature.lazer_state, 
            "sys_track": share.sFeature.batbam_state,
            "drv_el_temp": share.sDriver_add._temp_el/2, 
            "drv_el_err": share.sDriver_add._error_el, 
            "drv_az_temp": share.sDriver_add._temp_az/2, 
            "drv_az_err": share.sDriver_add._error_az,
            
            "sight_conn": share.iKPTconnected,
            "sight_mode": kpt_map.get(share.iKPTMode, str(share.iKPTMode)),
            "sight_el": share.KPT_ele, 
            "sight_az": share.KPT_azi, 
            "sight_el_tgt": share.EleAngleTarget,
        }

    @staticmethod
    def pack_command(cmd: CommandData) -> bytes:
        tx = sMessageFromAppTTDD()
        
        tx.sTTDD.fBuTam = cmd.bu_tam
        tx.sTTDD.fBuHuong = cmd.bu_huong
        tx.sTTDD.fHTam = cmd.h_tam
        tx.sTTDD.fHHuong = cmd.h_huong
        tx.sTTDD.fGocNgamTam = cmd.goc_ngam_tam
        tx.sTTDD.fGocNgamHuong = cmd.goc_ngam_huong
        tx.sTTDD.fNhietdo = cmd.nhiet_do
        tx.sTTDD.fApsuat = cmd.ap_suat
        tx.sTTDD.fGiongang = cmd.gio_ngang
        tx.sTTDD.fGiodoc = cmd.gio_doc
        tx.sTTDD.fDoNghieng = cmd.do_nghieng
        tx.sTTDD.fSoTocDauNong = cmd.so_toc
        tx.sTTDD.fGocNay = cmd.goc_nay
        tx.sTTDD.fDoCongNong = cmd.do_cong_nong
        tx.sTTDD.fGocTa = cmd.goc_ta
        tx.sTTDD.fSuaDauGuongTam = cmd.sua_dau_guong_tam
        tx.sTTDD.fSuaDauGuongHuong = cmd.sua_dau_guong_huong
        tx.sTTDD.fSuaTamZeroing = cmd.sua_tam_zero
        tx.sTTDD.fSuaHuongZeroing = cmd.sua_huong_zero
        tx.sTTDD.fCulyHieuChinh = cmd.cu_ly_hieu_chinh
        
        # Gán iMode và cự ly vào cấu trúc, lưu ý cự ly được truyền thẳng qua biến Alpha
        tx.sTTDD.iMode = cmd.iMode  
        tx.sTTDD.nhapsodan = cmd.nhapsodan
        tx.sTTDD.cambantam = cmd.cambantam
        tx.sTTDD.cambanhuong = cmd.cambanhuong
        tx.Alpha = cmd.cu_ly 
        
        tx.sTTDD.sTargetInfo.fSpeedEl = cmd.vt_mt_el
        tx.sTTDD.sTargetInfo.fSpeedAz = cmd.vt_mt_az
        
        tx.sTTDD.sFlag.b_Apsuat = (cmd.ttdd_flags >> 0) & 1
        tx.sTTDD.sFlag.b_DoNghieng = (cmd.ttdd_flags >> 1) & 1
        tx.sTTDD.sFlag.b_GioDoc = (cmd.ttdd_flags >> 2) & 1
        tx.sTTDD.sFlag.b_GioNgang = (cmd.ttdd_flags >> 3) & 1
        tx.sTTDD.sFlag.b_GocTa = (cmd.ttdd_flags >> 4) & 1
        tx.sTTDD.sFlag.b_NhietDo = (cmd.ttdd_flags >> 5) & 1
        tx.sTTDD.sFlag.b_CuLy = (cmd.ttdd_flags >> 6) & 1
        tx.sTTDD.sFlag.b_VanTocEl = (cmd.ttdd_flags >> 7) & 1
        tx.sTTDD.sFlag.b_VanTocAz = (cmd.ttdd_flags >> 8) & 1
        
        tx.sTTDD.sFeature.b_CTChuyenDoi = (cmd.feature_flags >> 0) & 1
        tx.sTTDD.sFeature.b_BuDanDao = (cmd.feature_flags >> 1) & 1
        tx.sTTDD.sFeature.b_AutoLoF = (cmd.feature_flags >> 2) & 1
        tx.sTTDD.sFeature.b_Chedobandon = (cmd.feature_flags >> 3) & 1

        tx.sGCU.Time_DX = int(cmd.gcu_dx)
        tx.sGCU.Time_DXN = int(cmd.gcu_dxn)
        tx.sGCU.Time_DXD = int(cmd.gcu_dxd)
        tx.sGCU.Time_LT = int(cmd.gcu_lt)
        tx.sGCU.Time_Auto_Off = int(cmd.gcu_auto_off)
        tx.sGCU.SovienDXN = int(cmd.gcu_cnt_dxn)
        tx.sGCU.SovienDXD = int(cmd.gcu_cnt_dxd)
        tx.sGCU._ConfigFlag = int(cmd.gcu_cmd_flag)
        tx.sGCU.BurstCount = int(cmd.nhapsodan)
        #int(cmd.gcu_total_ammo)
        tx.sGCU.BypassLvdt = int(cmd.gcu_bypass_lvdt)
        tx.sGCU.flagResetChukidan = cmd.flagResetChukidan
        tx.sGCU.is_gcu_inside = int(cmd.is_gcu_inside)
        
        tx.sBtn.ElUp = (cmd.btn_flags >> 0) & 1
        tx.sBtn.ElDown = (cmd.btn_flags >> 1) & 1
        tx.sBtn.AzUp = (cmd.btn_flags >> 2) & 1
        tx.sBtn.AzDown = (cmd.btn_flags >> 3) & 1
        
        tx.sBtn.fDposEl_TC = cmd.tc_dpos_el
        tx.sBtn.fDposAz_TC = cmd.tc_dpos_az
        
        tx.u8CheckSum = ProtocolHandler.calculate_checksum(tx)
        
        cmd.iMode = 0
        
        return bytearray(tx)

    @staticmethod
    def verify(cmd: CommandData, recv: dict) -> bool:
        if not recv: 
            print("[VERIFY] Chưa nhận được dữ liệu phản hồi!")
            return False
        
        EPS = 0.05 
        checks = [
            ("bu_tam", "echo_bu_tam"),
            ("bu_huong", "echo_bu_huong"),
            ("goc_ngam_tam", "echo_goc_ngam_tam"),
            ("goc_ngam_huong", "echo_goc_ngam_huong"),
            ("nhiet_do", "echo_nhiet_do"),
            ("ap_suat", "echo_ap_suat"),
            ("gio_ngang", "echo_gio_ngang"),
            ("gio_doc", "echo_gio_doc"),
            ("do_nghieng", "echo_do_nghieng"),
            ("so_toc", "echo_so_toc"),
            ("goc_nay", "echo_goc_nay"),
            ("do_cong_nong", "echo_do_cong_nong"),
            ("goc_ta", "echo_goc_ta"),
            ("cu_ly", "echo_cu_ly"),
            ("vt_mt_el", "echo_vt_mt_el"),
            ("vt_mt_az", "echo_vt_mt_az"),
            ("h_tam", "echo_h_tam"),
            ("h_huong", "echo_h_huong"),
            ("sua_dau_guong_tam", "echo_sua_dg_tam"),
            ("sua_dau_guong_huong", "echo_sua_dg_huong"),
            ("sua_tam_zero", "echo_sua_tam_zero"),
            ("sua_huong_zero", "echo_sua_huong_zero"),
            ("cu_ly_hieu_chinh", "echo_cu_ly_hc"),
            ("cambantam", "echo_cam_tam"),
            ("cambanhuong", "echo_cam_huong"),
            ("gcu_dx", "echo_gcu_dx"),
            ("gcu_dxn", "echo_gcu_dxn"),
            ("gcu_dxd", "echo_gcu_dxd"),
            ("gcu_lt", "echo_gcu_lt"),
            ("gcu_cnt_dxn", "echo_gcu_cnt_dxn"),
            ("gcu_cnt_dxd", "echo_gcu_cnt_dxd"),
            ("gcu_total_ammo", "echo_gcu_total_ammo")
        ]

        for cmd_attr, recv_key in checks:
            if cmd_attr == "gcu_total_ammo" and recv.get("sys_ctrl_mode", 0) != 5:
                continue

            cmd_val = getattr(cmd, cmd_attr, 0)
            recv_val = recv.get(recv_key, 0)
            if abs(recv_val - cmd_val) > EPS:
                print(f"[VERIFY] Mismatch {cmd_attr} ({recv_key}): R={recv_val} C={cmd_val}")
                return False

        return True