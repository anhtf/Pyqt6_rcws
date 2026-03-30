
import PyInstaller.__main__
import platform
import os
import shutil

def build():
    print("Building RCWS Executable...")
    
    # Xóa sạch bản đóng gói cũ kỹ trước đó nhằm tránh rác mâu thuẫn
    if os.path.exists("dist"): shutil.rmtree("dist")
    if os.path.exists("build"): shutil.rmtree("build")

    sep = os.pathsep # Biểu diễn ngắt kết nối đường dẫn (Ví dụ: ; trên hệ thống Windows, : trên hệ thống Linux)

    # Hình thành định dạng tham số lệnh truyền vào PyInstaller
    args = [
        "../src/main.py",
        "--name=rcws",
        "--onefile",
        "--icon=../images.jpeg",
        # "--noconsole", # Bỏ chú thích dòng này ở bản hoàn chỉnh (Production) để ẩn cửa sổ console đen xì đi
        "--clean",
        
        # Thêm thư mục gốc của dự án vào đường dẫn tìm kiếm module
        # Cần thiết để PyInstaller tìm thấy gói helpers (nằm ngoài thư mục src)
        "--paths=../",
        
        # Thêm thư mục dữ liệu kèm theo (Các định dạng Assets tĩnh như Ảnh, vv...)
        "--add-data=../src/ui/logo.png" + sep + "ui",
        
        # Các thư viện ẩn Import (PyInstaller hay bị sót nếu các thư viện kia load dạng động CTypes)
        "--hidden-import=paramiko", 
        "--hidden-import=vlc",
        
        # Từ khóa bỏ qua loại trừ bớt phân vùng (Để ép giảm dung lượng tệp tin xuất nếu chắc chắn chả bao giờ chạm đến nó)
        # "--exclude-module=tkinter",
    ]
    
    PyInstaller.__main__.run(args)
    
    print("Build Complete.")
    print(f"Executable is in: {os.path.abspath('dist')}")

if __name__ == "__main__":
    build()
