#!/bin/bash
set -e

echo "🚀 Deploying FastAPI to AWS API Gateway with CDK"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK is not installed. Installing..."
    npm install -g aws-cdk
fi

# Check AWS credentials
echo -e "${BLUE}🔐 Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure'"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}
echo -e "${GREEN}✅ AWS Account: $ACCOUNT_ID${NC}"
echo -e "${GREEN}✅ AWS Region: $REGION${NC}"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt -q

# Bootstrap CDK (if not already done)
echo -e "${BLUE}🔧 Bootstrapping CDK (if needed)...${NC}"
cdk bootstrap aws://$ACCOUNT_ID/$REGION

# Synthesize CloudFormation template
echo -e "${BLUE}🏗️  Synthesizing CDK stack...${NC}"
cdk synth

# Deploy the stack
echo -e "${BLUE}🚢 Deploying to AWS...${NC}"
cdk deploy --require-approval never

# Get the API Key value
echo -e "${BLUE}🔑 Retrieving API Key...${NC}"
API_KEY_ID=$(aws cloudformation describe-stacks \
    --stack-name FastApiGatewayStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
    --output text \
    --region $REGION)

if [ -n "$API_KEY_ID" ]; then
    API_KEY_VALUE=$(aws apigateway get-api-key \
        --api-key $API_KEY_ID \
        --include-value \
        --query 'value' \
        --output text \
        --region $REGION)
    
    # Get API URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name FastApiGatewayStack \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
        --output text \
        --region $REGION)
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}API Gateway URL:${NC}"
    echo -e "${BLUE}$API_URL${NC}"
    echo ""
    echo -e "${YELLOW}API Key:${NC}"
    echo -e "${BLUE}$API_KEY_VALUE${NC}"
    echo ""
    echo -e "${YELLOW}Test your API with:${NC}"
    echo -e "${BLUE}curl -H \"x-api-key: $API_KEY_VALUE\" ${API_URL}health${NC}"
    echo ""
    echo -e "${YELLOW}Or test a TODO endpoint:${NC}"
    echo -e "${BLUE}curl -H \"x-api-key: $API_KEY_VALUE\" ${API_URL}api/v1/todos${NC}"
    echo ""
else
    echo "❌ Could not retrieve API Key. Check the CloudFormation stack outputs."
fi
