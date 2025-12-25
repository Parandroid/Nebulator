.PHONY: help venv install run clean setup

# Default target
help:
	@echo "Nebulator - Makefile Commands:"
	@echo "  make venv      - Create virtual environment"
	@echo "  make install   - Install dependencies"
	@echo "  make run        - Run the application"
	@echo "  make clean      - Remove virtual environment"
	@echo "  make setup      - Create venv and install dependencies (all-in-one)"
	@echo ""
	@echo "Note: On Windows, you can also use setup.bat, run.bat, and clean.bat"

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Virtual environment created in ./venv"

# Install dependencies
install: venv
	@echo "Installing dependencies..."
ifeq ($(OS),Windows_NT)
	@cmd.exe /c "venv\Scripts\python.exe -m pip install --upgrade pip"
	@cmd.exe /c "venv\Scripts\python.exe -m pip install -r requirements.txt"
else
	@venv/bin/python -m pip install --upgrade pip
	@venv/bin/python -m pip install -r requirements.txt
endif
	@echo "Dependencies installed successfully!"

# Setup: create venv and install dependencies
setup: venv install
	@echo "Setup complete! Run 'make run' to start the application."

# Run the application
run:
	@echo "Starting Nebulator..."
	@echo "Open http://localhost:8000 in your browser"
ifeq ($(OS),Windows_NT)
	@cmd.exe /c "venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
else
	@venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
endif

# Clean: remove virtual environment
clean:
	@echo "Removing virtual environment..."
ifeq ($(OS),Windows_NT)
	@cmd.exe /c "if exist venv rmdir /s /q venv"
else
	@rm -rf venv
endif
	@echo "Clean complete!"
