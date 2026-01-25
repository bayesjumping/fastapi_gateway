"""Todo repository for database operations."""

from typing import Optional, List
from datetime import datetime

from app.db.database import todos_db, get_next_id
from app.models.todo import Priority


class TodoRepository:
    """Repository for Todo CRUD operations."""
    
    @staticmethod
    def get_all() -> List[dict]:
        """Get all todos."""
        return list(todos_db.values())
    
    @staticmethod
    def get_by_id(todo_id: int) -> Optional[dict]:
        """Get todo by ID."""
        return todos_db.get(todo_id)
    
    @staticmethod
    def create(todo_data: dict) -> dict:
        """Create a new todo."""
        todo_id = get_next_id()
        new_todo = {
            "id": todo_id,
            **todo_data,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        todos_db[todo_id] = new_todo
        return new_todo
    
    @staticmethod
    def update(todo_id: int, update_data: dict) -> Optional[dict]:
        """Update an existing todo."""
        if todo_id not in todos_db:
            return None
        
        todos_db[todo_id].update(update_data)
        todos_db[todo_id]["updated_at"] = datetime.now()
        return todos_db[todo_id]
    
    @staticmethod
    def delete(todo_id: int) -> bool:
        """Delete a todo by ID."""
        if todo_id not in todos_db:
            return False
        del todos_db[todo_id]
        return True
    
    @staticmethod
    def delete_completed() -> int:
        """Delete all completed todos and return count."""
        global todos_db
        initial_count = len(todos_db)
        
        # Create new dict without completed todos
        remaining = {
            id: todo for id, todo in todos_db.items()
            if not todo["completed"]
        }
        
        # Update the database
        todos_db.clear()
        todos_db.update(remaining)
        
        return initial_count - len(todos_db)
    
    @staticmethod
    def filter_todos(
        completed: Optional[bool] = None,
        priority: Optional[Priority] = None,
        tags: Optional[List[str]] = None
    ) -> List[dict]:
        """Filter todos by various criteria."""
        todos = list(todos_db.values())
        
        if completed is not None:
            todos = [t for t in todos if t["completed"] == completed]
        
        if priority is not None:
            todos = [t for t in todos if t["priority"] == priority]
        
        if tags:
            todos = [
                t for t in todos
                if any(tag in t.get("tags", []) for tag in tags)
            ]
        
        return todos
    
    @staticmethod
    def get_stats() -> dict:
        """Get statistics about todos."""
        all_todos = list(todos_db.values())
        completed_count = sum(1 for t in all_todos if t["completed"])
        
        return {
            "total": len(all_todos),
            "completed": completed_count,
            "pending": len(all_todos) - completed_count
        }
