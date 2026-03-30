import struct
from enum import IntEnum, Flag
from typing import NamedTuple, Optional, List

# ==============================================================================
# ENUMS
# ==============================================================================
class Command(IntEnum):
    """Mã lệnh chính."""
    TUNNING_CMD = 0x05
    DCU_TELEMETRY = 0x09

class TdkModeC(IntEnum):
    """Định nghĩa các chế độ hoạt động của hệ thống (eSystemMode)"""
    POWERUP = 0
    OBSERVATION = 1
    TARGET_LOCK = 2
    FIRE = 3
    ENGINEERING = 4
    AUXILIARY = 5
    END = 6
    
class TvkStateC(IntEnum):
    """Trạng thái hiện tại của hệ thống (eSystemState)"""
    POWERUP = 0
    STANDBY = 1
    AIMING = 2
    PRI_STABIL = 3
    GOTO = 4
    SLAVE_STABIL = 5
    ENGINEERING = 6
    EXCEPT = 7
    END = 8

class TunningFlags1(Flag):
    """Các bit trong byte control_byte_1 của sTunningData."""
    NONE = 0
    GET_FLAG = 1 << 0
    SET_FLAG = 1 << 1
    EL_AZ = 1 << 2
    AZ_DEFAULT = 1 << 5
    EL_DEFAULT = 1 << 6
    SET_RATE = 1 << 7

class TunningFlags2(Flag):
    """Các bit trong byte control_byte_2 của sTunningData."""
    NONE = 0
    GO_POS = 1 << 0
    SAVE_POS = 1 << 1
    CONTROL_POS = 1 << 2
    
class TunningLoopMode(IntEnum):
    """Giá trị cho 2 bit pos_rate_current trong control_byte_1."""
    CURRENT = 0
    RATE = 1
    POSITION = 2

# ==============================================================================
# CẤU TRÚC GÓI TIN
# ==============================================================================
class PacketBase:
    _fields: List[tuple[str, str]] = []
    _endian: str = '<'
    @classmethod
    def get_format_string(cls) -> str: return cls._endian + ''.join(f for _, f in cls._fields)
    @classmethod
    def get_size(cls) -> int: return struct.calcsize(cls.get_format_string())
    @classmethod
    def unpack(cls, buffer: bytes):
        if len(buffer) != cls.get_size(): return None
        try:
            PacketTuple = NamedTuple(cls.__name__ + 'Data', [(n, str) for n, _ in cls._fields])
            return PacketTuple(*struct.unpack(cls.get_format_string(), buffer))
        except struct.error: return None
    @classmethod
    def pack(cls, **kwargs) -> bytes:
        try:
            values = [kwargs.get(field_name, 0) for field_name, _ in cls._fields]
            return struct.pack(cls.get_format_string(), *values)
        except (KeyError, struct.error) as e: raise ValueError(f"Packing error for {cls.__name__}: {e}")

class DcuTelemetryPacket(PacketBase):
    """[CẬP NHẬT] Ánh xạ cấu trúc packet sMessageSendToRCS (Hướng từ DCU gửi lên Client)"""
    _fields = [
        ('cmd', 'B'),
        ('az_motor_driver_flags', 'I'),
        ('el_motor_driver_flags', 'I'),
        ('dcu_status_flags', 'H'),

        ('az_pos_enc_afterGear_fcbk', 'f'),     
        ('az_rate_enc_afterGear_fcbk_x10', 'h'),
        ('el_pos_enc_afterGear_fcbk', 'f'),      
        ('el_rate_enc_afterGear_fcbk_x10', 'h'),
        
        ('az_pos_enc_beforeGear_fcbk', 'f'),
        ('az_rate_enc_beforeGear_fcbk_x10', 'h'),
        ('el_pos_enc_beforeGear_fcbk', 'f'),
        ('el_rate_enc_beforeGear_fcbk_x10', 'h'),

        ('az_posCtr_ref', 'f'),
        ('el_posCtr_ref', 'f'),

        ('az_hc_pos_x10', 'h'), ('az_hc_rate_x10', 'h'),
        ('el_hc_pos_x10', 'h'), ('el_hc_rate_x10', 'h'),
        
        ('gyro_az_pos_x10', 'h'), ('gyro_az_rate_x10', 'h'),
        ('gyro_el_pos_x10', 'h'), ('gyro_el_rate_x10', 'h'),
        
        ('az_motor_udc_x10', 'h'), ('el_motor_udc_x10', 'h'),

        ('az_ia_x10', 'h'), ('az_ib_x10', 'h'), ('az_ic_x10', 'h'),
        ('el_ia_x10', 'h'), ('el_ib_x10', 'h'), ('el_ic_x10', 'h'),
        
        ('az_dpos_x10', 'h'), ('el_dpos_x10', 'h'),
        
        ('az_rate_setpoint_x10', 'h'), ('el_rate_setpoint_x10', 'h'),
        
        ('az_id_setpoint_x10', 'h'), ('az_id_feedback_x10', 'h'),
        ('el_id_setpoint_x10', 'h'), ('el_id_feedback_x10', 'h'),
        
        # Dòng điện Iq
        ('az_iq_setpoint_x10', 'h'), ('az_iq_feedback_x10', 'h'),
        ('el_iq_setpoint_x10', 'h'), ('el_iq_feedback_x10', 'h'),
        
        # Điện áp Ud, Uq
        ('az_udq0_d_x10', 'h'), ('az_udq0_q_x10', 'h'),
        ('el_udq0_d_x10', 'h'), ('el_udq0_q_x10', 'h'),
        
        # Thông số PID
        ('kp_x100', 'H'),
        ('ki_x100', 'H'),
        ('kd_x100', 'H'),
        
        # Giới hạn dòng
        ('i_limit', 'B'),
        
        # Nhiệt độ
        ('dcu_temp_x2', 'B'), ('az_driver_temp_x2', 'B'), ('el_driver_temp_x2', 'B'),
        
        # Trigger và trạng thái
        ('rcs_trigger', 'H'),
        ('e_mode_state', 'B'),
        ('counter', 'H'),
    ]

# TunningCommandPacket struct này được kế thừa từ gói sTunningData
class TunningCommandPacket(PacketBase):
    """Ánh xạ gói dữ liệu cấu hình sTunningData (Hướng từ Client cấu hình xuống DCU)"""
    _fields = [
        ('cmd', 'B'),
        ('control_byte_1', 'B'),
        ('control_byte_2', 'B'),
        ('pos_az', 'f'),
        ('pos_el', 'f'),
        ('Kp', 'h'),
        ('Ki', 'h'),
        ('Kd', 'h'),
        ('i_limit', 'B'),
        ('rate', 'f'),
        ('checksum', 'B') # Byte checksum luôn nằm cuối cùng của gói tin
    ]

def calculate_checksum(payload: bytes) -> int:
    # Logic chuẩn: Mã checksum thường bằng tổng các byte trước đó & 0xFF.
    # Mình cộng tổng toàn bộ mảng payload truyền vào rồi lấy 8 bit cuối.
    return sum(payload) & 0xFF

def get_bit(value, bit_index):
    return (value >> bit_index) & 1

def bytes_to_hex_str(byte_data: bytes) -> str:
    return ' '.join(f'0x{b:02x}' for b in byte_data)
