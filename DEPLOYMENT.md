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

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Deploy to AWS

```bash
./deploy.sh
```

This script will:
- Install all dependencies
- Bootstrap CDK in your AWS account (if needed)
- Introspect your FastAPI application
- Generate API Gateway resources dynamically
- Deploy Lambda function with your code
- Create API Key and Usage Plan
- Output the API URL and API Key

### 3. Test Your API

After deployment, you'll receive:
- **API Gateway URL**
- **API Key Value**

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

1. **`lambda_handler.py`**: Wraps FastAPI with Mangum for Lambda compatibility
2. **`infrastructure/fastapi_introspector.py`**: Introspects FastAPI app to extract routes and models
3. **`infrastructure/cdk_stack.py`**: Generates API Gateway infrastructure dynamically
4. **`cdk_app.py`**: CDK app entry point
5. **`deploy.sh`**: Automated deployment script

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
├── lambda_handler.py          # Lambda handler (NEW)
├── cdk_app.py                 # CDK app entry point (NEW)
├── cdk.json                   # CDK configuration (NEW)
├── deploy.sh                  # Deployment script (NEW)
├── destroy.sh                 # Cleanup script (NEW)
├── requirements.txt           # Python dependencies (updated with mangum)
├── app/
│   ├── models/                # Pydantic models
│   ├── routers/               # FastAPI routers
│   ├── services/              # Business logic
│   └── db/                    # Data layer
└── infrastructure/            # CDK infrastructure code (NEW)
    ├── __init__.py
    ├── fastapi_introspector.py  # FastAPI introspection utilities
    └── cdk_stack.py              # Dynamic CDK stack generator
```

## 🔧 CDK Commands

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy the stack
cdk deploy

# View differences before deployment
cdk diff

# Destroy all resources
./destroy.sh
# or
cdk destroy
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

# Check CDK bootstrap
cdk bootstrap

# View detailed logs
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
