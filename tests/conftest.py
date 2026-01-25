"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_todos():
    """Reset todos database before each test."""
    from app.db.todo_repository import todos_db
    from app.db.database import reset_next_id
    
    todos_db.clear()
    reset_next_id(1)
    yield
    todos_db.clear()
    reset_next_id(1)
