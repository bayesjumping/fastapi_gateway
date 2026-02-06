"""Tests for the todo service layer."""
from app.services.todo_service import TodoService
from app.models.todo import TodoCreate, TodoUpdate, Priority


def test_list_todos_with_filters_and_pagination():
    service = TodoService()

    service.create_todo(TodoCreate(title="Alpha", priority=Priority.low, tags=["Work"]))
    service.create_todo(TodoCreate(title="Beta", priority=Priority.high, tags=["Home", "work"]))
    service.create_todo(TodoCreate(title="Gamma", priority=Priority.high, completed=True))

    result = service.list_todos(completed=False, priority=Priority.high, tags="work", skip=0, limit=10)

    assert result.total == 1
    assert result.completed == 1
    assert result.pending == 2
    assert result.todos[0].title == "Beta"


def test_update_todo_no_fields_returns_none():
    service = TodoService()
    created = service.create_todo(TodoCreate(title="Original"))

    updated = service.update_todo(created.id, TodoUpdate())
    assert updated is None


def test_toggle_and_delete_completed():
    service = TodoService()
    todo = service.create_todo(TodoCreate(title="Toggle Me"))

    toggled = service.toggle_todo(todo.id)
    assert toggled is not None
    assert toggled.completed is True

    deleted_count = service.delete_completed_todos()
    assert deleted_count == 1