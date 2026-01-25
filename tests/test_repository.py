"""Tests for the todo repository."""
import pytest
from app.db.todo_repository import TodoRepository
from app.db.database import todos_db


@pytest.fixture(autouse=True)
def clear_db():
    """Clear the database before and after each test."""
    from app.db.database import reset_next_id
    
    todos_db.clear()
    reset_next_id(1)
    yield
    todos_db.clear()
    reset_next_id(1)


class TestGetAll:
    """Tests for get_all."""

    def test_get_empty_list(self):
        """Test getting todos from empty database."""
        todos = TodoRepository.get_all()
        assert todos == []

    def test_get_todos(self):
        """Test getting todos after creating some."""
        TodoRepository.create({"title": "Todo 1", "completed": False, "priority": "medium"})
        TodoRepository.create({"title": "Todo 2", "completed": False, "priority": "medium"})
        
        todos = TodoRepository.get_all()
        assert len(todos) == 2
        assert todos[0]["title"] == "Todo 1"
        assert todos[1]["title"] == "Todo 2"


class TestGetById:
    """Tests for get_by_id."""

    def test_get_existing_todo(self):
        """Test getting an existing todo."""
        created = TodoRepository.create({"title": "Test", "completed": False, "priority": "medium"})
        found = TodoRepository.get_by_id(created["id"])
        assert found is not None
        assert found["id"] == created["id"]
        assert found["title"] == "Test"

    def test_get_nonexistent_todo(self):
        """Test getting a non-existent todo."""
        found = TodoRepository.get_by_id(999)
        assert found is None


class TestCreate:
    """Tests for create."""

    def test_create_simple_todo(self):
        """Test creating a simple todo."""
        todo_data = {"title": "Test Todo", "completed": False, "priority": "medium"}
        created = TodoRepository.create(todo_data)
        
        assert created["id"] == 1
        assert created["title"] == "Test Todo"
        assert created["completed"] is False
        assert created["priority"] == "medium"

    def test_create_full_todo(self):
        """Test creating a todo with all fields."""
        todo_data = {
            "title": "Full Todo",
            "description": "Description",
            "priority": "high",
            "completed": False
        }
        created = TodoRepository.create(todo_data)
        
        assert created["title"] == "Full Todo"
        assert created["description"] == "Description"
        assert created["priority"] == "high"

    def test_create_increments_id(self):
        """Test that IDs are incremented."""
        todo1 = TodoRepository.create({"title": "First", "completed": False, "priority": "medium"})
        todo2 = TodoRepository.create({"title": "Second", "completed": False, "priority": "medium"})
        
        assert todo1["id"] == 1
        assert todo2["id"] == 2


class TestUpdate:
    """Tests for update."""

    def test_update_todo_success(self):
        """Test updating a todo successfully."""
        created = TodoRepository.create({"title": "Original", "completed": False, "priority": "medium"})
        
        update_data = {
            "title": "Updated",
            "description": "New description",
            "completed": True
        }
        updated = TodoRepository.update(created["id"], update_data)
        
        assert updated is not None
        assert updated["title"] == "Updated"
        assert updated["description"] == "New description"
        assert updated["completed"] is True

    def test_update_partial(self):
        """Test partial update."""
        created = TodoRepository.create({
            "title": "Original",
            "description": "Original desc",
            "completed": False,
            "priority": "medium"
        })
        
        update_data = {"title": "Updated Title"}
        updated = TodoRepository.update(created["id"], update_data)
        
        assert updated["title"] == "Updated Title"
        assert updated["description"] == "Original desc"

    def test_update_nonexistent(self):
        """Test updating a non-existent todo."""
        update_data = {"title": "Updated"}
        updated = TodoRepository.update(999, update_data)
        assert updated is None


class TestDelete:
    """Tests for delete."""

    def test_delete_existing_todo(self):
        """Test deleting an existing todo."""
        created = TodoRepository.create({"title": "To Delete", "completed": False, "priority": "medium"})
        
        result = TodoRepository.delete(created["id"])
        assert result is True
        
        found = TodoRepository.get_by_id(created["id"])
        assert found is None

    def test_delete_nonexistent_todo(self):
        """Test deleting a non-existent todo."""
        result = TodoRepository.delete(999)
        assert result is False
