"""
CDK Stack that dynamically generates API Gateway infrastructure from FastAPI application.
This stack introspects the FastAPI app at synthesis time and creates all necessary AWS resources.
"""
import os
import sys
import shutil
import subprocess
import jsii
from typing import Dict, Any, List
from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    BundlingOptions,
    ILocalBundling,
)
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_logs as logs
from constructs import Construct

# Add parent directory to path to import FastAPI app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app as fastapi_app
from ..introspection.fastapi_introspector import FastAPIIntrospector, pydantic_to_api_gateway_model


@jsii.implements(ILocalBundling)
class LocalBundler:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def try_bundle(self, output_dir: str, _options: BundlingOptions) -> bool:
        try:
            requirements = self.project_root / "infra" / "requirements-lambda.txt"
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements),
                    "-t",
                    output_dir,
                    "--upgrade",
                    "--no-cache-dir",
                ]
            )

            shutil.copytree(
                self.project_root / "app",
                Path(output_dir) / "app",
                dirs_exist_ok=True,
            )
            shutil.copy2(self.project_root / "main.py", Path(output_dir) / "main.py")

            for root, dirs, files in os.walk(output_dir):
                dirs[:] = [d for d in dirs if d not in {"__pycache__", "tests"}]
                for file_name in files:
                    if file_name.endswith(".pyc"):
                        try:
                            os.remove(Path(root) / file_name)
                        except OSError:
                            pass

            return True
        except Exception:
            return False


class FastApiGatewayStack(Stack):
    """CDK Stack that generates API Gateway from FastAPI application."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Introspect the FastAPI application
        print("🔍 Introspecting FastAPI application...")
        self.introspector = FastAPIIntrospector(fastapi_app)

        print(f"📋 Found {len(self.introspector.routes)} routes")
        print(f"📦 Found {len(self.introspector.models)} models")

        # Build stable parameter name mapping per parent path
        self._param_name_by_parent = self._build_param_name_map()

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
        project_root = Path(__file__).parent.parent.parent

        lambda_fn = _lambda.Function(
            self,
            "FastApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="app.runtime.lambda_handler.handler",
            code=_lambda.Code.from_asset(
                str(project_root),
                exclude=[
                    "build",
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
                    "local": LocalBundler(project_root),
                    "command": [
                        "bash", "-c",
                        " && ".join([
                            "pip install -r infra/requirements-lambda.txt -t /asset-output --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: --upgrade --no-cache-dir",
                            "cp -r app /asset-output/",
                            "cp main.py /asset-output/",
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
            try:
                # Simplify schema to avoid API Gateway limitations
                simplified_schema = self._simplify_schema_for_apigw(schema)

                api_model = apigw.Model(
                    self,
                    f"Model{model_name}",
                    rest_api=self.api,
                    content_type="application/json",
                    model_name=model_name,
                    schema=simplified_schema,
                )
                api_models[model_name] = api_model
            except Exception as e:
                print(f"  ⚠️  Warning: Could not create model {model_name}: {e}")
                # Continue without this model

        # Create routes grouped by path
        created_resources = {}

        # Create single Lambda integration for all routes
        lambda_integration = apigw.LambdaIntegration(
            self.lambda_function,
            proxy=True,
            allow_test_invoke=True,
        )

        for route in self.introspector.routes:
            print(f"  🛣️  Creating route: {' '.join(route.methods)} {route.path}")

            # Get or create the resource for this path
            resource = self._get_or_create_resource(route.path, created_resources)

            # Create method for each HTTP method
            for method in route.methods:
                if method == "OPTIONS":
                    continue  # Skip OPTIONS, handled by CORS

                # Simplified - validation happens in Lambda
                method_options = {
                    "authorization_type": apigw.AuthorizationType.NONE,
                    "api_key_required": True,
                }

                resource.add_method(
                    method,
                    lambda_integration,
                    **method_options
                )

    def _build_param_name_map(self) -> Dict[str, str]:
        """Build a stable mapping of parent path -> parameter name."""
        param_name_by_parent: Dict[str, str] = {}

        for route in self.introspector.routes:
            parts = [p for p in route.path.split("/") if p]
            current_path = ""

            for part in parts:
                if part.startswith("{") and part.endswith("}"):
                    parent_path = current_path if current_path else "/"
                    if parent_path not in param_name_by_parent:
                        param_name_by_parent[parent_path] = part
                    chosen = param_name_by_parent[parent_path]
                    current_path = f"{current_path}/{chosen}" if current_path else f"/{chosen}"
                else:
                    current_path = f"{current_path}/{part}" if current_path else f"/{part}"

        return param_name_by_parent

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
            if part.startswith("{") and part.endswith("}"):
                parent_path = current_path if current_path else "/"
                normalized_part = self._param_name_by_parent.get(parent_path, part)
            else:
                normalized_part = part

            current_path = f"{current_path}/{normalized_part}" if current_path else f"/{normalized_part}"

            if current_path in created_resources:
                current_resource = created_resources[current_path]
            else:
                # Check if it's a path parameter
                resource_part = normalized_part

                current_resource = current_resource.add_resource(resource_part)
                created_resources[current_path] = current_resource

        return current_resource

    def _simplify_schema_for_apigw(self, schema: Dict[str, Any]) -> apigw.JsonSchema:
        """Simplify schema for API Gateway limitations."""
        # Convert to API Gateway JsonSchema format
        return apigw.JsonSchema.from_dict(schema)

    def _create_outputs(self):
        """Create CloudFormation outputs."""
        CfnOutput(
            self,
            "ApiUrl",
            value=self.api.url,
            description="API Gateway endpoint URL",
        )

        CfnOutput(
            self,
            "ApiKeyId",
            value=self.api_key.key_id,
            description="API Key ID",
        )
