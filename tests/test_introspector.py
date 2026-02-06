"""Tests for FastAPI introspection utilities."""
from fastapi import FastAPI
from pydantic import BaseModel

from infra.introspection.fastapi_introspector import FastAPIIntrospector


class ChildModel(BaseModel):
    name: str


class ParentModel(BaseModel):
    child: ChildModel


def build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/items/{item_id}", response_model=ParentModel, tags=["items"])
    async def get_item(item_id: int) -> ParentModel:  # pragma: no cover - not executed
        return ParentModel(child=ChildModel(name=str(item_id)))

    return app


def test_introspector_routes_and_tags():
    app = build_app()
    introspector = FastAPIIntrospector(app)

    routes_by_tag = introspector.get_routes_by_tag()
    assert "items" in routes_by_tag
    assert routes_by_tag["items"][0].path == "/items/{item_id}"

    paths = introspector.get_api_gateway_paths()
    assert "/items/{item_id}" in paths


def test_introspector_schemas_resolve_defs():
    app = build_app()
    introspector = FastAPIIntrospector(app)

    schemas = introspector.get_json_schemas()
    assert "ParentModel" in schemas
    assert "$defs" not in schemas["ParentModel"]

    openapi = introspector.to_openapi_dict()
    assert "paths" in openapi