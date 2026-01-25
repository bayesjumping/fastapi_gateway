#!/bin/bash

echo "🎯 FastAPI to API Gateway - Quick Setup"
echo "======================================="

# Create virtual environment
echo "1️⃣  Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "2️⃣  Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "3️⃣  Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "✅ Setup complete!"
echo ""
echo "To deploy to AWS:"
echo "  ./deploy.sh"
echo ""
echo "To test locally:"
echo "  source .venv/bin/activate"
echo "  python -m uvicorn main:app --reload"
echo ""
