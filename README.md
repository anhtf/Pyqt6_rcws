# RCWS - Radio Communication & Wireless System

A professional PyQt5-based GUI application for radio communication and wireless system monitoring, control, and management.

> ⚠️ **DISCLAIMER:** Đây chỉ là bản demo, k có ý nghĩa thực tế hay bí mật quân sự, công việc tại viettel

<img width="1920" height="1080" alt="Screenshot from 2026-03-30 10-42-25" src="https://github.com/user-attachments/assets/e135be38-929b-4b8f-ac33-0bf1b2f08fd0" />

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [License](#license)

## Overview

RCWS (Radio Communication & Wireless System) is a comprehensive desktop application designed for monitoring and controlling wireless communication systems. It provides real-time data streaming, protocol management, and system deployment capabilities with a professional UI interface.

## Features

✨ **Core Features:**
- 🔐 Secure authentication and login system
- 📡 UDP-based network communication
- 🎬 RTSP video streaming integration
- 🎮 Real-time control interface with multiple control tabs
- 📊 Live data monitoring and visualization
- 🔧 Firmware management and updates
- 🎛️ System tuning and parameter adjustment
- 📝 Session logging and data recording (CSV format)
- 🌐 Multi-platform support (Linux & Windows)
- 📱 High-DPI display scaling support

## System Requirements

**Hardware:**
- CPU: Dual-core processor or higher
- RAM: 2 GB minimum (4 GB recommended)
- Disk: 500 MB free space

**Software:**
- Python 3.7 or higher
- PyQt5 5.15.0+
- VLC libraries (for video streaming)
- SSH/SFTP support via Paramiko

## Installation

### 1. Clone or Download the Project

```bash
cd /path/to/rcws_3
```

### 2. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or individually
pip install PyQt5>=5.15.0
pip install python-vlc>=3.0.0
pip install paramiko>=2.7.0
```

### 3. Review Configuration

Edit `src/config.py` to set your system parameters:
- UDP IP and port settings
- RTSP stream URLs
- Deployment paths
- Login credentials

## Usage

### Starting the Application

```bash
python src/main.py
```

### Application Tabs

1. **Login Tab** - User authentication and session management
2. **Control Tab** - Real-time system control and command execution
3. **Streaming Tab** - RTSP video stream viewing
4. **Tuning Tab** - System parameter adjustment
5. **Firmware Tab** - Firmware management and updates

### Session Logging

All sessions are automatically logged to `logs/` directory with timestamped CSV files:
- Format: `Session_YYYYMMDD_HHMMSS_[RX|TX]_001.csv`
- Contains communication data and system metrics

## Project Structure

```
rcws_3/
├── src/                              # Main application source code
│   ├── main.py                       # Application entry point
│   ├── config.py                     # Configuration settings
│   ├── setup_run.py                  # Initialization script
│   ├── core/                         # Core functionality modules
│   │   ├── comms.py                  # UDP communication worker
│   │   ├── constants.py              # Application constants
│   │   ├── definitions.py            # Data definitions
│   │   ├── logger.py                 # Session logging
│   │   └── protocol.py               # Communication protocol
│   └── ui/                           # UI components
│       ├── app_window.py             # Main window
│       ├── components.py             # Reusable UI components
│       ├── ip_scanner.py             # IP scanning utility
│       └── tabs/                     # Application tabs
│           ├── login_tab.py
│           ├── control_tab.py
│           ├── streaming_tab.py
│           ├── tuning_tab.py
│           └── firmware_tab.py
├── helpers/                          # Utility modules
│   ├── paths.py                      # Path utilities
│   ├── test_base32.py                # Base32 encoding tests
│   ├── test_css.py                   # CSS utilities
│   └── test_radio.py                 # Radio protocol tests
├── deploy/                           # Deployment scripts and tools
│   ├── build_exe.py                  # Executable builder
│   ├── create_shortcut.sh            # Shortcut creation script
│   ├── rcws.spec                     # PyInstaller specification
│   └── setup.sh                      # Setup script
├── docs/                             # Documentation
├── logs/                             # Session logs (auto-generated)
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## Configuration

### UDP Settings
Configure UDP communication in `src/config.py`:
```python
UDP_IP_BIND = "0.0.0.0"         # Bind to all interfaces
UDP_PORT_BIND = 0               # Auto-select port
UDP_IP_DEST = "127.0.0.1"       # Destination IP
UDP_PORT_DEST = 5001            # Destination port
BUFFER_SIZE = 8192              # Communication buffer size
```

### Deployment Paths
```python
DEFAULT_DEPLOY_DIR = "Desktop/App"
TARGET_PATHS = {
    "ControlApp": "Monitor/ControlApp",
    "DashboardRCWS": "Dashboard/build-DashboardRCWS-Desktop-Debug/DashboardRCWS",
    "RCWS": "rcws"
}
```

### Security
```python
LOGIN_PASSWORD = "123"          # Change this in production!
CONNECTION_TIMEOUT = 5          # Seconds
DEBUG = True                    # Set to False in production
```

## Building Standalone Executable

For Windows deployment:

```bash
cd deploy/
bash setup.sh
```

This will create a standalone executable in the `build/` directory.

## Troubleshooting

**Issue:** Application won't start on Linux
- Solution: Ensure `QT_QPA_PLATFORM` environment variable is set to "xcb"

**Issue:** RTSP stream not displaying
- Solution: Verify RTSP URL in config.py and network connectivity

**Issue:** UDP communication fails
- Solution: Check firewall settings and UDP port availability

## Development

The project uses the following architecture:
- **PyQt5** - UI framework
- **Threading** - Concurrent UDP communication and logging
- **CSV Logging** - Session data persistence
- **QSS Stylesheets** - Professional UI theming

For modifications, ensure changes follow the existing module structure.

## License
 
