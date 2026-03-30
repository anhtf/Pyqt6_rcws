#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$DIR")"
cd "$ROOT_DIR" || exit

echo "[SETUP] Starting VRW-V12 Setup..."

# 1. Install Python Dependencies
echo "[SETUP] Python dependencies are managed by 'setup_run.py'. Skipping global install."
echo "        Please run 'python3 src/setup_run.py' to create the environment and install dependencies."

# 2. Compile Mock Server
echo "[SETUP] Compiling RCWS_MOCK..."
if [ -d "RCWS_MOCK" ]; then
    cd RCWS_MOCK
    g++ mock.cpp -o mock -lpthread
    if [ $? -eq 0 ]; then
        echo "[SETUP] Mock Server compiled successfully (./RCWS_MOCK/mock)."
    else
        echo "[SETUP] Error compiling Mock Server."
    fi
    cd ..
else
    echo "[SETUP] Error: RCWS_MOCK directory not found."
fi

# 3. Compile Helper Tools
echo "[SETUP] Compiling Helper Tools..."
if [ -d "helpers" ]; then
    cd helpers
    if [ -f "check_size.c" ]; then
        gcc check_size.c -o check_size
        echo "[SETUP] check_size compiled."
    fi
    cd ..
fi

echo "[SETUP] Setup Complete."
echo "Run 'python3 src/main.py' to start the application."
echo "Run './RCWS_MOCK/mock' to start the simulation server."
