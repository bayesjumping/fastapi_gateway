#!/bin/bash
set -e

echo "📄 Generating OpenAPI schema..."

# Change to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Generate OpenAPI JSON from FastAPI app
python -c "from main import app; import json; print(json.dumps(app.openapi(), indent=2))" > infra/openapi.json

echo "✅ OpenAPI schema generated at infra/openapi.json"
