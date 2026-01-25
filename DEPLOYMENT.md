# FastAPI to AWS API Gateway with CDK

This project automatically generates AWS CDK infrastructure code from your FastAPI application, deploying it to AWS API Gateway with Lambda integration and API Key authentication.

## 🎯 Features

- **Dynamic CDK Generation**: Reads your FastAPI code at runtime and generates API Gateway infrastructure
- **API Key Authentication**: Automatically creates and configures API Keys for secure access
- **Pydantic Validation**: Converts Pydantic models to JSON Schema for API Gateway request validation
- **Lambda Integration**: Packages and deploys your FastAPI app as AWS Lambda functions
- **Full OpenAPI Support**: Leverages FastAPI's built-in OpenAPI schema generation
- **One-Command Deployment**: Simple deployment script handles everything

## 📋 Prerequisites

- **Python 3.11+**
- **AWS CLI** configured with credentials (`aws configure`)
- **Node.js and npm** (for AWS CDK)
- **AWS CDK CLI** (`npm install -g aws-cdk`)

## 🚀 Quick Start

### 1. Complete Setup

```bash
make setup
```

This will:
- Create a virtual environment
- Install Python dependencies
- Install AWS CDK CLI globally

### 2. Configure AWS & Bootstrap CDK

```bash
# Configure AWS credentials (if not already done)
aws configure

# Activate virtual environment
source .venv/bin/activate

# Bootstrap CDK (first time only)
make bootstrap
```

### 3. Deploy to AWS

```bash
make deploy
```

This script will:
- Install all dependencies
- Bootstrap CDK in your AWS account (if needed)
- Introspect your FastAPI application
- Generate API Gateway resources dynamically
- Deploy Lambda function with your code
- Create API Key and Usage Plan

### 3. Test Your API

Test it:

```bash
# Health check
curl -H "x-api-key: YOUR_API_KEY" https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/health

# Get all todos
curl -H "x-api-key: YOUR_API_KEY" https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/v1/todos

# Create a todo
curl -X POST \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test from API Gateway","priority":"high"}' \
  https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/v1/todos
```

## 🏗️ How It Works

### Architecture

```
FastAPI App (main.py)
       ↓
CDK Introspector (reads at synth time)
       ↓
CDK Stack Generation
       ↓
API Gateway + Lambda + API Key
       ↓
Deployed Infrastructure
```

### Key Components

1. **`infra/lambda_handler.py`**: Wraps FastAPI with Mangum for Lambda compatibility
2. **`infra/fastapi_introspector.py`**: Introspects FastAPI app to extract routes and models
3. **`infra/cdk_stack.py`**: Generates API Gateway infrastructure dynamically
4. **`infra/cdk_app.py`**: CDK app entry point
5. **`infra/deploy.sh`**: Automated deployment script
6. **`infra/requirements-lambda.txt`**: Runtime-only dependencies for Lambda

### Dynamic Generation Process

At CDK synthesis time (`cdk synth`), the stack:

1. **Imports your FastAPI app** from `main.py`
2. **Introspects all routes**: Extracts HTTP methods, paths, request/response models
3. **Converts Pydantic models** to JSON Schema using `model_json_schema()`
4. **Creates API Gateway models** for request validation
5. **Generates resources and methods** with proper integration
6. **Configures API Key authentication** on all endpoints

## 📁 Project Structure

```
.
├── main.py                    # FastAPI application
├── makefile                   # Build and deployment commands
├── cdk.json                   # CDK configuration
├── pytest.ini                 # Test configuration
├── requirements.txt           # Python dependencies
├── app/
│   ├── models/                # Pydantic models
│   ├── routers/               # FastAPI routers
│   ├── services/              # Business logic
│   └── db/                    # Data layer
├── tests/                     # Test suite
│   ├── test_health.py         # Health endpoint tests
│   ├── test_models.py         # Model validation tests
│   ├── test_repository.py     # Repository tests
│   └── test_todos.py          # API endpoint tests
└── infra/                     # Infrastructure code
    ├── lambda_handler.py      # Lambda entry point
    ├── fastapi_introspector.py # Route/model introspection
    ├── cdk_stack.py           # CDK stack generator
    ├── cdk_app.py             # CDK app entry point
    ├── deploy.sh              # Deployment script
    ├── destroy.sh             # Cleanup script
    ├── generate_openapi.sh    # OpenAPI schema generator
    └── requirements-lambda.txt # Lambda runtime dependencies
```

## 🔧 Make Commands

```bash
# Show all available commands
make help

# Deploy to AWS
make deploy

# Destroy all resources
make destroy

# Run tests
make test

# Run locally
make run

# Generate OpenAPI schema
make openapi
```

### Advanced CDK Commands

```bash
# Activate virtual environment first
source .venv/bin/activate

# Synthesize CloudFormation template
cdk synth

# View differences before deployment
cdk diff

# Deploy with verbose output
cdk deploy --verbose
```

## 🔑 API Key Management

The deployment creates an API Key with usage limits:

- **Rate Limit**: 100 requests/second
- **Burst Limit**: 200 requests
- **Quota**: 10,000 requests/day

To retrieve your API Key later:

```bash
# Get API Key ID from stack outputs
aws cloudformation describe-stacks \
  --stack-name FastApiGatewayStack \
  --query 'Stacks[0].Outputs'

# Get API Key value
aws apigateway get-api-key \
  --api-key YOUR_API_KEY_ID \
  --include-value
```

## 📊 Monitoring

The deployment includes:

- **CloudWatch Logs**: Lambda execution logs (7-day retention)
- **API Gateway Metrics**: Request counts, latency, errors
- **Request Tracing**: Data trace enabled for debugging

View logs:

```bash
aws logs tail /aws/lambda/FastApiGatewayStack-FastApiHandler --follow
```

## 🛠️ Customization

### Modify API Gateway Settings

Edit `infrastructure/cdk_stack.py`:

```python
# Change throttling limits
deploy_options={
    "throttling_rate_limit": 200,  # requests/second
    "throttling_burst_limit": 400,
}

# Change Lambda timeout/memory
lambda_fn = _lambda.Function(
    timeout=Duration.seconds(60),
    memory_size=1024,
)
```

### Add More Routes

Just add them to your FastAPI app! The CDK will automatically discover and deploy them:

```python
# In app/routers/example.py or a new router
@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "Automatically deployed!"}
```

Then redeploy:

```bash
./deploy.sh
```

## 🐛 Troubleshooting

### Deployment Fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Bootstrap CDK if not already done
make bootstrap

# Try deployment again
make deploy

# View detailed logs (activate venv first)
source .venv/bin/activate
cdk deploy --verbose
```

### Lambda Errors

```bash
# View Lambda logs
aws logs tail /aws/lambda/FastApiGatewayStack-FastApiHandler --follow

# Test Lambda directly
aws lambda invoke \
  --function-name FastApiGatewayStack-FastApiHandler \
  --payload '{}' \
  response.json
```

### API Gateway 403 Errors

- Ensure you're sending the `x-api-key` header
- Verify the API Key is associated with the Usage Plan
- Check the API Key hasn't expired

## 🧹 Cleanup

To remove all AWS resources:

```bash
./destroy.sh
```

This will delete:
- API Gateway
- Lambda function
- API Keys and Usage Plans
- CloudWatch Logs
- IAM roles

## 📝 Notes

- **In-Memory Storage**: The current implementation uses in-memory storage, which resets on each Lambda cold start. For production, replace with DynamoDB.
- **Cold Starts**: First request may be slower due to Lambda cold start
- **Costs**: AWS charges apply for API Gateway, Lambda, and CloudWatch Logs
- **Region**: Default region is `us-east-1`, set `AWS_REGION` environment variable to change

## 🚧 Future Enhancements

- [ ] Add DynamoDB integration for persistent storage
- [ ] Support multiple Lambda functions (one per route)
- [ ] Add Cognito User Pool authentication
- [ ] Custom domain name support
- [ ] WAF integration
- [ ] API versioning

## 📚 Learn More

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Mangum Documentation](https://mangum.io/)

## 📄 License

MIT License - See LICENSE file for details
