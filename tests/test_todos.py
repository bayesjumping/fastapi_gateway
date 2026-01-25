"""Tests for Todo API endpoints."""
import pytest


class TestTodoList:
    """Tests for listing todos."""

    def test_get_empty_todos(self, client):
        """Test getting empty todo list."""
        response = client.get("/api/v1/todos")
        assert response.status_code == 200
        data = response.json()
        assert data["todos"] == []
        assert data["total"] == 0

    def test_get_todos_with_data(self, client):
        """Test getting todos after creating some."""
        # Create a todo
        client.post("/api/v1/todos", json={"title": "Test Todo", "priority": "medium"})
        
        # Get all todos
        response = client.get("/api/v1/todos")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["todos"]) == 1
        assert data["todos"][0]["title"] == "Test Todo"


class TestCreateTodo:
    """Tests for creating todos."""

    def test_create_todo_success(self, client):
        """Test creating a todo successfully."""
        todo_data = {
            "title": "Test Todo",
            "description": "Test Description",
            "priority": "high"
        }
        response = client.post("/api/v1/todos", json=todo_data)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Todo"
        assert data["description"] == "Test Description"
        assert data["priority"] == "high"
        assert data["completed"] is False

    def test_create_todo_minimal(self, client):
        """Test creating a todo with minimal data."""
        todo_data = {"title": "Minimal Todo"}
        response = client.post("/api/v1/todos", json=todo_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Todo"
        assert data["description"] is None
        assert data["priority"] == "medium"  # default
        assert data["completed"] is False

    def test_create_todo_invalid_priority(self, client):
        """Test creating a todo with invalid priority."""
        todo_data = {"title": "Test", "priority": "invalid"}
        response = client.post("/api/v1/todos", json=todo_data)
        assert response.status_code == 422

    def test_create_todo_missing_title(self, client):
        """Test creating a todo without title."""
        todo_data = {"description": "No title"}
        response = client.post("/api/v1/todos", json=todo_data)
        assert response.status_code == 422


class TestGetTodo:
    """Tests for getting a single todo."""

    def test_get_todo_success(self, client):
        """Test getting an existing todo."""
        # Create a todo
        create_response = client.post("/api/v1/todos", json={"title": "Test Todo"})
        todo_id = create_response.json()["id"]
        
        # Get the todo
        response = client.get(f"/api/v1/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test Todo"

    def test_get_todo_not_found(self, client):
        """Test getting a non-existent todo."""
        response = client.get("/api/v1/todos/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateTodo:
    """Tests for updating todos."""

    def test_update_todo_success(self, client):
        """Test updating a todo successfully."""
        # Create a todo
        create_response = client.post("/api/v1/todos", json={"title": "Original"})
        todo_id = create_response.json()["id"]
        
        # Update the todo
        update_data = {
            "title": "Updated",
            "description": "New description",
            "priority": "high",
            "completed": True
        }
        response = client.put(f"/api/v1/todos/{todo_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["description"] == "New description"
        assert data["priority"] == "high"
        assert data["completed"] is True

    def test_update_todo_partial(self, client):
        """Test partial update of a todo."""
        # Create a todo
        create_response = client.post("/api/v1/todos", json={
            "title": "Original",
            "description": "Original description"
        })
        todo_id = create_response.json()["id"]
        
        # Update only title
        update_data = {"title": "Updated Title"}
        response = client.put(f"/api/v1/todos/{todo_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Original description"  # unchanged

    def test_update_todo_not_found(self, client):
        """Test updating a non-existent todo."""
        response = client.put("/api/v1/todos/999", json={"title": "Updated"})
        assert response.status_code == 404


class TestToggleTodo:
    """Tests for toggling todo completion status."""

    def test_toggle_todo_success(self, client):
        """Test toggling a todo's completion status."""
        # Create a todo
        create_response = client.post("/api/v1/todos", json={"title": "Test"})
        todo_id = create_response.json()["id"]
        
        # Toggle to completed
        response = client.patch(f"/api/v1/todos/{todo_id}/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        
        # Toggle back to incomplete
        response = client.patch(f"/api/v1/todos/{todo_id}/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is False

    def test_toggle_todo_not_found(self, client):
        """Test toggling a non-existent todo."""
        response = client.patch("/api/v1/todos/999/toggle")
        assert response.status_code == 404


class TestDeleteTodo:
    """Tests for deleting todos."""

    def test_delete_todo_success(self, client):
        """Test deleting a todo successfully."""
        # Create a todo
        create_response = client.post("/api/v1/todos", json={"title": "Test"})
        todo_id = create_response.json()["id"]
        
        # Delete the todo
        response = client.delete(f"/api/v1/todos/{todo_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/todos/{todo_id}")
        assert get_response.status_code == 404

    def test_delete_todo_not_found(self, client):
        """Test deleting a non-existent todo."""
        response = client.delete("/api/v1/todos/999")
        assert response.status_code == 404

    def test_delete_all_todos(self, client):
        """Test deleting completed todos."""
        # Create multiple todos, some completed
        client.post("/api/v1/todos", json={"title": "Todo 1", "completed": True})
        client.post("/api/v1/todos", json={"title": "Todo 2", "completed": False})
        client.post("/api/v1/todos", json={"title": "Todo 3", "completed": True})
        
        # Delete completed todos
        response = client.delete("/api/v1/todos")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 2
        
        # Verify only incomplete todo remains
        list_response = client.get("/api/v1/todos")
        assert list_response.json()["total"] == 1
