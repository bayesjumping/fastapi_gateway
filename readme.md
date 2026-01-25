# FastAPI to CDK Gateway

Automatically deploy your FastAPI application to AWS API Gateway with Lambda, using AWS CDK.

## Overview

This project dynamically generates AWS infrastructure from your FastAPI application. No manual CDK code required - just write FastAPI as usual, and the CDK introspector reads your routes and models at deployment time to create:

- ✅ API Gateway REST API with all endpoints
- ✅ Lambda function with your code
- ✅ API Key authentication
- ✅ Request validation from Pydantic models
- ✅ Usage plans and throttling

## Project Structure

```
fastapi_gateway/
├── main.py              # FastAPI application entry point
├── app/
│   ├── __init__.py
│   ├── routers/         # API route definitions
│   │   ├── __init__.py
│   │   └── example.py   # Example router with CRUD operations
│   └── models/          # Pydantic models
│       └── __init__.py
├── requirements.txt     # Python dependencies
├── makefile            # Build and setup commands
└── .gitignore
```

## Getting Started

### Quick Setup

```bash
# Complete setup (creates venv, installs dependencies, installs CDK)
make setup

# Activate virtual environment
source .venv/bin/activate

# Configure AWS (if not already done)
aws configure

# Bootstrap CDK (first time only)
make bootstrap
```

### Run Locally

```bash
make run
```

The API will be available at http://localhost:8000

### Deploy to AWS

```bash
make deploy
```

### Run Tests

```bash
make test
```

The API will be available at http://localhost:8000

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Available Endpoints

### Health & Info
- `GET /` - Root endpoint with API information
- `GET /health` - Health check

### Todo API
- `GET /api/v1/todos` - List all todos (with filtering)
- `GET /api/v1/todos/{id}` - Get specific todo
- `POST /api/v1/todos` - Create new todo
- `PUT /api/v1/todos/{id}` - Update todo
- `PATCH /api/v1/todos/{id}/toggle` - Toggle completion status
- `DELETE /api/v1/todos/{id}` - Delete todo
- `DELETE /api/v1/todos` - Delete all completed todos

## Make Commands

```bash
make help         # Show all available commands
make setup        # Complete setup (venv + dependencies + CDK)
make install      # Install Python dependencies only
make bootstrap    # Bootstrap AWS CDK
make run          # Run FastAPI server locally
make test         # Run test suite
make deploy       # Deploy to AWS
make destroy      # Remove AWS resources
make openapi      # Generate OpenAPI schema
make clean        # Clean virtual environment
```

## Documentation

- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Full Deployment Guide](DEPLOYMENT.md) - Comprehensive documentation

## How It Works

The CDK stack dynamically introspects your FastAPI application at synthesis time to generate all AWS resources. Add a new endpoint to your FastAPI app, run `make deploy`, and it automatically appears in API Gateway!
