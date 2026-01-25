.PHONY: help install venv requirements clean test run deploy destroy openapi setup bootstrap

VENV_DIR := .venv
PYTHON := /opt/homebrew/bin/python3
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

help:
	@echo "Available commands:"
	@echo "  make setup        - Complete setup (install deps + CDK)"
	@echo "  make install      - Create venv and install all dependencies"
	@echo "  make venv         - Create Python virtual environment"
	@echo "  make requirements - Install requirements from requirements.txt"
	@echo "  make bootstrap    - Bootstrap AWS CDK in your account"
	@echo "  make clean        - Remove virtual environment"
	@echo "  make test         - Run tests"
	@echo "  make run          - Run FastAPI development server"
	@echo "  make deploy       - Deploy to AWS API Gateway with CDK"
	@echo "  make destroy      - Destroy the AWS CloudFormation stack"
	@echo "  make openapi      - Generate OpenAPI schema"

setup: install
	@echo "Checking for Node.js and npm..."
	@which node > /dev/null || (echo "❌ Node.js not found. Please install Node.js first." && exit 1)
	@which npm > /dev/null || (echo "❌ npm not found. Please install npm first." && exit 1)
	@echo "Installing AWS CDK CLI globally..."
	@npm install -g aws-cdk || echo "⚠️  CDK installation failed. You may need to run with sudo."
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure AWS credentials: aws configure"
	@echo "  2. Activate virtual environment: source .venv/bin/activate"
	@echo "  3. Bootstrap CDK (first time only): make bootstrap"
	@echo "  4. Deploy to AWS: make deploy"

install: venv requirements
	@echo "Installation complete! Activate venv with: source $(VENV_DIR)/bin/activate"

bootstrap:
	@echo "Bootstrapping AWS CDK..."
	@source $(VENV_DIR)/bin/activate && cdk bootstrap

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
	@echo "Running tests..."
	@$(VENV_PYTHON) -m pytest tests/ -v --tb=short

run:
	@$(VENV_PYTHON) -m uvicorn main:app --reload

deploy:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@bash ./infra/deploy.sh

destroy:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@bash ./infra/destroy.sh

openapi:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@bash ./infra/generate_openapi.sh
