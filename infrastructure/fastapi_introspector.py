"""
CDK utilities for introspecting FastAPI applications and generating API Gateway resources.
This module dynamically reads the FastAPI app at CDK synthesis time to create API Gateway infrastructure.
"""
import inspect
import json
from typing import Dict, List, Any, Optional, Set
from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel
from enum import Enum


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
            if isinstance(route, APIRoute):
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
            
        model_name = model.__name__
        if model_name in self.models:
            return
            
        if issubclass(model, BaseModel):
            self.models[model_name] = model
            
            # Collect nested models
            if hasattr(model, 'model_fields'):
                for field_name, field_info in model.model_fields.items():
                    field_type = field_info.annotation
                    if inspect.isclass(field_type) and issubclass(field_type, BaseModel):
                        self._collect_response_models(field_type)
                    # Handle List types
                    elif hasattr(field_type, '__origin__'):
                        if hasattr(field_type, '__args__'):
                            for arg in field_type.__args__:
                                if inspect.isclass(arg) and issubclass(arg, BaseModel):
                                    self._collect_response_models(arg)
    
    def get_json_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get JSON schemas for all Pydantic models."""
        schemas = {}
        for model_name, model_class in self.models.items():
            if hasattr(model_class, 'model_json_schema'):
                schema = model_class.model_json_schema()
                # Clean up the schema for API Gateway
                schemas[model_name] = self._clean_schema(schema)
        return schemas
    
    def _clean_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up JSON schema for API Gateway compatibility."""
        # Remove $defs if present and inline them
        if '$defs' in schema:
            defs = schema.pop('$defs')
            # Replace $ref with actual definitions
            schema = self._resolve_refs(schema, defs)
        
        # Ensure schema has a type
        if 'type' not in schema and 'properties' in schema:
            schema['type'] = 'object'
        
        return schema
    
    def _resolve_refs(self, obj: Any, defs: Dict[str, Any]) -> Any:
        """Resolve $ref references in schema."""
        if isinstance(obj, dict):
            if '$ref' in obj:
                ref_path = obj['$ref'].split('/')[-1]
                if ref_path in defs:
                    return self._resolve_refs(defs[ref_path], defs)
            return {k: self._resolve_refs(v, defs) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_refs(item, defs) for item in obj]
        return obj
    
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
