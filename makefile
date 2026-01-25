.PHONY: help install venv requirements clean test run

VENV_DIR := .venv
PYTHON := /opt/homebrew/bin/python3
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

help:
	@echo "Available commands:"
	@echo "  make install      - Create venv and install all dependencies"
	@echo "  make venv         - Create Python virtual environment"
	@echo "  make requirements - Install requirements from requirements.txt"
	@echo "  make clean        - Remove virtual environment"
	@echo "  make test         - Run tests"
	@echo "  make run          - Run FastAPI development server"

install: venv requirements
	@echo "Installation complete! Activate venv with: source $(VENV_DIR)/bin/activate"

venv:
	@echo "Creating Python virtual environment..."
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(VENV_PIP) install --upgrade pip setuptools wheel

requirements: venv
	@echo "Installing requirements..."
	@$(VENV_PIP) install -r requirements.txt

clean:
	@echo "Removing virtual environment..."
	@rm -rf $(VENV_DIR)
	@rm -rf __pycache__ .pytest_cache *.pyc
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Clean complete"

test:
	@$(VENV_PYTHON) -m pytest tests/

run:
	@$(VENV_PYTHON) -m uvicorn main:app --reload
