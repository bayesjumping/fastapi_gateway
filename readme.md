# FastAPI to CDK Gateway

A project that translates FastAPI constructs into AWS CDK API Gateway resources in an unintrusive way.

## Overview

This project allows you to define your API using FastAPI's familiar syntax and automatically generate AWS CDK infrastructure code to deploy it as an API Gateway with Lambda functions.

## Project Structure

```
fast_api_gateway/
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

### Installation

```bash
make install
source .venv/bin/activate
```

### Run the FastAPI Server

```bash
make run
```

The API will be available at http://localhost:8000

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Available Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/items` - List all items
- `GET /api/items/{item_id}` - Get specific item
- `POST /api/items` - Create new item
- `PUT /api/items/{item_id}` - Update item
- `DELETE /api/items/{item_id}` - Delete item

## Development

### Running Tests

```bash
make test
```

### Clean Up

```bash
make clean
```

## CDK Translation (Coming Soon)

The CDK translation module will parse FastAPI routes and generate corresponding API Gateway and Lambda resources automatically.
