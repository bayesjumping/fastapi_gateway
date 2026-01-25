"""Todo service layer for business logic."""

from typing import Optional, List

from app.db.todo_repository import TodoRepository
from app.models.todo import (
    Priority,
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoListResponse
)


class TodoService:
    """Service layer for Todo business logic."""
    
    def __init__(self):
        self.repo = TodoRepository()
    
    def list_todos(
        self,
        completed: Optional[bool] = None,
        priority: Optional[Priority] = None,
        tags: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> TodoListResponse:
        """List todos with filtering and pagination."""
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",")]
        
        # Filter todos
        filtered = self.repo.filter_todos(completed, priority, tag_list)
        
        # Get total before pagination
        total = len(filtered)
        
        # Apply pagination
        paginated = filtered[skip:skip + limit]
        
        # Get stats
        stats = self.repo.get_stats()
        
        return TodoListResponse(
            todos=[TodoResponse(**todo) for todo in paginated],
            total=total,
            completed=stats["completed"],
            pending=stats["pending"]
        )
    
    def get_todo(self, todo_id: int) -> Optional[TodoResponse]:
        """Get a specific todo by ID."""
        todo = self.repo.get_by_id(todo_id)
        return TodoResponse(**todo) if todo else None
    
    def create_todo(self, todo: TodoCreate) -> TodoResponse:
        """Create a new todo."""
        todo_data = todo.model_dump()
        new_todo = self.repo.create(todo_data)
        return TodoResponse(**new_todo)
    
    def update_todo(self, todo_id: int, todo_update: TodoUpdate) -> Optional[TodoResponse]:
        """Update an existing todo."""
        # Get only fields that were actually provided
        update_data = todo_update.model_dump(exclude_unset=True)
        
        if not update_data:
            return None  # No fields to update
        
        updated = self.repo.update(todo_id, update_data)
        return TodoResponse(**updated) if updated else None
    
    def toggle_todo(self, todo_id: int) -> Optional[TodoResponse]:
        """Toggle completion status of a todo."""
        todo = self.repo.get_by_id(todo_id)
        if not todo:
            return None
        
        updated = self.repo.update(todo_id, {"completed": not todo["completed"]})
        return TodoResponse(**updated) if updated else None
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo by ID."""
        return self.repo.delete(todo_id)
    
    def delete_completed_todos(self) -> int:
        """Delete all completed todos."""
        return self.repo.delete_completed()
