"""
CDK Stack that dynamically generates API Gateway infrastructure from FastAPI application.
This stack introspects the FastAPI app at synthesis time and creates all necessary AWS resources.
"""
import os
import sys
from typing import Dict, Any, List
from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
)
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_logs as logs
from constructs import Construct

# Add parent directory to path to import FastAPI app
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app as fastapi_app
from .fastapi_introspector import FastAPIIntrospector, pydantic_to_api_gateway_model


class FastApiGatewayStack(Stack):
    """CDK Stack that generates API Gateway from FastAPI application."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Introspect the FastAPI application
        print("🔍 Introspecting FastAPI application...")
        self.introspector = FastAPIIntrospector(fastapi_app)
        
        print(f"📋 Found {len(self.introspector.routes)} routes")
        print(f"📦 Found {len(self.introspector.models)} models")
        
        # Create Lambda function (single function for all routes)
        # For production: can split into multiple functions by modifying this
        self.lambda_function = self._create_lambda_function()
        
        # Create API Gateway
        self.api = self._create_api_gateway()
        
        # Create API Key
        self.api_key = self._create_api_key()
        
        # Create models and integrate routes
        self._create_models_and_routes()
        
        # Outputs
        self._create_outputs()
    
    def _create_lambda_function(self) -> _lambda.Function:
        """Create the Lambda function for the FastAPI application."""
        print("🔨 Creating Lambda function...")
        
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        
        lambda_fn = _lambda.Function(
            self,
            "FastApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_handler.handler",
            code=_lambda.Code.from_asset(
                str(project_root),
                exclude=[
                    "cdk.out",
                    "infra",
                    "*.md",
                    "*.sh",
                    "cdk.json",
                    "cdk.context.json",
                    ".venv",
                    ".git",
                    ".gitignore",
                    "__pycache__",
                    "*.pyc",
                    "tests",
                ],
                bundling={
                    "image": _lambda.Runtime.PYTHON_3_11.bundling_image,
                    "command": [
                        "bash", "-c",
                        " && ".join([
                            "pip install -r infra/requirements-lambda.txt -t /asset-output --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: --upgrade --no-cache-dir",
                            "cp -r app /asset-output/",
                            "cp main.py /asset-output/",
                            "cp infra/lambda_handler.py /asset-output/",
                            "find /asset-output -type d -name '__pycache__' -exec rm -rf {} + || true",
                            "find /asset-output -type f -name '*.pyc' -delete || true",
                            "find /asset-output -type d -name 'tests' -exec rm -rf {} + || true",
                        ])
                    ],
                }
            ),
            function_name="FastApiGateway-Handler",
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "PYTHONPATH": "/var/task",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )
        
        return lambda_fn
    
    def _create_api_gateway(self) -> apigw.RestApi:
        """Create the API Gateway REST API."""
        print("🚪 Creating API Gateway...")
        
        api = apigw.RestApi(
            self,
            "FastApiGateway",
            rest_api_name=fastapi_app.title,
            description=fastapi_app.description,
            deploy_options={
                "stage_name": "prod",
                "throttling_rate_limit": 100,
                "throttling_burst_limit": 200,
                "logging_level": apigw.MethodLoggingLevel.INFO,
                "data_trace_enabled": True,
                "metrics_enabled": True,
            },
            api_key_source_type=apigw.ApiKeySourceType.HEADER,
            default_cors_preflight_options={
                "allow_origins": apigw.Cors.ALL_ORIGINS,
                "allow_methods": apigw.Cors.ALL_METHODS,
                "allow_headers": ["Content-Type", "X-Api-Key", "Authorization"],
            },
        )
        
        return api
    
    def _create_api_key(self) -> apigw.ApiKey:
        """Create API Key for authentication."""
        print("🔑 Creating API Key...")
        
        api_key = apigw.ApiKey(
            self,
            "FastApiKey",
            api_key_name=f"{fastapi_app.title}-key",
            description="API Key for FastAPI Gateway",
        )
        
        # Create usage plan
        usage_plan = apigw.UsagePlan(
            self,
            "FastApiUsagePlan",
            name=f"{fastapi_app.title}-usage-plan",
            description="Usage plan for FastAPI Gateway",
            throttle={
                """
                Deprecated stack module.
                Use infra/stacks/gateway_stack.py instead.
                """
                from .stacks.gateway_stack import FastApiGatewayStack  # noqa: F401
                "period": apigw.Period.DAY,
