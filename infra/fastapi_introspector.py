"""
Deprecated module.
Use infra/introspection/fastapi_introspector.py instead.
"""
from .introspection.fastapi_introspector import (  # noqa: F401
    FastAPIIntrospector,
    RouteInfo,
    pydantic_to_api_gateway_model,
)
