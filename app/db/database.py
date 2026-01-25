"""In-memory database for todos."""

from datetime import datetime
from app.models.todo import Priority

# In-memory database (replace with real DB in production)
todos_db: dict[int, dict] = {
    1: {
        "id": 1,
        "title": "Learn FastAPI",
        "description": "Study FastAPI documentation and build a sample API",
        "completed": False,
        "priority": Priority.high,
        "tags": ["learning", "python"],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    },
    2: {
        "id": 2,
        "title": "Write tests",
        "description": "Add unit tests for the API endpoints",
        "completed": True,
        "priority": Priority.medium,
        "tags": ["testing", "development"],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
}

_next_id = 3


def get_next_id() -> int:
    """Get next available ID."""
    global _next_id
    current_id = _next_id
    _next_id += 1
    return current_id


def reset_next_id(value: int = 1) -> None:
    """Reset ID counter (useful for testing)."""
    global _next_id
    _next_id = value
