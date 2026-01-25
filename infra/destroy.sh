#!/bin/bash
set -e

echo "🗑️  Destroying FastAPI Gateway Stack"
echo "===================================="

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK is not installed."
    exit 1
fi

echo -e "${YELLOW}⚠️  This will destroy all resources in the FastApiGatewayStack${NC}"
read -p "Are you sure? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo -e "${RED}🗑️  Destroying stack...${NC}"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

cdk destroy --force

echo ""
echo -e "${RED}✅ Stack destroyed successfully${NC}"
