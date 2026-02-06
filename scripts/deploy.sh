#!/bin/bash
set -e

echo "🚀 Deploying FastAPI to AWS API Gateway with CDK"
echo "================================================"

# Change to project root
cd "$(dirname "$0")/.."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Use AWS profile from environment variable if set
if [ -n "$AWS_PROFILE" ]; then
    echo -e "${BLUE}📋 Using AWS Profile: $AWS_PROFILE${NC}"
fi

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

# Check AWS credentials (SSO or regular)
echo -e "${BLUE}🔐 Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS credentials not valid. Attempting SSO login...${NC}"
    echo -e "${BLUE}🔑 Logging into AWS SSO with profile: $AWS_PROFILE${NC}"

    aws sso login --profile $AWS_PROFILE

    # Verify credentials again
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "❌ AWS SSO login failed. Please check your configuration."
        echo "You may need to run: aws configure sso --profile $AWS_PROFILE"
        exit 1
    fi
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

# Check if deployment succeeded
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Wait a moment for stack to stabilize
sleep 5

# Get the API Key value with better error handling
API_KEY_ID=$(aws cloudformation describe-stacks \
    --stack-name FastApiGatewayStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
    --output text \
    --region $REGION 2>/dev/null)

if [ -z "$API_KEY_ID" ] || [ "$API_KEY_ID" == "None" ]; then
    echo -e "${YELLOW}⚠️  Could not retrieve API Key ID from stack outputs.${NC}"
    echo -e "${YELLOW}   Run this command to get your API details:${NC}"
    echo -e "${BLUE}   aws cloudformation describe-stacks --stack-name FastApiGatewayStack --query 'Stacks[0].Outputs'${NC}"
    exit 0
fi

API_KEY_VALUE=$(aws apigateway get-api-key \
    --api-key $API_KEY_ID \
    --include-value \
    --query 'value' \
    --output text \
    --region $REGION 2>/dev/null)

# Get API URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name FastApiGatewayStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text \
    --region $REGION 2>/dev/null)

if [ -n "$API_URL" ] && [ -n "$API_KEY_VALUE" ]; then
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
    echo ""
    echo -e "${RED}❌ Could not retrieve API details${NC}"
    echo -e "${YELLOW}Check CloudFormation console or run:${NC}"
    echo -e "${BLUE}aws cloudformation describe-stacks --stack-name FastApiGatewayStack${NC}"
fi
