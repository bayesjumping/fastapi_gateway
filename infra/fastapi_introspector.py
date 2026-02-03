"""
CDK utilities for introspecting FastAPI applications and generating API Gateway resources.
This module dynamically reads the FastAPI app at CDK synthesis time to create API Gateway infrastructure.
"""
import inspect
from typing import Dict, List, Any, Optional, Set
from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel


class RouteInfo:
    """Information about a FastAPI route."""
    
    def __init__(
        self,
        path: str,
        methods: Set[str],
        name: str,
        summary: Optional[str],
        request_model: Optional[type],
        response_model: Optional[type],
        tags: List[str]
    ):
        self.path = path
        self.methods = methods
        self.name = name
        self.summary = summary
        self.request_model = request_model
        self.response_model = response_model
        self.tags = tags
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert route info to dictionary."""
        return {
            "path": self.path,
            "methods": list(self.methods),
            "name": self.name,
            "summary": self.summary,
            "request_model": self.request_model.__name__ if self.request_model else None,
            "response_model": self.response_model.__name__ if self.response_model else None,
            "tags": self.tags
        }


class FastAPIIntrospector:
    """Introspects FastAPI applications to extract route and model information."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.routes: List[RouteInfo] = []
        self.models: Dict[str, type] = {}
        self._introspect()
    
    def _introspect(self):
        """Introspect the FastAPI application."""
        for route in self.app.routes:
            if not isinstance(route, APIRoute):
                continue
            
            route_info = self._extract_route_info(route)
            self.routes.append(route_info)
            
            # Collect models
            if route_info.request_model:
                self.models[route_info.request_model.__name__] = route_info.request_model
            if route_info.response_model:
                self._collect_response_models(route_info.response_model)
    
    def _extract_route_info(self, route: APIRoute) -> RouteInfo:
        """Extract information from an APIRoute."""
        # Get request body model
        request_model = None
        if route.body_field:
            request_model = route.body_field.type_
        
        # Get response model
        response_model = None
        if route.response_model:
            response_model = route.response_model
        
        return RouteInfo(
            path=route.path,
            methods=route.methods,
            name=route.name,
            summary=route.summary or route.name,
            request_model=request_model,
            response_model=response_model,
            tags=route.tags or []
        )
    
    def _collect_response_models(self, model: type):
        """Recursively collect response models and their dependencies."""
        if not model or not hasattr(model, '__name__'):
            return
        
        if not inspect.isclass(model):
            return
            
        model_name = model.__name__
        if model_name in self.models:
            return
        
        if not self._is_base_model(model):
            return
        
        self.models[model_name] = model
        self._collect_nested_models(model)
    
    def _is_base_model(self, model: type) -> bool:
        """Check if model is a BaseModel subclass."""
        try:
            return issubclass(model, BaseModel)
        except TypeError:
            return False
    
    def _collect_nested_models(self, model: type):
        """Collect nested models from model fields."""
        if not hasattr(model, 'model_fields'):
            return
        
        for field_info in model.model_fields.values():
            field_type = field_info.annotation
            self._process_field_type(field_type)
    
    def _process_field_type(self, field_type: type):
        """Process a field type and collect if it's a BaseModel."""
        if inspect.isclass(field_type) and self._is_base_model(field_type):
            self._collect_response_models(field_type)
            return
        
        # Handle generic types (List, Optional, etc.)
        if not hasattr(field_type, '__origin__') or not hasattr(field_type, '__args__'):
            return
        
        for arg in field_type.__args__:
            if inspect.isclass(arg) and self._is_base_model(arg):
                self._collect_response_models(arg)
    
    def get_json_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get JSON schemas for all Pydantic models."""
        schemas = {}
        for model_name, model_class in self.models.items():
            if not hasattr(model_class, 'model_json_schema'):
                continue
            
            schema = model_class.model_json_schema()
            schemas[model_name] = self._clean_schema(schema)
        return schemas
    
    def _clean_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up JSON schema for API Gateway compatibility."""
        if '$defs' in schema:
            defs = schema.pop('$defs')
            schema = self._resolve_refs(schema, defs)
        
        if 'type' not in schema and 'properties' in schema:
            schema['type'] = 'object'
        
        return schema
    
    def _resolve_refs(self, obj: Any, defs: Dict[str, Any]) -> Any:
        """Resolve $ref references in schema."""
        if isinstance(obj, list):
            return [self._resolve_refs(item, defs) for item in obj]
        
        if not isinstance(obj, dict):
            return obj
        
        if '$ref' in obj:
            ref_path = obj['$ref'].split('/')[-1]
            if ref_path in defs:
                return self._resolve_refs(defs[ref_path], defs)
            return obj
        
        return {k: self._resolve_refs(v, defs) for k, v in obj.items()}
    
    def get_routes_by_tag(self) -> Dict[str, List[RouteInfo]]:
        """Group routes by their tags."""
        routes_by_tag = {}
        for route in self.routes:
            for tag in route.tags:
                if tag not in routes_by_tag:
                    routes_by_tag[tag] = []
                routes_by_tag[tag].append(route)
        return routes_by_tag
    
    def get_api_gateway_paths(self) -> List[str]:
        """Get all unique paths for API Gateway."""
        return list(set(route.path for route in self.routes))
    
    def get_routes_for_path(self, path: str) -> List[RouteInfo]:
        """Get all routes for a specific path."""
        return [route for route in self.routes if route.path == path]
    
    def to_openapi_dict(self) -> Dict[str, Any]:
        """Convert to OpenAPI-compatible dictionary."""
        return self.app.openapi()


def pydantic_to_api_gateway_model(model: type[BaseModel]) -> Dict[str, Any]:
    """Convert a Pydantic model to an API Gateway model schema."""
    if not hasattr(model, 'model_json_schema'):
        return {}
    
    schema = model.model_json_schema()
    
    # API Gateway expects a specific format
    api_gateway_schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": schema.get("properties", {}),
    }
    
    if "required" in schema:
        api_gateway_schema["required"] = schema["required"]
    
    if "title" in schema:
        api_gateway_schema["title"] = schema["title"]
    
    return api_gateway_schema
