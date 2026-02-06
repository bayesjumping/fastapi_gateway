"""Tests for infra stack helpers."""
from types import SimpleNamespace

from infra.stacks.gateway_stack import FastApiGatewayStack


class FakeResource:
    def __init__(self, part: str = "") -> None:
        self.part = part
        self.children: dict[str, "FakeResource"] = {}

    def add_resource(self, part: str) -> "FakeResource":
        if part not in self.children:
            self.children[part] = FakeResource(part)
        return self.children[part]


def make_stack_with_routes(paths: list[str]) -> FastApiGatewayStack:
    stack = FastApiGatewayStack.__new__(FastApiGatewayStack)
    stack.introspector = SimpleNamespace(
        routes=[SimpleNamespace(path=path) for path in paths]
    )
    stack._param_name_by_parent = FastApiGatewayStack._build_param_name_map(stack)
    stack.api = SimpleNamespace(root=FakeResource("/"))
    return stack


def test_build_param_name_map_stable_per_parent():
    stack = make_stack_with_routes([
        "/api/v1/todos/{todo_id}",
        "/api/v1/todos/{other_id}/toggle",
        "/api/v1/todos/{todo_id}/comments/{comment_id}",
    ])

    assert stack._param_name_by_parent["/api/v1/todos"] == "{todo_id}"
    assert stack._param_name_by_parent["/api/v1/todos/{todo_id}/comments"] == "{comment_id}"


def test_get_or_create_resource_reuses_param_resource():
    stack = make_stack_with_routes([
        "/api/v1/todos/{todo_id}",
        "/api/v1/todos/{other_id}",
    ])

    created_resources: dict[str, FakeResource] = {}

    first = FastApiGatewayStack._get_or_create_resource(
        stack,
        "/api/v1/todos/{todo_id}",
        created_resources,
    )
    second = FastApiGatewayStack._get_or_create_resource(
        stack,
        "/api/v1/todos/{other_id}",
        created_resources,
    )

    assert first is second