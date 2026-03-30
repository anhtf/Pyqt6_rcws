import os
import sys
import subprocess
import platform
import venv
from pathlib import Path

def main():
    # 1. Khởi tạo và thiết lập các biến đường dẫn gốc
    project_dir = Path(__file__).parent.parent.absolute()
    venv_dir = project_dir / ".venv"
    
    print(f"--- RCWS Setup & Run Script ---")
    print(f"Project Directory: {project_dir}")
    print(f"Detected OS: {platform.system()} {platform.release()}")
    print(f"Target: Cross-Platform (Windows/Linux) Setup")

    # 2. Tạo môi trường ảo (venv) nếu chưa tồn tại
    created_venv = False
    
    # Trực tiếp kiểm tra xem môi trường ảo venv có hoạt động ổn không TRƯỚC khi mặc định bỏ qua
    if venv_dir.exists():
        # Kiểm tra nhanh sự hiện diện của trình thực thi Python
        check_python = venv_dir / "bin" / "python"
        if platform.system() == "Windows":
             check_python = venv_dir / "Scripts" / "python.exe"
        
        if not check_python.exists():
            print(f"[!] Found existing .venv at {venv_dir} but it appears broken (missing python).")
            print("    Ignoring broken components to attempt clean creation/fallback.")
            # Chúng ta không nhất thiết phải xóa nó đi, hàm venv.create vẫn có quyền ghi đè, hoặc ta có thể đảo sang sử dụng Fallback
            # Tuy nhiên hàm tạo venv.create vẫn có thể bị khựng lại (fail) nếu nó đánh mất quyền tự do ghi đè file liên kết ảo (symlinks)
            # Tạm bỏ qua và đi thẳng xuống kiểm tra Logic khởi tạo
            pass
        else:
             # Môi trường ảo tồn tại nguyên vẹn, do đó bỏ qua bước khởi tạo thêm
             pass

    # Tổ chức Logic làm mềm: Giải chạy chế độ tạo mới nếu môi trường không tồn tại HOẶC file bị hỏng hóc
    should_create = False
    if not venv_dir.exists():
        should_create = True
    else:
        # Kiểm tra lại một lần nữa cho cẩn thận
        check_python = venv_dir / "bin" / "python"
        if platform.system() == "Windows":
             check_python = venv_dir / "Scripts" / "python.exe"
        if not check_python.exists():
            should_create = True

    # Chiến lược 1: Thử dùng bộ .venv với tệp liên kết symlinks (Chuẩn phổ thông)
    if should_create:
        print(f"[+] Creating virtual environment at {venv_dir}...")
        try:
            venv.create(venv_dir, with_pip=True, prompt="rcws_env")
            created_venv = True
        except Exception as e:
            print(f"[!] Standard venv creation failed: {e}")
            
            # Chiến lược 2: Thử dùng bộ .venv với tính năng sao chép chép File copy (Giải pháp phụ khi lỗi Symlink)
            print("[+] Retrying with symlinks=False (copying files)...")
            try:
                venv.create(venv_dir, with_pip=True, prompt="rcws_env", symlinks=False)
                created_venv = True
            except Exception as e2:
                print(f"[!] Local venv creation failed: {e2}")
                
                # Chiến lược 3: Chọn điểm rớt giải pháp (Fallback) quay về tạo ở ngay thư mục của máy tính (Home) / User / .rcws_envs
                home_venv_base = Path.home() / ".rcws_envs"
                home_venv_base.mkdir(parents=True, exist_ok=True)
                # Tránh thiết lập thư mục trùng đè lên nhau nếu lỡ có nhiều bản mã rcws cùng hoạt động song song
                safe_name = f"{project_dir.name}_{abs(hash(str(project_dir)))}"
                fallback_venv_dir = home_venv_base / safe_name
                
                print(f"[+] Attempting to create fallback venv at: {fallback_venv_dir}...")
                try:
                    venv.create(fallback_venv_dir, with_pip=True, prompt="rcws_env")
                    venv_dir = fallback_venv_dir # Cập nhật và chỉ đích danh lại mục tiêu đường dẫn
                    created_venv = True
                    print(f"[+] Successfully created fallback virtual environment.")
                except Exception as e3:
                     print(f"[!] Critical: All venv creation strategies failed. Last error: {e3}")
                     sys.exit(1)
    else:
        # Thuật toán ẩn :v nếu cái venv đã hỏng, hệ thống có thử lục xem có mớ Fallback lưu ở Home của lần vỡ trứng trước kia không?
        pass

    if not created_venv and not venv_dir.exists():
         # Code logic giải quyết vấn đề khi đường dẫn thư mục ảo venv thay đổi
         # Tạm bỏ qua vì thuật toán bao quát trên kia làm cứng cáp rồi
         pass 
         
    if not venv_dir.exists():
         # Xem liệu nó có nằm ngoài màn hình Home không (Phòng trường hợp chạy Fallback ở lần trước)
         home_venv_base = Path.home() / ".rcws_envs"
         safe_name = f"{project_dir.name}_{abs(hash(str(project_dir)))}"
         possible_fallback = home_venv_base / safe_name
         if possible_fallback.exists():
             venv_dir = possible_fallback
             print(f"[+] Found existing fallback virtual environment at {venv_dir}")
         else:
             # Có chạm đến khu vực này thì các chu trình phòng hộ bên trên đã lo xong hết rồi
             pass

    if not venv_dir.exists():
        print(f"[!] Error: Virtual environment not found at {venv_dir}")
        sys.exit(1)
    
    print(f"[+] Using Virtual Environment: {venv_dir}")

    # 3. Xác định phân loại thư viện thực thi dựa theo hệ điều hành OS
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"

    # Fallback soát lỗ hổng nếu file pip.exe mất tích nhưng python.exe vẫn chạy (Vì thường trên win chỉ có python.exe là luôn đủ độ lì)
    if not pip_exe.exists() and python_exe.exists():
         # Chúng ta hoàn toàn có thể chạy command bằng python -m pip thay thế
         pass

    if not python_exe.exists():
        print(f"[!] Error: Python executable not found at {python_exe}")
        print("    You may need to delete the .venv directory and try again.")
        sys.exit(1)

    # 4. Bắt đầu tải và cài đặt tự động các thư viện đi kèm
    req_file = project_dir / "requirements.txt"
    if req_file.exists():
        print("[+] Checking and installing dependencies from requirements.txt...")
        try:
            # Dùng command dạng python -m pip thao tác an toàn hơn là gọi thẳng lệnh pip ra chạy
            subprocess.check_call([str(python_exe), "-m", "pip", "install", "-r", str(req_file)])
        except subprocess.CalledProcessError as e:
            print(f"[!] Error installing dependencies: {e}")
            sys.exit(1)
    else:
        print("[!] Warning: requirements.txt not found. Skipping dependency installation.")
    
    # 5. Bước tùy chọn: Tổng kiểm tra tình trạng ứng dụng VLC trên máy
    # Chỉ là kiểm tra sơ khai, vài thiết bị phần cứng kén chọn có thể báo sai lệch
    print("[+] Checking for VLC library (basic check)...")
    try:
        # Khởi tạo thử thư viện python-vlc trong chính môi trường ảo (venv)
        check_vlc_cmd = [str(python_exe), "-c", "import vlc; print('VLC found', vlc)"]
        subprocess.check_call(check_vlc_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("    -> VLC bindings appear to work.")
    except subprocess.CalledProcessError:
        print("    [!] Warning: Could not import 'vlc'. Ensure the VLC media player is installed on your OS.")
        print("        Windows: Install local VLC application.")
        print("        Linux: 'sudo apt install vlc' or similar.")

    # 6. Giải chạy tập tin hệ thống main.py
    main_script = project_dir / "src" / "main.py"
    if not main_script.exists():
        print(f"[!] Error: main.py not found at {main_script}")
        sys.exit(1)

    print(f"[+] Launching RCWS Application ({main_script.name})...")
    print("---------------------------------------------------")
    
    # Đẩy File thực thi Python từ môi trường venv khởi chạy luôn tệp kịch bản chính của chúng ta
    try:
        subprocess.check_call([str(python_exe), str(main_script)])
    except KeyboardInterrupt:
        print("\n[+] Application stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Application exited with error code: {e.returncode}")
    
    print("---------------------------------------------------")
    print("[+] Done.")
    if platform.system() == "Windows":
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
