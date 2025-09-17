# Robot AI - Makefile
# ===================

.PHONY: help setup install test lint format clean run debug docs

# Default target
help:
	@echo "🤖 Robot AI - Available Commands"
	@echo "================================="
	@echo "setup     - Setup complete development environment"
	@echo "install   - Install Python dependencies only"
	@echo "test      - Run all tests"
	@echo "lint      - Run code linting"
	@echo "format    - Format code with black"
	@echo "clean     - Clean build artifacts and cache"
	@echo "run       - Run robot in production mode"
	@echo "debug     - Run robot in debug mode"
	@echo "sim       - Run robot in simulation mode (no hardware)"
	@echo "docs      - Generate documentation"
	@echo "service   - Install/start systemd service (RPi only)"

# Environment setup
setup:
	@echo "Setting up Robot AI environment..."
	./scripts/setup_environment.sh

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Testing
test:
	@echo "Running tests..."
	python -m pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v

# Code quality
lint:
	@echo "Running linting..."
	flake8 src/ tests/
	mypy src/

format:
	@echo "Formatting code..."
	black src/ tests/
	isort src/ tests/

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -name "*.log" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# Running
run:
	@echo "Starting Robot AI..."
	python3 src/main.py

debug:
	@echo "Starting Robot AI in debug mode..."
	python3 src/main.py --debug

sim:
	@echo "Starting Robot AI in simulation mode..."
	python3 src/main.py --no-hardware --debug

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "TODO: Implement documentation generation"

# Service management (Raspberry Pi)
service-install:
	@echo "Installing systemd service..."
	sudo systemctl enable robot-ai
	@echo "Service installed. Use 'make service-start' to start."

service-start:
	@echo "Starting robot service..."
	sudo systemctl start robot-ai

service-stop:
	@echo "Stopping robot service..."
	sudo systemctl stop robot-ai

service-status:
	@echo "Service status:"
	sudo systemctl status robot-ai

# Development helpers
dev-setup:
	@echo "Setting up development environment..."
	python3 -m venv robot_env
	source robot_env/bin/activate && pip install -r requirements.txt

# Quick health check
health:
	@echo "Robot AI Health Check"
	@echo "====================="
	@python3 -c "import sys; print(f'Python: {sys.version}')"
	@python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
	@python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')"
	@python3 -c "import yaml; print('YAML: OK')"
	@echo "Health check complete!"

# Hardware test
hw-test:
	@echo "Testing hardware connections..."
	@python3 -c "
try:
    import RPi.GPIO as GPIO
    print('✓ RPi.GPIO available')
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
except ImportError:
    print('⚠ RPi.GPIO not available (not on Raspberry Pi)')
except Exception as e:
    print(f'✗ GPIO error: {e}')
"