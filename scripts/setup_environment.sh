#!/bin/bash

# Robot AI - Environment Setup Script
# ===================================
# This script sets up the complete development environment for Robot AI

set -e  # Exit on any error

echo "🤖 Robot AI - Environment Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running on Raspberry Pi
check_platform() {
    if [[ $(uname -m) == "aarch64" ]] || [[ $(uname -m) == "armv7l" ]]; then
        print_info "Detected ARM platform (Raspberry Pi)"
        export IS_RPI=true
    else
        print_info "Detected x86_64 platform (Development machine)"
        export IS_RPI=false
    fi
}

# Update system packages
update_system() {
    print_info "Updating system packages..."
    
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt upgrade -y
        print_status "System packages updated"
    else
        print_warning "apt not found, skipping system update"
    fi
}

# Install system dependencies
install_system_deps() {
    print_info "Installing system dependencies..."
    
    if command -v apt &> /dev/null; then
        sudo apt install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            cmake \
            git \
            curl \
            wget \
            nano \
            htop \
            i2c-tools \
            libopencv-dev \
            libhdf5-dev \
            libhdf5-serial-dev \
            libatlas-base-dev \
            libjasper-dev \
            libqtgui4 \
            libqt4-test \
            libgstreamer1.0-dev \
            libgstreamer-plugins-base1.0-dev
            
        print_status "System dependencies installed"
    else
        print_error "apt not found, please install dependencies manually"
    fi
}

# Install Raspberry Pi specific dependencies
install_rpi_deps() {
    if [[ "$IS_RPI" == "true" ]]; then
        print_info "Installing Raspberry Pi specific dependencies..."
        
        # Enable camera and I2C
        sudo raspi-config nonint do_camera 0
        sudo raspi-config nonint do_i2c 0
        sudo raspi-config nonint do_spi 0
        
        # Install RPi.GPIO and camera libraries
        sudo apt install -y \
            python3-rpi.gpio \
            python3-picamera2 \
            python3-libcamera \
            libraspberrypi-bin \
            libraspberrypi-dev
            
        print_status "Raspberry Pi dependencies installed"
    else
        print_warning "Not on Raspberry Pi, skipping RPi-specific setup"
    fi
}

# Setup Python virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."
    
    if [[ ! -d "robot_env" ]]; then
        python3 -m venv robot_env
        print_status "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source robot_env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    print_status "Virtual environment ready"
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    # Activate virtual environment
    source robot_env/bin/activate
    
    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        print_status "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Install ROS2 (if on Raspberry Pi)
install_ros2() {
    if [[ "$IS_RPI" == "true" ]]; then
        print_info "Installing ROS2 Humble..."
        
        # Add ROS2 repository
        sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
        
        # Install ROS2
        sudo apt update
        sudo apt install -y ros-humble-desktop
        
        # Setup ROS2 environment
        echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
        
        print_status "ROS2 Humble installed"
    else
        print_warning "Not on Raspberry Pi, skipping ROS2 installation"
        print_info "For development, install ROS2 following: https://docs.ros.org/en/humble/Installation.html"
    fi
}

# Setup directories
setup_directories() {
    print_info "Setting up project directories..."
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p data/{maps,experiences,models}
    mkdir -p config/local
    mkdir -p tests/unit
    mkdir -p tests/integration
    mkdir -p docs/api
    mkdir -p captures
    
    # Set permissions
    chmod +x scripts/*.sh
    
    print_status "Project directories created"
}

# Download AI models
download_models() {
    print_info "Downloading AI models..."
    
    # Create models directory
    mkdir -p data/models
    
    # Download YOLOv8 nano model (lightweight for RPi)
    if [[ ! -f "data/models/yolov8n.pt" ]]; then
        wget -O data/models/yolov8n.pt "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
        print_status "YOLOv8 nano model downloaded"
    else
        print_warning "YOLOv8 model already exists"
    fi
}

# Create service file for auto-start
create_service() {
    if [[ "$IS_RPI" == "true" ]]; then
        print_info "Creating systemd service for auto-start..."
        
        cat > robot-ai.service << EOF
[Unit]
Description=Robot AI Autonomous System
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/robot_env/bin
ExecStart=$(pwd)/robot_env/bin/python $(pwd)/src/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

        sudo mv robot-ai.service /etc/systemd/system/
        sudo systemctl daemon-reload
        
        print_status "Systemd service created"
        print_info "To enable auto-start: sudo systemctl enable robot-ai"
        print_info "To start service: sudo systemctl start robot-ai"
    fi
}

# Test installation
test_installation() {
    print_info "Testing installation..."
    
    # Activate virtual environment
    source robot_env/bin/activate
    
    # Test Python imports
    python3 -c "
import cv2
import numpy as np
import yaml
print('✓ Core dependencies working')
"
    
    if [[ "$IS_RPI" == "true" ]]; then
        python3 -c "
import RPi.GPIO as GPIO
print('✓ RPi.GPIO working')
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
"
    fi
    
    print_status "Installation test passed"
}

# Main setup function
main() {
    echo
    print_info "Starting Robot AI environment setup..."
    echo
    
    check_platform
    update_system
    install_system_deps
    install_rpi_deps
    setup_venv
    install_python_deps
    install_ros2
    setup_directories
    download_models
    create_service
    test_installation
    
    echo
    print_status "Robot AI environment setup complete!"
    echo
    print_info "Next steps:"
    echo "  1. Activate virtual environment: source robot_env/bin/activate"
    echo "  2. Test the system: python3 src/main.py --no-hardware --debug"
    echo "  3. Connect hardware and run: python3 src/main.py"
    echo
    
    if [[ "$IS_RPI" == "true" ]]; then
        print_info "Raspberry Pi specific:"
        echo "  - Reboot to enable camera and I2C: sudo reboot"
        echo "  - Enable auto-start: sudo systemctl enable robot-ai"
    fi
    
    echo
}

# Run main function
main "$@"