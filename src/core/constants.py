
# Bảng dịch mã trạng thái của bộ điều khiển súng (GCU) sang tiếng Việt
# Mục đích: Dùng để hiển thị trạng thái lên màn hình UI cho người vận hành dễ đọc thay vì hiển thị số mã code.
GCU_STATE_MAP = {
    0: "KXĐ", 
    1: "LĐ", 
    2: "SS KH",
    3: "ĐLĐ", 
    4: "ĐLĐ", 
    5: "ĐLĐ",
    6: "KH", 
    7: "XLT", 
    8: "XLL",
    9: "XLOVC", 
    10: "MKNLVDT", 
    11: "MKNTĐK",
    12: "KĐ", 
    13: "HĐ"
}

# Hàm chuyển đổi một số nguyên sang hệ cơ số 32 (base 32).
# Cách dùng: Hàm này nhận vào một số (n), sau đó sử dụng phép chia lấy dư để tạo ra chuỗi string base 32 tương ứng.
def to_base_32(n):
    if n == 0: return "0"
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
    res = ""
    n = int(n)
    while n > 0:
        res = digits[n % 32] + res
        n //= 32
    return res
