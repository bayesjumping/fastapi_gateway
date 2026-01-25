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
from infrastructure.fastapi_introspector import FastAPIIntrospector, pydantic_to_api_gateway_model


class FastApiGatewayStack(Stack):
    """CDK Stack that generates API Gateway from FastAPI application."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Introspect the FastAPI application
        print("🔍 Introspecting FastAPI application...")
        self.introspector = FastAPIIntrospector(fastapi_app)
        
        print(f"📋 Found {len(self.introspector.routes)} routes")
        print(f"📦 Found {len(self.introspector.models)} models")
        
        # Create Lambda function
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
                bundling={
                    "image": _lambda.Runtime.PYTHON_3_11.bundling_image,
                    "command": [
                        "bash", "-c",
                        " && ".join([
                            "pip install -r requirements.txt -t /asset-output",
                            "cp -r app /asset-output/",
                            "cp main.py /asset-output/",
                            "cp lambda_handler.py /asset-output/",
                        ])
                    ],
                }
            ),
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
                "rate_limit": 100,
                "burst_limit": 200,
            },
            quota={
                "limit": 10000,
                "period": apigw.Period.DAY,
            },
        )
        
        usage_plan.add_api_key(api_key)
        usage_plan.add_api_stage(
            stage=self.api.deployment_stage,
        )
        
        return api_key
    
    def _create_models_and_routes(self):
        """Create API Gateway models and integrate routes."""
        print("🏗️  Creating models and routes...")
        
        # Create models from Pydantic schemas
        api_models = {}
        schemas = self.introspector.get_json_schemas()
        
        for model_name, schema in schemas.items():
            print(f"  📐 Creating model: {model_name}")
            api_model = apigw.Model(
                self,
                f"Model{model_name}",
                rest_api=self.api,
                content_type="application/json",
                model_name=model_name,
                schema=apigw.JsonSchema(
                    schema=apigw.JsonSchemaVersion.DRAFT4,
                    type=apigw.JsonSchemaType.OBJECT,
                    properties={
                        k: self._convert_property_to_json_schema(v)
                        for k, v in schema.get("properties", {}).items()
                    },
                    required=schema.get("required", []),
                ),
            )
            api_models[model_name] = api_model
        
        # Create request validator
        request_validator = apigw.RequestValidator(
            self,
            "RequestValidator",
            rest_api=self.api,
            request_validator_name="request-validator",
            validate_request_body=True,
            validate_request_parameters=True,
        )
        
        # Create Lambda integration
        lambda_integration = apigw.LambdaIntegration(
            self.lambda_function,
            proxy=True,
            allow_test_invoke=True,
        )
        
        # Create routes grouped by path
        created_resources = {}
        
        for route in self.introspector.routes:
            print(f"  🛣️  Creating route: {' '.join(route.methods)} {route.path}")
            
            # Get or create the resource for this path
            resource = self._get_or_create_resource(route.path, created_resources)
            
            # Determine request model
            request_models = None
            if route.request_model and route.request_model.__name__ in api_models:
                request_models = {
                    "application/json": api_models[route.request_model.__name__]
                }
            
            # Create method for each HTTP method
            for method in route.methods:
                if method == "OPTIONS":
                    continue  # Skip OPTIONS, handled by CORS
                
                method_options = {
                    "authorization_type": apigw.AuthorizationType.NONE,
                    "api_key_required": True,
                    "request_validator": request_validator,
                }
                
                if request_models:
                    method_options["request_models"] = request_models
                
                resource.add_method(
                    method,
                    lambda_integration,
                    **method_options
                )
    
    def _get_or_create_resource(
        self, 
        path: str, 
        created_resources: Dict[str, apigw.Resource]
    ) -> apigw.Resource:
        """Get or create an API Gateway resource for the given path."""
        if path in created_resources:
            return created_resources[path]
        
        # Root path
        if path == "/" or path == "":
            created_resources[path] = self.api.root
            return self.api.root
        
        # Split path into parts
        parts = [p for p in path.split("/") if p]
        
        current_path = ""
        current_resource = self.api.root
        
        for part in parts:
            current_path += f"/{part}"
            
            if current_path in created_resources:
                current_resource = created_resources[current_path]
            else:
                # Check if it's a path parameter
                if part.startswith("{") and part.endswith("}"):
                    param_name = part[1:-1]
                    new_resource = current_resource.add_resource(
                        f"{{{param_name}}}",
                    )
                else:
                    new_resource = current_resource.add_resource(part)
                
                created_resources[current_path] = new_resource
                current_resource = new_resource
        
        return current_resource
    
    def _convert_property_to_json_schema(self, prop: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a property schema to API Gateway JsonSchema format."""
        json_schema = {}
        
        prop_type = prop.get("type")
        if prop_type == "string":
            json_schema["type"] = apigw.JsonSchemaType.STRING
        elif prop_type == "integer":
            json_schema["type"] = apigw.JsonSchemaType.INTEGER
        elif prop_type == "number":
            json_schema["type"] = apigw.JsonSchemaType.NUMBER
        elif prop_type == "boolean":
            json_schema["type"] = apigw.JsonSchemaType.BOOLEAN
        elif prop_type == "array":
            json_schema["type"] = apigw.JsonSchemaType.ARRAY
            if "items" in prop:
                json_schema["items"] = self._convert_property_to_json_schema(prop["items"])
        elif prop_type == "object":
            json_schema["type"] = apigw.JsonSchemaType.OBJECT
        
        # Add constraints
        if "minLength" in prop:
            json_schema["min_length"] = prop["minLength"]
        if "maxLength" in prop:
            json_schema["max_length"] = prop["maxLength"]
        if "minimum" in prop:
            json_schema["minimum"] = prop["minimum"]
        if "maximum" in prop:
            json_schema["maximum"] = prop["maximum"]
        if "enum" in prop:
            json_schema["enum"] = prop["enum"]
        if "description" in prop:
            json_schema["description"] = prop["description"]
        
        return json_schema
    
    def _create_outputs(self):
        """Create CloudFormation outputs."""
        CfnOutput(
            self,
            "ApiUrl",
            value=self.api.url,
            description="API Gateway URL",
        )
        
        CfnOutput(
            self,
            "ApiKeyId",
            value=self.api_key.key_id,
            description="API Key ID (use 'aws apigateway get-api-key' to retrieve the key value)",
        )
        
        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.lambda_function.function_name,
            description="Lambda function name",
        )
        
        CfnOutput(
            self,
            "ApiId",
            value=self.api.rest_api_id,
            description="API Gateway REST API ID",
        )
