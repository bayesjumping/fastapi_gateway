"""Tests for Pydantic models."""
import pytest
from pydantic import ValidationError
from app.models.todo import TodoCreate, TodoUpdate, TodoResponse, Priority


class TestTodoCreate:
    """Tests for TodoCreate model."""

    def test_todo_create_valid(self):
        """Test creating a valid TodoCreate."""
        todo = TodoCreate(title="Test", description="Desc", priority="high")
        assert todo.title == "Test"
        assert todo.description == "Desc"
        assert todo.priority.value == "high"

    def test_todo_create_defaults(self):
        """Test TodoCreate with default values."""
        todo = TodoCreate(title="Test")
        assert todo.title == "Test"
        assert todo.description is None
        assert todo.priority.value == "medium"

    def test_todo_create_invalid_priority(self):
        """Test TodoCreate with invalid priority."""
        with pytest.raises(ValidationError):
            TodoCreate(title="Test", priority="invalid")

    def test_todo_create_missing_title(self):
        """Test TodoCreate without required title."""
        with pytest.raises(ValidationError):
            TodoCreate(description="No title")


class TestTodoUpdate:
    """Tests for TodoUpdate model."""

    def test_todo_update_all_fields(self):
        """Test updating all fields."""
        update = TodoUpdate(
            title="New Title",
            description="New Desc",
            priority="low",
            completed=True
        )
        assert update.title == "New Title"
        assert update.description == "New Desc"
        assert update.priority.value == "low"
        assert update.completed is True

    def test_todo_update_partial(self):
        """Test partial update."""
        update = TodoUpdate(title="Only Title")
        assert update.title == "Only Title"
        assert update.description is None
        assert update.priority is None
        assert update.completed is None

    def test_todo_update_empty(self):
        """Test empty update."""
        update = TodoUpdate()
        assert update.title is None
        assert update.description is None
        assert update.priority is None
        assert update.completed is None


class TestTodoResponse:
    """Tests for TodoResponse model."""

    def test_todo_response_valid(self):
        """Test creating a valid TodoResponse."""
        todo = TodoResponse(
            id=1,
            title="Test",
            description="Desc",
            priority="high",
            completed=False
        )
        assert todo.id == 1
        assert todo.title == "Test"
        assert todo.description == "Desc"
        assert todo.priority.value == "high"
        assert todo.completed is False

    def test_todo_response_missing_id(self):
        """Test TodoResponse without required id."""
        with pytest.raises(ValidationError):
            TodoResponse(title="Test", completed=False)

    def test_todo_response_with_defaults(self):
        """Test TodoResponse with default completed value."""
        todo = TodoResponse(id=1, title="Test")
        assert todo.completed is False
        assert todo.priority.value == "medium"
