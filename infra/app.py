#!/usr/bin/env python3
"""
CDK App entry point.
This script synthesizes and deploys the FastAPI Gateway stack.
"""
import os
from aws_cdk import App, Environment
from .stacks.gateway_stack import FastApiGatewayStack

app = App()

# Get AWS account and region from environment or use defaults
account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")

env = Environment(account=account, region=region) if account else None

FastApiGatewayStack(
    app,
    "FastApiGatewayStack",
    env=env,
    description="API Gateway generated from FastAPI application with API Key authentication",
)

app.synth()
