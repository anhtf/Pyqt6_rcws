#!/bin/bash

# Lấy đường dẫn thư mục hiện tại của script (chính là rcws_3)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Chuyển đến thư mục rcws_3 để chạy build
cd "$DIR" || exit

# Build file chạy bản mới nhất
echo "Đang build file chạy bản mới nhất..."
python3 build_exe.py

# Kiểm tra xem build có thành công không
if [ $? -ne 0 ]; then
    echo "Lỗi: Build thất bại. Không tạo shortcut."
    exit 1
fi

# Đường dẫn tới file thực thi và icon
EXEC_PATH="$DIR/dist/rcws"
ROOT_DIR="$(dirname "$DIR")"
ICON_PATH="$(realpath "$ROOT_DIR/images.jpeg")"

# Đường dẫn Desktop của người dùng hiện tại
DESKTOP_DIR="$HOME/Desktop"
SHORTCUT_PATH="$DESKTOP_DIR/RCWS.desktop"

# Tạo file .desktop
cat <<EOL > "$SHORTCUT_PATH"
[Desktop Entry]
Name=RCWS
Comment=Remote Controlled Weapon Station
Exec=env QT_QPA_PLATFORM=xcb "$EXEC_PATH"
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;
EOL

# Cấp quyền thực thi cho file .desktop
chmod +x "$SHORTCUT_PATH"

echo "Đã tạo shortcut tại $SHORTCUT_PATH"
echo "Hãy ra Desktop, click chuột phải vào file RCWS.desktop và chọn 'Allow Launching' (Cho phép khởi chạy) nếu cần thiết."
